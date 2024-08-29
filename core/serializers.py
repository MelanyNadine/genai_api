from rest_framework import serializers
from core.models import Files
from core.models import Queries

class FilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Files
        fields = '__all__'

class QueriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queries
        fields = '__all__'