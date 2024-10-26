import io
import json
import time
import base64
import openai
from gtts import gTTS
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from Socrate.settings import OPENAI_API_KEY
from .models import ChatMessage, ChatSession

User = get_user_model()
openai.api_key = OPENAI_API_KEY


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.session_id}'
        user = self.scope['user']

        if user.is_authenticated:
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            await self.create_initial_message_if_new()
            print(f"User {user.username} connected to session {self.session_id}.")
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        message_type = text_data_json.get('type', 'text')
        user = self.scope['user']

        print(f"Received message: {message} of type {message_type}")

        if user.is_authenticated:
            chat_session = await self.get_chat_session()
            if message_type == 'voice':
                user_message = await self.speech_to_text_conversion(message)
                user_voice_file = await self.save_voice_file(message, 'user_voice')
            else:
                user_message = message
                user_voice_file = None

            await self.save_message(chat_session, user, user_message, message_type, user_voice_file)
            print(f"User message saved: {user_message}")

            ai_response = await self.get_ai_response(chat_session, user_message)
            print(f"AI response: {ai_response}")

            if message_type == 'voice':
                ai_voice_response = await self.text_to_speech_conversion(ai_response)
                ai_voice_file = await self.save_voice_file(ai_voice_response, 'ai_voice')
                await self.save_message(chat_session, None, ai_response, 'voice', ai_voice_file)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': ai_voice_response,
                        'username': 'AI',
                        'message_type': 'voice',
                        'is_ai': True
                    }
                )
            else:
                await self.save_message(chat_session, None, ai_response)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': ai_response,
                        'username': 'AI',
                        'message_type': 'text',
                        'is_ai': True
                    }
                )
        else:
            print("User not authenticated.")

    @database_sync_to_async
    def get_chat_session(self):
        return ChatSession.objects.get(pk=self.session_id)

    @database_sync_to_async
    def save_message(self, chat_session, sender, content, message_type='text', voice_file=None):
        return ChatMessage.objects.create(
            chat_session=chat_session,
            sender=sender,
            content=content,
            message_type=message_type,
            voice_file=voice_file
        )

    async def get_ai_response(self, chat_session, user_message):
        context = chat_session.summary or chat_session.context
        recent_messages = await self.get_recent_messages(chat_session)

        for msg in recent_messages:
            sender_username = await self.get_sender_username(msg)
            context += f"\n{sender_username if sender_username else 'AI'}: {msg.content}"

        try:
            # Use acreate for async requests
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": chat_session.context},
                    {"role": "user", "content": user_message}
                ]
            )
            ai_response = response.choices[0].message['content'].strip()
            return ai_response
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return "Sorry, I couldn't process your request."

    async def speech_to_text_conversion(self, audio_base64):
        audio_bytes = base64.b64decode(audio_base64)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav"  # Setting the name attribute

        response = await sync_to_async(openai.Audio.transcribe)(
            model="whisper-1",
            file=audio_file,
            language='en'  # Ensure the language is set to English
        )
        return response['text'].strip()

    async def text_to_speech_conversion(self, text):
        tts = gTTS(text=text, lang='en')
        audio_file = io.BytesIO()
        tts.write_to_fp(audio_file)
        audio_file.seek(0)
        audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
        return audio_base64

    async def save_voice_file(self, audio_base64, prefix):
        audio_bytes = base64.b64decode(audio_base64)
        file_name = f"{prefix}_{self.session_id}_{int(time.time())}.mp3"
        audio_file = ContentFile(audio_bytes, name=file_name)
        return audio_file

    @database_sync_to_async
    def get_recent_messages(self, chat_session):
        return list(ChatMessage.objects.filter(chat_session=chat_session).order_by('-timestamp')[:5])

    @database_sync_to_async
    def get_sender_username(self, msg):
        return msg.sender.username if msg.sender else None

    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        message_type = event['message_type']
        is_ai = event['is_ai']

        print(f"Sending message to frontend: {message}")

        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'message_type': message_type,
            'is_ai': is_ai
        }))

    async def create_initial_message_if_new(self):
        chat_session = await self.get_chat_session()
        existing_messages = await self.get_existing_messages(chat_session)
        if not existing_messages:
            initial_message = await self.generate_initial_message(
                await sync_to_async(lambda: chat_session.material.material_type)()
            )
            await self.save_message(chat_session, None, initial_message)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': initial_message,
                    'username': 'AI',
                    'message_type': 'text',
                    'is_ai': True
                }
            )

    @database_sync_to_async
    def get_existing_messages(self, chat_session):
        return ChatMessage.objects.filter(chat_session=chat_session).exists()

    async def generate_initial_message(self, material_type):
        prompt = f"""
        Generate a welcoming message for a new chat session about a {material_type} material.
        The message should be in the following format:
        'Hello there, I'm Socrate. If you have any questions concerning this {material_type} material, I'm open for discussion.'
        """

        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": ""}
            ]
        )

        initial_message = response.choices[0].message['content'].strip()
        return initial_message
