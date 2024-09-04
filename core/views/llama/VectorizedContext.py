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
from transformers import AutoTokenizer, AutoConfig, LlamaForCausalLM
import torch
from huggingface_hub import login
import datetime
import base64
from dotenv import load_dotenv

"""

"""


CHROMA_CLIENT = chromadb.PersistentClient(path='./llama_collections/')

""" Options for Embedding Functions

1. Hugging Face Embedding Function
2. Sentence Transformer Embedding Function (Default)
"""
HUGGINGFACE_EF = embedding_functions.HuggingFaceEmbeddingFunction(
    api_key="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",
    model_name="meta-llama/Meta-Llama-3.1-8B"
)

DEFAULT_EF = embedding_functions.DefaultEmbeddingFunction()

""" Embedding Function setting

This Embedding function is used to create the vector store. It's used in both classes
here defined.
"""

EMBEDDING_FUNCTION = DEFAULT_EF

FILES_DIR = './files'

#Removes all the special characters in the filename later to become the collection name
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

    def create(self,request):
        user_query = request.data.get('query')

        context = ''
        
        for file in os.listdir(FILES_DIR):
            filename = file.split('.')[0]
            collection_name = get_collection_name(filename)
            collection = CHROMA_CLIENT.get_collection(name=collection_name, embedding_function=EMBEDDING_FUNCTION)
            collection_query = collection.query(query_texts=[user_query], n_results=5)
            context += str(collection_query)

        
        parent = os.path.dirname(os.getcwd())
        model_path = "C:\\Users\\mmonroy\\Documents\\Projects\\CarozziDemoApp\\Meta-Llama3.1-8B" 
        
        model = LlamaForCausalLM.from_pretrained(
            model_path,
            config=AutoConfig.from_pretrained(model_path)
        )

        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            config=AutoConfig.from_pretrained(model_path)
        )

        messages = [
            {
                "role": "system",
                "content": "You are a friendly chatbot who always responds in the style of a pirate",
            },
            {
                "role": "user", 
                "content": "Who are you?"
            },
        ]

        chat_template = "{% for message in messages %}{{'<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>' + '\n'}}{% endfor %}"
        tokenizer.chat_template = chat_template

        #bot_response = outputs[0]["generated_text"][-1]
        #bot_response = tokenizer.apply_chat_template(chat_config, tokenize=False)      
        tokenized_chat = tokenizer.apply_chat_template(messages, tokenize=True)

        prompt = "Hey, are you conscious? Can you talk to me?"

        inputs = tokenizer(prompt, return_tensors="pt")

        generate_ids = model.generate(inputs.input_ids, max_length=30)

        bot_response = tokenizer.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
        #bot_response = model.generate(tokenized_chat, max_new_tokens=1024) 
        return Response({"response": bot_response})

class LoadCollectionsView(viewsets.ModelViewSet):
    queryset = Queries.objects.all()
    serializer_class = QueriesSerializer

    def list(self, request):            

        info_source = ''

        collections = []
        
        for file in os.listdir(FILES_DIR):
            filename = file.split('.')[0]
            collection_name = get_collection_name(filename)
            
            if collection_already_exists(collection_name):
                collections.append(collection_name)
                continue
            else:
                self.create_collection_from_file(file)

        return Response({"collections":collections})
        
    def create_collection_from_file(self, file):

        filename = file.split('.')[0]
        file_ext = file.split('.')[1]
        collection_name = get_collection_name(filename)
        pdf_text = ""

        if file_ext=='pdf':
            pdf_file = PdfReader('./files/'+file)
            for page in pdf_file.pages:
                pdf_text += page.extract_text()

        splitted_text = pdf_text.split('\n')

        chuncked_text = [textline for textline in splitted_text if textline != "" or textline != " "]
        
        if chuncked_text:
            collection = CHROMA_CLIENT.create_collection(name=collection_name, embedding_function=EMBEDDING_FUNCTION)

            for i,textline in enumerate(chuncked_text):
                collection.add(documents=textline, ids=str(i))        
     
    def get_pdf_by_url(self, url):
        remote_file = urlopen(url).read()
        memory_file = io.BytesIO(remote_file)
        return memory_file

    def delete_collection(self, collection_name):
        CHROMA_CLIENT.delete_collection(name=collection_name)



