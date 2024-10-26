from django.contrib import admin

from core.models import Material, ChatMessage, ChatSession

admin.site.register(Material)
admin.site.register(ChatSession)
admin.site.register(ChatMessage)
