from django.shortcuts import render
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from collections import OrderedDict
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.decorators import api_view
from core.serializers import FilesSerializer
from core.models import Files
from pathlib import Path
from core.forms import UploadFileForm
import google.generativeai as genai
from vertexai.preview.generative_models import GenerativeModel, GenerationConfig, Part, Content
import pathlib
from pypdf import PdfReader
from urllib.request import urlopen
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.utils import embedding_functions
from chromadb.config import DEFAULT_TENANT, DEFAULT_DATABASE, Settings
import io
import re
import os
import itertools
import transformers
import torch
from huggingface_hub import login
from google.generativeai import caching
import datetime
import base64
from dotenv import load_dotenv

CHROMA_CLIENT = chromadb.PersistentClient(path='./')
EMBEDDING_FUNCTION = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
    api_key=os.environ.get('GOOGLE_API_KEY'), task_type="RETRIEVAL_QUERY"
)

def get_collection_name(self, filename):
    return re.sub(r'[^\w\s]', '', filename.replace(" ",""))

class ChatbotView(viewsets.ModelViewSet):
    queryset = Queries.objects.all()
    serializer_class = QueriesSerializer

    def create(self,request):
        genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))

        user_query = request.data.get('query')
        info_source = ''
        
        for file in os.listdir('./files'):
            filename = file.split('.')[0]
            collection_name = get_collection_name(filename)
            try:
                collection_name = get_collection_name(filename)
            except:
                continue

            collection = CHROMA_CLIENT.get_collection(name=collection_name, embedding_function=EMBEDDING_FUNCTION)
            info_source += collection.query(query_texts=[user_query], n_results=4, include=["documents", "metadatas"])
        
        prompt = f'''You are an assistant bot that answers questions using text from the source information provided. 
            You are allowed to obtain information only from the source information here specified. Include in the 
            answer the name of the file from which you obtained the information. \
            QUESTION: {user_query}
            SOURCE INFORMATION: {info_source}
        '''

        return Response({"response":[info_source, user_query]})
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(user_query)
                
        return Response({"response":response.text})

class LoadRagView(viewsets.ModelViewSet):
    queryset = Queries.objects.all()
    serializer_class = QueriesSerializer

    def list(self, request):            

        info_source = ''
        
        for file in os.listdir('./files'):
            filename = file.split('.')[0]
            collection_name = get_collection_name(filename)
        
        
            if self.collection_already_exists(collection_name):
                continue
            else:
                self.create_collection_from_file(file)

            collection = CHROMA_CLIENT.get_collection(name=collection_name, embedding_function=EMBEDDING_FUNCTION)
            collection_documents = collection.get()['documents']
            collection_text = '*NEW_DOC*'.join(collection_documents)
                
            if collection_text:
                info_source  += f'DOCUMENT TITLE: {file} \n DOCUMENT CONTENT: {collection_text}\n'

        return Response({"response":collection_name})
        
    
    def collection_already_exists(self, collection_name):
        try:
            collection = CHROMA_CLIENT.get_collection(name=collection_name, embedding_function=EMBEDDING_FUNCTION)
            return True
        except:
            return False
        
    def create_collection_from_file(self, file):

        filename = file.split('.')[0]
        file_ext = file.split('.')[1]
        collection_name = get_collection_name(filename)
        collection_text = ""

        if file_ext=='pdf':
            pdf_file = PdfReader('./files/'+file)
            for page in pdf_file.pages:
                collection_text += page.extract_text()

        splitted_text = re.split('\n \n', collection_text)
        chuncked_text = [textline for textline in splitted_text if textline != "" or textline != " "]

        if chuncked_text:
            collection = CHROMA_CLIENT.create_collection(name=collection_name, embedding_function=EMBEDDING_FUNCTION)
            
            for i, textline in enumerate(chuncked_text):
                try:
                    collection.add(documents=textline, ids=str(i)) 
                except:
                    break

    def get_pdf_by_url(self, url):
        remote_file = urlopen(url).read()
        memory_file = io.BytesIO(remote_file)
        return memory_file



