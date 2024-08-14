from django import forms

class UploadFileForm(forms.Form):
    filename = forms.CharField(max_length=45)
    filedata = forms.FileField()