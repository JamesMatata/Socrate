from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

User = get_user_model()


class Material(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='materials/')
    material_type = models.CharField(max_length=50)
    transcript = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    entities = models.JSONField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_url(self):
        if self.material_type in ['pdf', 'word']:
            return reverse('core:document_detail', args=[str(self.id)])
        elif self.material_type == 'video':
            return reverse('core:video_detail', args=[str(self.id)])
        elif self.material_type == 'audio':
            return reverse('core:audio_detail', args=[str(self.id)])
        return '#'

    def get_file_url(self):
        return self.file.url


class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    material = models.ForeignKey('Material', on_delete=models.CASCADE)
    context = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)  # Add this field to store conversation summary
    created_at = models.DateTimeField(auto_now_add=True)


class ChatMessage(models.Model):
    chat_session = models.ForeignKey(ChatSession, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    message_type = models.CharField(max_length=10, default='text')
    voice_file = models.FileField(upload_to='voice_messages/', null=True, blank=True)

    def __str__(self):
        return self.content
