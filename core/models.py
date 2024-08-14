from django.db import models

from django.db import models
from django.conf import settings

class Files(models.Model):
    id = models.AutoField(primary_key=True)
    filename = models.CharField(max_length=45)
    filedata = models.FileField()

    def __str__(self):
        return self.filename