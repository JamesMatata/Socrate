
# Socrate: AI-Powered Study Partner

## Overview
Socrate is an AI-powered web application designed to help students engage with their study materials interactively. Users can upload documents, videos, and audio files and communicate with an AI that can summarize content, extract key entities, and hold live discussions based on the uploaded material.

## Features
- **Upload Materials**: Supports PDFs, Word documents, videos, and audio files.
- **AI-Powered Chat**: Engage in live discussions with an AI based on the uploaded material.
- **Text and Voice Interaction**: Communicate with the AI through both text and voice messages.
- **Material Management**: View, manage, and delete uploaded materials easily.

## Tools and Technologies Used

### Backend and Core Functionality
- **Django**: Web framework used to build the application.
- **Django Channels**: Enables real-time communication via WebSockets for live chat functionality.
- **OpenAI API**: Powers the AI chat functionality, providing responses based on content summaries and extracted entities.

### File Processing and Analysis
- **PyMuPDF (fitz)**: Extracts text from PDF documents.
- **MoviePy**: Handles video processing, including frame extraction and audio handling.
- **Spacy**: Performs entity extraction from text, enabling better context and interaction with uploaded content.
- **Tesseract OCR (pytesseract)**: Recognizes text in image-based PDFs.

### Speech and Language Processing
- **Azure Cognitive Services Speech SDK**: Provides text-to-speech and speech-to-text conversion, enhancing voice interaction features.
- **Transformers (Hugging Face)**: Summarizes long text content, leveraging models like `distilbart-cnn-12-6`.

### Image and Video Processing
- **OpenCV**: Preprocesses images for OCR tasks.
- **FFmpeg**: Converts audio and video files to required formats for consistent processing.
- **Pillow**: Handles image manipulation and conversion for OCR preprocessing.

### Miscellaneous
- **Requests**: Manages API calls to external services, such as Azure's Computer Vision API.
- **gTTS (Google Text-to-Speech)**: Converts AI responses into audio, enhancing the voice interaction experience.

## Installation and Setup

1. **Clone the repository**:
    ```bash
    git clone https://github.com/JamesMatata/socrate
    cd socrate
    ```

2. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Environment Setup**:
   - **Azure Cognitive Services**: Add your Azure Speech SDK keys and endpoint.
   - **OpenAI API Key**: Add your OpenAI API key.
   - **Google Cloud API**: Add relevant Google Cloud API keys for speech-to-text and vision processing.

4. **Run the application**:
    ```bash
    python manage.py runserver
    ```

## Usage
1. **Upload Materials**: Choose a document, video, or audio file, and upload it to start interacting with Socrate.
2. **Engage in AI Chat**: Use text or voice to communicate with the AI, which responds based on your uploaded material.
3. **Manage Materials**: View a list of uploaded materials, and delete any that are no longer needed.

## Contribution
Contributions are welcome! Please submit a pull request with your proposed changes and ensure they follow the established code style and standards.
