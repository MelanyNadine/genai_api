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

class ChatbotView(viewsets.ModelViewSet):
    queryset = Files.objects.all()
    serializer_class = FilesSerializer
    
    def list(self, request):
        return Response({"response":"Welcome to rag demo. Try doing a POST request with your query"})
    
    def get_collection_name(self, filename):
        return re.sub(r'[^\w\s]', '', filename.replace(" ",""))

    def create(self,request):
        user_query = request.data.get('query')
        chroma_client = chromadb.PersistentClient(path='./')
        default_ef = embedding_functions.DefaultEmbeddingFunction()

        load_dotenv()
        genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))

        info_source = ''

        for file in os.listdir('./files'):
            filename = file.split('.')[0]
            try:
                collection_name = self.get_collection_name(filename)
            except:
                continue

            collection = chroma_client.get_collection(name=collection_name, embedding_function=default_ef)
            collection_documents = collection.get()['documents']
            collection_text = '*NEW_DOC*'.join(collection_documents)
                
            if collection_text:
                info_source  += f'DOCUMENT TITLE: {file} \n DOCUMENT CONTENT: {collection_text}\n'

        cache = caching.CachedContent.create(
            model='models/gemini-1.5-flash-001',
            display_name='manuals test',
            system_instruction=(
                'You are an assistant bot that answers questions using text from the source information provided.'
                'You are allowed to obtain information only from the source information here specified;'
                'Include in the answer the name of the file from which you obtained the information.'
            ),
            contents=[info_source],
            ttl=datetime.timedelta(minutes=10),
        )

        model = genai.GenerativeModel.from_cached_content(cached_content=cache)
        response = model.generate_content(user_query)
                
        return Response({"response":response.text})


class LoadRagView(viewsets.ModelViewSet):
    queryset = Files.objects.all()
    serializer_class = FilesSerializer

    def list(self, request):
        chroma_client = chromadb.PersistentClient(path='./')
        default_ef = embedding_functions.DefaultEmbeddingFunction()

        for file in os.listdir('./files'):
            filename = file.split('.')[0]
            collection_name = self.get_collection_name(filename)
    
            if self.collection_already_exists(collection_name):
                continue
            else:
                self.create_collection_from_file(file)

        return Response({"response": "Collections have been uploaded/updated"})

    def get_collection_name(self, filename):
        return re.sub(r'[^\w\s]', '', filename.replace(" ",""))

    def collection_already_exists(self, collection_name):
        chroma_client = chromadb.PersistentClient(path='./')
        default_ef = embedding_functions.DefaultEmbeddingFunction()
        try:
            collection = chroma_client.get_collection(name=collection_name, embedding_function= default_ef)
            return True
        except:
            return False
        
    def create_collection_from_file(self, file):
        chroma_client = chromadb.PersistentClient(path='./')
        default_ef = embedding_functions.DefaultEmbeddingFunction()

        filename = file.split('.')[0]
        file_ext = file.split('.')[1]
        collection_name = self.get_collection_name(filename)
        collection_text = ""

        if file_ext=='pdf':
            pdf_file = PdfReader('./files/'+file)
            for page in pdf_file.pages:
                collection_text += page.extract_text()
        """elif file_ext=='txt':
            collection_text"""

        splitted_text = re.split('\n \n', collection_text)
        chuncked_text = [textline for textline in splitted_text if textline != "" or textline != " "]

        chroma_client = chromadb.PersistentClient(path='./')
        
        default_ef = embedding_functions.DefaultEmbeddingFunction()

        if chuncked_text:
            collection = chroma_client.create_collection(name=collection_name, embedding_function=default_ef)
            
            for i, textline in enumerate(chuncked_text):
                collection.add(documents=textline, ids=str(i)) 

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

class MergeFilesView(viewsets.ModelViewSet):
    queryset = Files.objects.all()
    serializer_class = FilesSerializer

    def list(self, request):
        filespath = './files/'
        files = os.listdir(filespath)

        merged_pdfs_text = '''You are an assistant bot that answers questions using text from the source information
        included below. You are allowed to obtain information only from the source information here specified.
        If the source information is irrelevant to the answer, you may ignore it. Include in the answer the name
        of the file from which you obtained the information.\
        '''
        
        files = os.listdir('./files')
      
        for file in files:
            pdf_file = PdfReader('./files/'+file)
            for page in pdf_file.pages:
              filename = file.split('.')[0]
              file_ext = file.split('.')[1]
              if file_ext=='pdf':
                  merged_pdfs_text += f'TITLE: {filename} \t FILE: {file} \n '
                  merged_pdfs_text += page.extract_text() + '\n'

        with open('./files/mergedFiles/secondtest_xd.txt', 'w') as file:
            file.write(merged_pdfs_text)
            file.close()

        return Response({"response":"File has been created!"})


class AskPurelyLlamaView(viewsets.ModelViewSet):
    queryset = Files.objects.all()
    serializer_class = FilesSerializer

    def list(self, request):
        model_id = "meta-llama/Meta-Llama-3.1-8B-Instruct"

        login(token = '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')

        pipeline = transformers.pipeline(
            "text-generation",
            model=model_id,
            model_kwargs={"torch_dtype": torch.bfloat16},
            device_map="auto",
        )

        messages = [
            {"role": "system", "content": "You are an assistant bot"},
            {"role": "user", "content": "Who are you?"},
        ]

        outputs = pipeline(
            messages,
            max_new_tokens=256,
        )

        bot_response = outputs[0]["generated_text"][-1]

        return bot_response
