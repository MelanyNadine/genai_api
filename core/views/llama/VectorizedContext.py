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
import datetime
import base64
from dotenv import load_dotenv


CHROMA_CLIENT = chromadb.PersistentClient(path='./')

EMBEDDING_FUNCTION = embedding_functions.HuggingFaceEmbeddingFunction(
    api_key="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",
    model_name="meta-llama/Meta-Llama-3.1-8B"
)

FILES_DIR = './files'

def get_collection_name(filename):
        return re.sub(r'[^\w\s]', '', filename.replace(" ",""))

class ChatbotView(viewsets.ModelViewSet):
    queryset = Queries.objects.all()
    serializer_class = QueriesSerializer 

    def create(self,request):
        user_query = request.data.get('query')

        context = ''
        
        for file in os.listdir(FILES_DIR):
            filename = file.split('.')[0]
            collection_name = get_collection_name(filename)
            collection = CHROMA_CLIENT.get_collection(name=collection_name, embedding_function=EMBEDDING_FUNCTION)
            collection_query = collection.query(query_texts=[user_query], n_results=5)
            context += str(collection_query)
                
        return Response({"response":context})

class LoadCollectionsView(viewsets.ModelViewSet):
    queryset = Queries.objects.all()
    serializer_class = QueriesSerializer

    def list(self, request):            

        info_source = ''

        collections = []
        
        for file in os.listdir(FILES_DIR):
            filename = file.split('.')[0]
            collection_name = get_collection_name(filename)
            
            if self.collection_already_exists(collection_name):
                collections.append(collection_name)
                continue
            else:
                self.create_collection_from_file(file)

        return Response({"collections":collections})
        """
            collection = CHROMA_CLIENT.get_collection(name=collection_name, embedding_function=EMBEDDING_FUNCTION)
            collection_documents = collection.get()['documents']
            collection_text = '*NEW_DOC*'.join(collection_documents)
                
            if collection_text:
                info_source  += f'DOCUMENT TITLE: {file} \n DOCUMENT CONTENT: {collection_text}\n'
        
       """
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
        pdf_text = ""

        if file_ext=='pdf':
            pdf_file = PdfReader('./files/'+file)
            for page in pdf_file.pages:
                pdf_text += page.extract_text()

        splitted_text = re.split('\n \n', pdf_text)

        collection = CHROMA_CLIENT.create_collection(name=collection_name, embedding_function=EMBEDDING_FUNCTION)

        chuncked_text = [
            collection.add(documents=textline, ids=str(i)) 
            for i,textline in enumerate(splitted_text) 
            if textline != "" or textline != " "
        ]

    def get_pdf_by_url(self, url):
        remote_file = urlopen(url).read()
        memory_file = io.BytesIO(remote_file)
        return memory_file



