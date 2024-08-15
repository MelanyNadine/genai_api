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

        info_sources = []

        for file in os.listdir('./files'):
            filename = file.split('.')[0]
            collection_name = filename.replace(" ","")
    
            if self.collection_does_not_exists(collection_name):
                continue

            collection = chroma_client.get_collection(name=collection_name)
            collection_query = collection.query(query_texts=[filename], n_results=5)['documents'][0]
                
            if collection_query:
                info_sources.append({"file": file, "info": collection_query})

        prompt = f'''You are an assistant bot that answers questions using text from the source information
        included below. You are allowed to obtain information only from the source information here specified.
        If the source information is irrelevant to the answer, you may ignore it. Include in the answer the name
        of the file from which you obtained the information.\
        QUESTION: {user_query}
        SOURCE INFORMATION: {str(info_sources)}
        '''
        response = model.generate_content(prompt)

        return Response({"response":response.text})

    def collection_does_not_exists(self,  collection_name):
        chroma_client = chromadb.PersistentClient(path='./')
        default_ef = embedding_functions.DefaultEmbeddingFunction()
        try:
            collection = chroma_client.get_collection(name=collection_name, embedding_function= default_ef)
            return False
        except:
            return True


class LoadRagView(viewsets.ModelViewSet):
    queryset = Files.objects.all()
    serializer_class = FilesSerializer

    def list(self, request):
        chroma_client = chromadb.PersistentClient(path='./')
        default_ef = embedding_functions.DefaultEmbeddingFunction()
        
        for file in os.listdir('./files'):
            if self.collection_already_exists(file):
                continue
            else:
                self.create_collection_from_file(file)
        #"Collections have been created/updated!"
        return Response({"response": "Collections have been created/updated!"})

    def collection_already_exists(self, filename):
        chroma_client = chromadb.PersistentClient(path='./')
        default_ef = embedding_functions.DefaultEmbeddingFunction()
        collection_name = filename.split('.')[0].replace(" ","")
        try:
            collection = chroma_client.get_collection(name=collection_name, embedding_function= default_ef)
            return True
        except:
            return False
        

    def create_collection_from_file(self, filename):
        model = genai.GenerativeModel('gemini-1.5-flash')
        genai.configure(api_key="AIzaSyBxQN3piIIVdqA8Xzdpyq-kzARmn_WqrSU")
        chroma_client = chromadb.PersistentClient(path='./')
        default_ef = embedding_functions.DefaultEmbeddingFunction()

        collection_name = filename.split('.')[0].replace(" ","")
        file_ext = filename.split('.')[1]
        collection_text = ""

        if file_ext=='pdf':
            pdf_file = PdfReader('./files/'+filename)
            for page in pdf_file.pages:
                collection_text += page.extract_text()
        elif file_ext=='txt':
            collection_text

        splitted_text = re.split('\n \n', collection_text)
        chuncked_text = [i for i in splitted_text if i != ""]

        chroma_client = chromadb.PersistentClient(path='./')
        
        default_ef = embedding_functions.DefaultEmbeddingFunction()

        db = chroma_client.create_collection(name=collection_name, embedding_function=default_ef)
        
        for idx, document in enumerate(chuncked_text):
            db.add(documents=document, ids=str(idx))

        return 'success' if db else 'failed'

    def get_pdf_by_url(self, url):
        remote_file = urlopen(url).read()
        memory_file = io.BytesIO(remote_file)
        return memory_file

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
        filespath = './files/'
        files = os.listdir(filespath)

        return Response({"response": files})