import base64
import json

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError, JsonResponse
from django.utils.http import http_date
from wsgiref.util import FileWrapper
from .models import Material, ChatSession
from .utils import process_material, summarize_text, extract_entities
import os

User = get_user_model()


@login_required
def home_page(request):
    materials = Material.objects.filter(user=request.user)

    for material in materials:
        material.url = material.get_url()
        material.file_url = material.get_file_url()
    return render(request, 'core/home_page.html', {'materials': materials})


def create_chat_session_and_get_context(request, material):
    context = f"Transcript: {material.transcript}\nSummary: {material.summary}\nEntities: {material.entities}"
    chat_session, created = ChatSession.objects.get_or_create(material=material, user=request.user,
                                                              defaults={'context': context})
    chat_messages = chat_session.messages.all()
    return {
        'material': material,
        'material_data': json.dumps({'file_url': material.get_file_url(), 'material_type': material.material_type}),
        'chat_messages': chat_messages,
        'chat_session': chat_session.pk
    }


@login_required
def document_detail(request, pk):
    material = get_object_or_404(Material, pk=pk, user=request.user)
    context = create_chat_session_and_get_context(request, material)
    return render(request, 'core/document.html', context)


@login_required
def video_detail(request, pk):
    material = get_object_or_404(Material, pk=pk)
    context = create_chat_session_and_get_context(request, material)
    return render(request, 'core/video.html', context)


@login_required
def audio_detail(request, pk):
    material = get_object_or_404(Material, pk=pk)
    context = create_chat_session_and_get_context(request, material)
    return render(request, 'core/audio.html', context)


@login_required
def delete_material(request, pk):
    if request.method == 'POST':
        material = get_object_or_404(Material, pk=pk, user=request.user)
        try:
            material.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})


def serve_media(request, path):
    try:
        media_path = os.path.join('media', path)
        extension = os.path.splitext(media_path)[1].lower()

        video_extensions = ['.mp4', '.avi', '.mov']
        audio_extensions = ['.wav', '.mp3']

        if extension in video_extensions:
            content_type = 'video/mp4'
        elif extension in audio_extensions:
            content_type = 'audio/mpeg'
        else:
            return HttpResponseNotFound('<h1>File type not supported</h1>')

        file_size = os.path.getsize(media_path)
        file = open(media_path, 'rb')

        content_range = request.headers.get('Range', None)
        if content_range:
            content_range = content_range.strip().split('=')[-1]
            range_start, range_end = content_range.split('-')
            range_start = int(range_start)
            range_end = int(range_end) if range_end else file_size - 1
            length = range_end - range_start + 1
            file.seek(range_start)
            response = HttpResponse(
                FileWrapper(file, length),
                status=206,
                content_type=content_type,
            )
            response['Content-Length'] = str(length)
            response['Content-Range'] = f'bytes {range_start}-{range_end}/{file_size}'
        else:
            response = HttpResponse(
                FileWrapper(file),
                content_type=content_type,
            )
            response['Content-Length'] = str(file_size)
        response['Accept-Ranges'] = 'bytes'
        response['Last-Modified'] = http_date(os.path.getmtime(media_path))
        return response
    except FileNotFoundError:
        return HttpResponseNotFound('<h1>File not found</h1>')
    except Exception as e:
        return HttpResponseServerError(f'<h1>Server error: {e}</h1>')


@login_required
def upload_material(request):
    if request.method == 'POST':
        file_title = request.POST.get('file_title')
        uploaded_file = request.FILES.get('material')

        if uploaded_file:
            extension = os.path.splitext(uploaded_file.name)[1].lower()
            if extension in ['.pdf']:
                material_type = 'pdf'
            elif extension in ['.doc', '.docx']:
                material_type = 'word'
            elif extension in ['.mp4', '.avi', '.mov']:
                material_type = 'video'
            elif extension in ['.wav', '.mp3']:
                material_type = 'audio'
            else:
                material_type = 'unsupported'

            if material_type == 'unsupported':
                return JsonResponse({'success': False, 'error': 'Unsupported file type'})

            try:
                # Save material instance to make file accessible at material.file.path
                material = Material.objects.create(
                    user=request.user,
                    title=file_title,
                    file=uploaded_file,
                    material_type=material_type
                )

                file_path = material.file.path
                processed_text = process_material(material_type, file_path)

                if processed_text:
                    material.transcript = processed_text
                    material.summary = summarize_text(processed_text)
                    material.entities = extract_entities(processed_text)

                    # Only save if transcript, summary, and entities are set
                    if material.transcript and material.summary and material.entities:
                        if material.transcript.strip() and material.summary.strip() and material.entities.strip():
                            material.save()
                            return JsonResponse({'success': True, 'material_id': material.id})
                    else:
                        return JsonResponse(
                            {'success': False, 'error': 'Processing incomplete. Required fields missing.'})
                else:
                    return JsonResponse({'success': False, 'error': 'Error processing material text'})

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        else:
            return JsonResponse({'success': False, 'error': 'No file uploaded'})

    return render(request, 'core/home_page.html')


def upload_voice_message(request):
    if request.method == 'POST':
        chat_session_id = request.POST.get('chat_session_id')
        uploaded_file = request.FILES.get('voice_message')

        if uploaded_file and chat_session_id:
            try:
                fs = FileSystemStorage()
                filename = fs.save(uploaded_file.name, uploaded_file)
                file_path = fs.path(filename)

                with open(file_path, 'rb') as audio_file:
                    audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')

                return JsonResponse({'success': True, 'audio_base64': audio_base64})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        else:
            return JsonResponse({'success': False, 'error': 'No file uploaded or chat_session_id not provided'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})
