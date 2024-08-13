from django.shortcuts import render
from collections import OrderedDict
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import generics
from core.serializers import FilesSerializer
from core.models import Files

import google.generativeai as genai
import pathlib

class ChatbotView(viewsets.ModelViewSet):
    queryset = Files.objects.all()
    serializer_class = FilesSerializer

    # Log in to huggingface and grant authorization to huggingchat
    

    def list(self, request):
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Write a story about a magic backpack.")

        return Response({"response":response.text})


        