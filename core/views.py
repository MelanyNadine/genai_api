from django.shortcuts import render
from collections import OrderedDict
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import generics
from core.serializers import FilesSerializer
from core.models import Files

import google.generativeai as genai
import pathlib
from pypdf import PdfReader

class ChatbotView(viewsets.ModelViewSet):
    queryset = Files.objects.all()
    serializer_class = FilesSerializer

    # Log in to huggingface and grant authorization to huggingchat
    

    def list(self, request):
        model = genai.GenerativeModel("gemini-1.5-flash")
        genai.configure(api_key="AIzaSyBxQN3piIIVdqA8Xzdpyq-kzARmn_WqrSU")
        #response = model.generate_content("Write a story about a magic backpack.")
        pdf_text = load_pdf(file_path="https://az184419.vo.msecnd.net/schneider-trucks/PDF/maintenance/TriPac-EVOLUTION-Operators-Manual-55711-19-OP-Rev.-0-06-13.pdf")
        return Response({"response":pdf_text})


    def load_pdf(file_path):
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

        