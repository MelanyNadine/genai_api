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
import io
import re
import os
import time
from google.generativeai import caching
import datetime
import base64
from dotenv import load_dotenv

#pointer-behaviour emulator
CACHE_ID = [None]

def reduce_name(filename):
    return re.sub(r'[^\w\s]', '', filename.replace(" ",""))

class ChatbotView(viewsets.ModelViewSet):
    queryset = Queries.objects.all()
    serializer_class = QueriesSerializer

    def get_last_cache(self):
        """
        LAST CACHE RETRIEVAL

        
        """

        # If cache was set by LoadCacheView api calling, it's just returned
        if not CACHE_ID[0]:
            cached_content = caching.CachedContent.list()
            cache_data = [str(c) for c in cached_content]
            last_cache_from_stack = n = cache_data[0]

            # Stringified CachedContent object has some properties, being the first name.
            # Since it looks like <CachedContent(name='...') the characters to be considered
            # are = and '.
            name_start = lambda stringified_cache : stringified_cache.index('=') + 2
            name_end = lambda stringified_cache : stringified_cache.index("'", name_start(n) + 3)

            # CachedContent objects in cache_data list are stringified and the last in -
            # first out is separated from its first property: name='cache id'
            last_cache_id = last_cache_from_stack[name_start(n):name_end(n)]
            
            # the memory space previously reserved is set
            CACHE_ID[0] = last_cache_id

        return CACHE_ID[0]

    def create(self,request):
        user_query = request.data.get('query')
        genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
 
        try:
            cached_context = caching.CachedContent.get(name=self.get_last_cache())
        except:
            return Response({"response": "Cache has expired. Reload it!"})

        model = genai.GenerativeModel.from_cached_content(cached_content=cached_context)

        start_time = time.time() 
        response = model.generate_content(user_query)
        end_time = time.time()

        response_entry = {
            "query": user_query,
            "response": response.text, 
            "response_time": end_time - start_time   
        }
                
        return Response(response_entry)

class LoadCacheView(viewsets.ModelViewSet):
    queryset = Queries.objects.all()
    serializer_class = QueriesSerializer

    get_name = lambda self, file : file.split('.')[0]
    get_ext = lambda self, file : file.split('.')[1]

    txts_dir = './txts/'
    txt_files = os.listdir(txts_dir)

    def list(self, request):            

        context = self.get_or_create_files_context()
        cache_limit = 72 #hours

        cache = caching.CachedContent.create(
            model='models/gemini-1.5-flash-001',
            display_name='manuals test',
            system_instruction=(
                'You are an assistant bot that answers questions using text from the source information provided.'
                'You are allowed to obtain information only from the source information here specified;'
                'Include in the answer the name of the file from which you obtained the information.'
            ),
            contents=[context],
            ttl=datetime.timedelta(hours=cache_limit),
        )

        CACHE_ID[0] = cache.name

        return Response({
            "response": "Cached Context have been uploaded/updated", 
            "cache_id": CACHE_ID[0], 
            "cache_duration": f'{cache_limit} hours'
        })
    
    def get_or_create_files_context(self):
        pdf_pages = []
        files_dir = './files/'
        pdf_files = os.listdir(files_dir)
        
        context = self.get_previous_context_from_txt_files()
        
        for pdf_file in pdf_files:
            filename = self.get_name(pdf_file)
            file_ext = self.get_ext(pdf_file)
            reduced_name = reduce_name(filename)

            # if pdf file name exists as a .txt file listed in txts directory the process
            # of conversion was done before so it continues to next item in the loop
            if f'{filename}.txt' in self.txt_files:
                continue

            if file_ext=='pdf':
                pdf_content = PdfReader('./files/' + pdf_file)

                # the more the files, the more time it requires for processing. For scalability purposes
                # this approach might need to be changed in the future. Time complexity: O(k \cdot n)
                pdf_pages = [page.extract_text() for page in pdf_content.pages if page.extract_text()]

                pdf_title = filename
                pdf_text = '\n'.join(pdf_pages)
                pdftxt_data = [pdf_title, pdf_text]

                context += f'DOCUMENT TITLE: {pdf_title} \n CONTENT: {pdf_text} \n'

                with open(f'{txts_dir}{filename}.txt', 'w', encoding="utf-8") as file:
                    file.writelines(pdftxt_data)
        
        return context

    def get_previous_context_from_txt_files(self):

        context = ""

        for txt_file in self.txt_files:
            filename = self.get_name(txt_file)
            with open(f'{self.txts_dir}{txt_file}', 'r', encoding="utf-8") as file:
                context += f'DOCUMENT TITLE: {filename} \n CONTENT: {file.read()} \n'
                
        return context

    def get_pdf_by_url(self, url):
        remote_file = urlopen(url).read()
        memory_file = io.BytesIO(remote_file)
        return memory_file
