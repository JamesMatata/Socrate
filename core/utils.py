import fitz  # PyMuPDF
import pytesseract
from docx import Document
from google.cloud import speech_v1p1beta1 as speech, vision
from moviepy.editor import VideoFileClip
import io
import cv2
import wave
import json
from vosk import Model, KaldiRecognizer
from transformers import pipeline
import spacy
from PIL import Image
import numpy as np
import time
import logging
import re
# import requests

# Ensure tesseract executable path is correctly set
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load models globally
logger.info("Loading summarization pipeline...")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
logger.info("Summarization pipeline loaded.")

logger.info("Loading spaCy model...")
nlp = spacy.load("en_core_web_sm")
logger.info("spaCy model loaded.")

MAX_TOKEN_LENGTH = 512


def chunk_text_by_token_length(text, max_length=512):
    words = text.split()
    current_chunk = []
    current_length = 0

    for word in words:
        word_length = len(word)
        if current_length + word_length + 1 <= max_length:
            current_chunk.append(word)
            current_length += word_length + 1
        else:
            yield " ".join(current_chunk)
            current_chunk = [word]
            current_length = word_length + 1

    if current_chunk:
        yield " ".join(current_chunk)


def summarize_text(text):
    start_time = time.time()
    logger.info("Starting text summarization...")

    chunks = list(chunk_text_by_token_length(text))
    summaries = []

    for chunk in chunks:
        summary = summarizer(chunk, max_length=150, min_length=30, do_sample=False)
        summaries.append(summary[0]['summary_text'])

    combined_summary = " ".join(summaries)
    end_time = time.time()
    logger.info(f"Text summarization completed in {end_time - start_time:.2f} seconds.")

    return combined_summary


def extract_entities(text):
    start_time = time.time()
    logger.info("Starting entity extraction...")
    doc = nlp(text)
    entities = [(entity.text, entity.label_) for entity in doc.ents]
    end_time = time.time()
    logger.info(f"Entity extraction completed in {end_time - start_time:.2f} seconds.")
    return entities


'''
# Grammar correction using LanguageTool API
def correct_grammar(text):
    url = "https://api.languagetool.org/v2/check"
    params = {
        'text': text,
        'language': 'en-US',
    }
    response = requests.post(url, data=params)
    matches = response.json().get('matches', [])
    corrected_text = text
    for match in reversed(matches):
        offset = match['offset']
        length = match['length']
        replacement = match['replacements'][0]['value']
        corrected_text = corrected_text[:offset] + replacement + corrected_text[offset + length:]
    return corrected_text
    '''


# Transcription function using Vosk
def transcribe_audio_vosk(audio_path, model_path='vosk-model-small-en-us-0.15'):
    model = Model(model_path)
    wf = wave.open(audio_path, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    transcript = ''
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = rec.Result()
            transcript += json.loads(result)['text'] + ' '
    final_result = rec.FinalResult()
    transcript += json.loads(final_result)['text']
    return transcript


# Extract text from PDF using PyMuPDF
def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


# Preprocess image for OCR
def preprocess_image_for_ocr(image):
    # Convert image to numpy array
    image_np = np.array(image)

    # Convert to grayscale
    gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # Use adaptive thresholding to handle different lighting conditions
    adaptive_thresh = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    # Perform morphological operations to remove noise and close gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    morph = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)

    # Invert the image (white text on black background)
    inverted = cv2.bitwise_not(morph)

    return Image.fromarray(inverted)



# Clean OCR text
def clean_ocr_text(text):
    text = re.sub(r'\n+', ' ', text)  # Replace newlines with spaces
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII characters
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    text = text.strip()  # Remove leading and trailing whitespace
    return text


# Extract text from image-based PDF using Tesseract
def extract_text_from_image_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", (pix.width, pix.height), bytes(pix.samples))  # Ensure the samples are in bytes
        preprocessed_img = preprocess_image_for_ocr(img)
        raw_text = pytesseract.image_to_string(preprocessed_img, config=r'--oem 3 --psm 6')
        cleaned_text = clean_ocr_text(raw_text)
        # corrected_text = correct_grammar(cleaned_text)
        corrected_text = cleaned_text
        text += corrected_text + "\n"
    return text


# Extract text from Word document
def extract_text_from_word(file_path):
    doc = Document(file_path)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text


# Extract audio from video
def extract_audio_from_video(video_path, audio_path):
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path)


# Transcribe audio using Google Cloud Speech-to-Text
def transcribe_audio(audio_path):
    client = speech.SpeechClient()
    with io.open(audio_path, 'rb') as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code='en-US'
    )

    response = client.recognize(config=config, audio=audio)
    transcript = ''
    for result in response.results:
        transcript += result.alternatives[0].transcript
    return transcript


# Analyze video frames using Google Cloud Vision
def analyze_video_frames(video_path):
    client = vision.ImageAnnotatorClient()
    video = VideoFileClip(video_path)
    frame_texts = []
    for frame in video.iter_frames():
        success, encoded_image = cv2.imencode('.jpg', frame)
        if not success:
            continue
        image = vision.Image(content=encoded_image.tobytes())
        response = client.text_detection(image=image)
        frame_text = ''
        for text in response.text_annotations:
            frame_text += text.description + ' '
        frame_texts.append(frame_text.strip())
    return ' '.join(frame_texts)


# Process video to extract text and transcriptions
def process_video(video_path):
    audio_path = f"{video_path}.wav"
    extract_audio_from_video(video_path, audio_path)
    transcript = transcribe_audio(audio_path)
    frame_text = analyze_video_frames(video_path)
    combined_text = transcript + ' ' + frame_text
    return combined_text


# Process material based on type
def process_material(material_type, file_path):
    if material_type == 'pdf':
        # Check if PDF is image-based
        text = extract_text_from_pdf(file_path)
        if not text.strip():  # If no text is found, assume it's an image-based PDF
            return extract_text_from_image_pdf(file_path)
        return text
    elif material_type == 'image_pdf':
        return extract_text_from_image_pdf(file_path)
    elif material_type == 'word':
        return extract_text_from_word(file_path)
    elif material_type == 'video':
        return process_video(file_path)
    elif material_type == 'audio':
        return transcribe_audio_vosk(file_path)
    else:
        raise ValueError("Unsupported material type")
