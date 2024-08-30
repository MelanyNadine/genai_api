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
from core.views.gemini.CachedContext import ChatbotView as GeminiChatBotView1
from core.views.gemini.CachedContext import LoadCacheView
from core.views.gemini.VectorizedContext import ChatbotView as GeminiChatBotView2
from core.views.gemini.VectorizedContext import LoadCollectionsView as LoadGeminiCollectionsView
from core.views.llama.VectorizedContext import ChatbotView as LlamaChatBotView
from core.views.llama.VectorizedContext import LoadCollectionsView
from core.views.Files import FileUploadView
from core.views.Files import FilesRetrievalView
from rest_framework import routers
from django.conf import settings
from django.conf.urls.static import static

router = routers.DefaultRouter()

"""
URLs associated to RAG based on long-context caching
    1. host/api/cached-context/chat
    2. host/api/cached-context/generate-cache
"""
router.register(r'cached-context/chat', GeminiChatBotView1, 'geminichat')
router.register(r'cached-context/refresh-cache', LoadCacheView, 'geminiload')


"""
URLs associated to RAG based on long-context caching
    1. host/api/cached-context/chat
    2. host/api/cached-context/generate-cache
"""

router.register(r'gemini/vectorized-context/gemini-chat', GeminiChatBotView2, 'geminichat2')
router.register(r'gemini/vectorized-context/load-gemini-collections', LoadGeminiCollectionsView, 'geminicollections')

router.register(r'llama/vectorized-context/llama-chat', LlamaChatBotView, 'llamachat')
router.register(r'llama/vectorized-context/load-llama-collections', LoadCollectionsView, 'llamacollections')

"""
URLs associated to Files treatment
"""

router.register(r'get-files', FilesRetrievalView, 'files')
router.register(r'file-upload', FileUploadView, 'fileupload')


urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/', include(router.urls))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)