from django.shortcuts import render
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from collections import OrderedDict
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.decorators import api_view
from core.serializers import QueriesSerializer
from core.models import Queries
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
import time
import itertools
import transformers
import torch
from huggingface_hub import login
from google.generativeai import caching
import datetime
import base64
from dotenv import load_dotenv

CHROMA_CLIENT = chromadb.PersistentClient(path='./gemini_collections/')
EMBEDDING_FUNCTION = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
    api_key=os.environ.get('GOOGLE_API_KEY'), task_type="RETRIEVAL_QUERY"
)

def get_collection_name(filename):
    return re.sub(r'[^\w\s]', '', filename.replace(" ",""))

def collection_already_exists(collection_name):
    try:
        collection = CHROMA_CLIENT.get_collection(name=collection_name, embedding_function=EMBEDDING_FUNCTION)
        return True
    except:
        return False

class ChatbotView(viewsets.ModelViewSet):
    queryset = Queries.objects.all()
    serializer_class = QueriesSerializer

    def list(self, request):

        collection_text = ''
        size_counter = 0
        test = []

        for file in os.listdir('./files/'):
            filename = file.split('.')[0]
            file_ext = file.split('.')[1]
            if file_ext=='pdf':
                pdf_file = PdfReader('./files/'+file)
                for page in pdf_file.pages:
                    collection_text += page.extract_text()

            if collection_text:
                splitted_text = re.split('\n \n', collection_text)
                chuncked_text = [textline for textline in splitted_text if textline != "" or textline != " "]

            for i, textline in enumerate(chuncked_text):
                size = len(textline.encode("utf-8"))
                size_counter += size
                test.append([i, textline, size, len(textline)])  

        return Response({'test':test, 'size':size_counter})

    def create(self,request):
        genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))

        user_query = request.data.get('query')
        context = ''
        
        for file in os.listdir('./files'):
            filename = file.split('.')[0]
            collection_name = get_collection_name(filename)

            if collection_already_exists(collection_name):
                collection = CHROMA_CLIENT.get_collection(name=collection_name, embedding_function=EMBEDDING_FUNCTION)
                collection_query = collection.query(query_texts=[user_query], n_results=2, include=["documents", "metadatas"])
                collection_best_response = collection_query['documents'][0]
                context += f'''
                    NEW INFO SOURCE: \n {filename} \n 
                    NEW CONTEXT FROM INFO SOURCE TO ANSWER TO {user_query}: {collection_best_response}\n
                '''

        prompt = f'''You are an assistant bot that answers questions using text from the source information here provided. 
            You are allowed to obtain information only from the source information here specified. Include in the 
            answer the name of the file from which you obtained the information. \
            QUESTION: {user_query}
            SOURCE INFORMATION AND FURTHER INSTRUCTIONS: {context}
        '''
        
        model = genai.GenerativeModel('gemini-1.5-flash')

        start_time = time.time() 
        response = model.generate_content(prompt)
        end_time = time.time()

        response_entry = {
            "query": user_query,
            "context": context, 
            "response": response.text, 
            "response_time": end_time - start_time   
        }
                
        return Response(response_entry)

class LoadCollectionsView(viewsets.ModelViewSet):
    queryset = Queries.objects.all()
    serializer_class = QueriesSerializer
    sizes = []
    size_counter = 0

    def list(self, request):            

        collections = []
        
        for file in os.listdir('./files'):
            filename = file.split('.')[0]
            collection_name = get_collection_name(filename)
        
            if collection_already_exists(collection_name):
                CHROMA_CLIENT.delete_collection(name=collection_name)
                collections.append(collection_name)
                continue
            else:
                self.create_collection_from_file(file)

        return Response({"collections":collections, "sizes": self.sizes})
        
    def create_collection_from_file(self, file):

        filename = file.split('.')[0]
        file_ext = file.split('.')[1]
        collection_name = get_collection_name(filename)
        collection_text = ""

        if file_ext=='pdf':
            pdf_file = PdfReader('./files/'+file)
            for page in pdf_file.pages:
                collection_text += page.extract_text()

        if collection_text:
            splitted_text = re.split('\n \n', collection_text)
            chuncked_text = [textline for textline in splitted_text if textline != "" or textline != " "]

            collection = CHROMA_CLIENT.create_collection(name=collection_name, embedding_function=EMBEDDING_FUNCTION)
                
            for i, textline in enumerate(chuncked_text):
                try:
                    collection.add(documents=textline, ids=str(i))        
                    self.sizes.append({'success': len(textline.encode("utf-8"))})
                except:
                    self.sizes.append({'failure': len(textline.encode("utf-8"))})

    def get_pdf_by_url(self, url):
        remote_file = urlopen(url).read()
        memory_file = io.BytesIO(remote_file)
        return memory_file



