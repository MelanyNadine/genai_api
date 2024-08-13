from django.db import models

from django.db import models
from django.utils import timezone
from django.conf import settings

class Files(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=45)
    encodedFile = models.TextField()