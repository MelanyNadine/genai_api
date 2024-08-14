from django.shortcuts import render
from collections import OrderedDict
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.decorators import api_view
from core.serializers import FilesSerializer
from core.models import Files

import google.generativeai as genai
import pathlib
from pypdf import PdfReader
from urllib.request import urlopen
from pyPdf import PdfFileWriter, PdfFileReader

class ChatbotView(viewsets.ModelViewSet):
    queryset = Files.objects.all()
    serializer_class = FilesSerializer

    # Log in to huggingface and grant authorization to huggingchat
    
    
    def list(self, request):
        model = genai.GenerativeModel("gemini-1.5-flash")
        genai.configure(api_key="AIzaSyBxQN3piIIVdqA8Xzdpyq-kzARmn_WqrSU")
        #response = model.generate_content("Write a story about a magic backpack.")
        remote_file = urlopen("https://web.stanford.edu/class/archive/cs/cs110/cs110.1214/static/lectures/cs110-lecture-17-mapreduce.pdf").read()
        memory_file = StringIO(remoteFile)
        pdf_file = PdfFileReader(memoryFile)
        pdf_text = ""
        for page in pdf_file.pages:
            pdf_text += page.extract_text()

        return Response({"response":pdf_text})

    @api_view(['GET', 'POST'])
    def post(self):
        return 0
        