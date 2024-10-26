import os
import re
import time

import fitz
import pytesseract
import numpy as np
import ffmpeg
import cv2
import spacy
import requests
from PIL import Image
from docx import Document
from moviepy.editor import VideoFileClip
from transformers import pipeline
import azure.cognitiveservices.speech as speechsdk

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load models globally
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
nlp = spacy.load("en_core_web_sm")

MAX_TOKEN_LENGTH = 512


def chunk_text_by_token_length(text, max_length=512):
    words = text.split()
    current_chunk = []
    current_length = 0

    for word in words:
        word_length = len(word)
        # Check if adding the next word would exceed the max_length
        if current_length + word_length + 1 <= max_length or not current_chunk:
            current_chunk.append(word)
            current_length += word_length + 1
        else:
            # If the next word causes the chunk to exceed max_length, yield the current chunk
            yield " ".join(current_chunk)
            current_chunk = [word]
            current_length = word_length + 1

    # Yield any remaining words as the final chunk
    if current_chunk:
        yield " ".join(current_chunk)


def summarize_text(text):
    # Chunk the text
    chunks = list(chunk_text_by_token_length(text, max_length=512))

    summaries = []
    temp_chunk = ""

    for chunk in chunks:
        # Accumulate smaller chunks until reaching the max length
        if len(temp_chunk) + len(chunk) <= 512:
            temp_chunk += " " + chunk
        else:
            if temp_chunk:
                summary = summarizer(temp_chunk.strip(), max_length=150, min_length=30, do_sample=False)
                summaries.append(summary[0]['summary_text'])
            temp_chunk = chunk  # Start a new temp_chunk

    # Summarize any remaining text in temp_chunk
    if temp_chunk:
        summary = summarizer(temp_chunk.strip(), max_length=150, min_length=30, do_sample=False)
        summaries.append(summary[0]['summary_text'])

    # Combine summaries into a single output
    combined_summary = " ".join(summaries)

    return combined_summary


def extract_entities(text):
    doc = nlp(text)
    entities = [(entity.text, entity.label_) for entity in doc.ents]
    return entities


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


def convert_audio_to_wav(input_path, output_path):
    try:
        print(f"Converting '{input_path}' to '{output_path}'...")
        # Specify the path to ffmpeg executable
        ffmpeg_executable = r"C:\ffmpeg\bin\ffmpeg.exe"  # Update with your actual path

        (
            ffmpeg
            .input(input_path)
            .output(output_path, format='wav', acodec='pcm_s16le', ac=1, ar='16000')
            .overwrite_output()
            .run(cmd=ffmpeg_executable)
        )
        print("Conversion successful.")
    except ffmpeg.Error as e:
        print(f"Error converting audio file: {e.stderr.decode()}")
        raise e
    except Exception as e:
        print(f"An unexpected error occurred during audio conversion: {e}")
        raise e


def transcribe_audio(audio_path):
    if not os.path.exists(audio_path):
        return ""

    speech_key = "ae01fc5132af49cbb9e9c3549d04e865"
    service_region = "southafricanorth"

    if not speech_key or not service_region:
        return ""

    try:
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        audio_config = speechsdk.audio.AudioConfig(filename=audio_path)
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        result = recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return ""
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            return ""
    except Exception as e:
        return ""


def process_audio_file(input_audio_path):
    if not os.path.exists(input_audio_path):
        return ""

    # Define the path for the converted WAV file
    converted_audio_path = os.path.splitext(input_audio_path)[0] + "_converted.wav"

    # Convert the audio file to WAV format with required specifications
    convert_audio_to_wav(input_audio_path, converted_audio_path)

    # Check if the converted file was created
    if not os.path.exists(converted_audio_path):
        return ""

    # Transcribe the converted audio file
    transcription = transcribe_audio(converted_audio_path)

    # Delete the converted audio file if it's no longer needed
    os.remove(converted_audio_path)

    return transcription


# Analyze video frames using Azure Computer Vision
def analyze_video_frames(video_path):
    # Replace with your Azure Computer Vision subscription key and endpoint
    subscription_key = "ba7c3b8fda124933969b52f1781e25ff"
    endpoint = "https://socratecomputervision.cognitiveservices.azure.com/"

    ocr_url = endpoint + "/vision/v3.2/read/analyze"

    video = VideoFileClip(video_path)
    frame_texts = []

    # Adjust the frame processing interval to reduce the number of requests
    frame_interval = 10  # Process one frame every 30 seconds
    frame_times = range(0, int(video.duration), frame_interval)

    for t in frame_times:
        frame = video.get_frame(t)
        success, encoded_image = cv2.imencode('.jpg', frame)
        if not success:
            continue

        image_bytes = encoded_image.tobytes()

        headers = {
            'Ocp-Apim-Subscription-Key': subscription_key,
            'Content-Type': 'application/octet-stream'
        }

        # Implement retry logic with exponential backoff
        max_retries = 5
        retry_delay = 1  # Start with a 1-second delay

        for attempt in range(max_retries):
            try:
                response = requests.post(ocr_url, headers=headers, data=image_bytes)
                response.raise_for_status()
                break  # Exit the retry loop if the request was successful
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:
                    print(f"Received 429 Too Many Requests. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"HTTP error occurred: {e}")
                    return ''
            except Exception as e:
                print(f"An error occurred: {e}")
                return ''

        else:
            print("Max retries exceeded. Skipping this frame.")
            continue  # Skip to the next frame after max retries

        operation_url = response.headers["Operation-Location"]

        # Poll for the result
        while True:
            result_response = requests.get(operation_url, headers={'Ocp-Apim-Subscription-Key': subscription_key})
            result = result_response.json()
            if 'analyzeResult' in result or ('status' in result and result['status'] == 'failed'):
                break
            time.sleep(1)

        # Extract text if succeeded
        if result.get('status') == 'succeeded' and 'analyzeResult' in result:
            frame_text = ''
            for read_result in result['analyzeResult']['readResults']:
                for line in read_result['lines']:
                    frame_text += line['text'] + ' '
            frame_texts.append(frame_text.strip())

    return ' '.join(frame_texts)


# Extract audio from video and process it
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
        return process_audio_file(file_path)  # Assuming `transcribe_audio` can handle generic audio
    else:
        raise ValueError("Unsupported material type")
