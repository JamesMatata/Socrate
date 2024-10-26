# core/urls.py
from django.urls import path
from core import views

app_name = 'core'

urlpatterns = [
    path('', views.home_page, name='home'),
    path('upload_material/', views.upload_material, name='upload_material'),
    path('document/<int:pk>/', views.document_detail, name='document_detail'),
    path('video/<int:pk>/', views.video_detail, name='video_detail'),
    path('audio/<int:pk>/', views.audio_detail, name='audio_detail'),
    path('media/<path:path>/', views.serve_media, name='serve_media'),
    path('delete_material/<int:pk>/', views.delete_material, name='delete_material'),
    path('upload_voice_message/', views.upload_voice_message, name='upload_voice_message'),
]

