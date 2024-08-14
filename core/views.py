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

class ChatbotView(viewsets.ModelViewSet):
    queryset = Files.objects.all()
    serializer_class = FilesSerializer
    
    def list(self, request):
        return Response({"response":"Welcome to rag demo. Try doing a POST request with your query"})
        

    def create(self,request):
        user_query = request.data.get('query')
        model = genai.GenerativeModel('gemini-1.5-flash')
        genai.configure(api_key="AIzaSyBxQN3piIIVdqA8Xzdpyq-kzARmn_WqrSU")

        chroma_client = chromadb.PersistentClient(path='./')
        default_ef = embedding_functions.DefaultEmbeddingFunction()

        db = chroma_client.get_collection(name="DemoRag", embedding_function= default_ef)

        query = user_query
        passage = db.query(query_texts=[query], n_results=5)['documents'][0]

        prompt = f'''You are a helpful and informative bot that answers questions using text from the reference passage included below. Be sure to respond in a complete sentence, being comprehensive, including all relevant background information. If the passage is irrelevant to the answer, you may ignore it. \
          QUESTION: "{query}"
          PASSAGE: "{passage}"
          '''
        response = model.generate_content(prompt)

        return Response({"response":response.text})


class LoadRagView(viewsets.ModelViewSet):
    queryset = Files.objects.all()
    serializer_class = FilesSerializer

    def list(self, request):
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        genai.configure(api_key="AIzaSyBxQN3piIIVdqA8Xzdpyq-kzARmn_WqrSU")
        
        remote_file = urlopen("https://web.stanford.edu/class/archive/cs/cs110/cs110.1214/static/lectures/cs110-lecture-17-mapreduce.pdf").read()
        memory_file = io.BytesIO(remote_file)
        pdf_file = PdfReader(memory_file)
        pdf_text = ""

        for page in pdf_file.pages:
            pdf_text += page.extract_text()

        splitted_text = re.split('\n \n', pdf_text)
        chuncked_text = [i for i in splitted_text if i != ""]

        chroma_client = chromadb.PersistentClient(path='./')
        
        default_ef = embedding_functions.DefaultEmbeddingFunction()

        db = chroma_client.create_collection(name="DemoRag", embedding_function=default_ef)
        
        for idx, document in enumerate(chuncked_text):
            db.add(documents=document, ids=str(idx))

        return Response({"response": "rag has been loaded!"})

class FileUploadView(viewsets.ModelViewSet):
    queryset = Files.objects.all()
    serializer_class = FilesSerializer

    def create(self, request):
        filename = request.data.get('filename')
        filedata = request.data.get('filedata')
        new_file = Files(filename=filename)
        new_file.filedata = filedata
        new_file.save()
        if filedata:
            default_storage.save("./"+filename, ContentFile(b''+bytes.fromhex(filedata)))
        
        return Response({"response": "File has been loaded!"})

class FilesRetrievalView(viewsets.ModelViewSet):
    queryset = Files.objects.all()
    serializer_class = FilesSerializer

    def list(self, request):
        filespath = '/files/'
        files = os.listdir(filespath)

        return Response({"response": files})