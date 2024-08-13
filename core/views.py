from django.shortcuts import render
from collections import OrderedDict
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import generics
from core.serializers import FilesSerializer
from core.models import Files

class ChatbotView(viewsets.ModelViewSet):
    queryset = Files.objects.all()
    serializer_class = FilesSerializer

    def list(self, request):
        return Response({"test":"this is a test"})
