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
import io
import re
import os

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