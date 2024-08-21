"""
URL configuration for genai_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from core.views import ChatbotView
from core.views import LoadRagView
from core.views import FileUploadView
from core.views import FilesRetrievalView
from core.views import MergeFilesView
from rest_framework import routers
from django.conf import settings
from django.conf.urls.static import static

router = routers.DefaultRouter()
router.register(r'chat', ChatbotView, 'chat')
router.register(r'rag', LoadRagView, 'init')
router.register(r'file-upload', FileUploadView, 'fileupload')
router.register(r'get-files', FilesRetrievalView, 'getfiles')
router.register(r'make-merged_file', MergeFilesView, 'makemergedfile')

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/', include(router.urls))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)