console.log("Chat.js loaded");

document.addEventListener('DOMContentLoaded', () => {
    const chatSessionIdElement = document.getElementById('chatSessionId');
    const chatSessionId = chatSessionIdElement ? chatSessionIdElement.value : null;
    const chatMessages = document.querySelector('.chat-messages');

    if (!chatSessionId) {
        console.error('chatSessionId is not defined');
        return;
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;

    console.log("Connecting to WebSocket with chatSessionId:", chatSessionId);

    const chatSocket = new WebSocket(
        'ws://' + window.location.host + '/ws/chat/' + chatSessionId + '/'
    );

    chatSocket.onopen = function(e) {
        console.log("WebSocket connection established.");
    };

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        const message = data.message;
        const messageType = data.message_type;
        const isAi = data.is_ai;

        console.log("Received message from WebSocket:", data);

        if (messageType === 'text') {
            appendMessage(isAi ? 'received-chats' : 'outgoing-chats', message, isAi);
        } else if (messageType === 'voice') {
            appendVoiceMessage(isAi ? 'received-chats' : 'outgoing-chats', message, isAi);
        }

        // Scroll to the bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    chatSocket.onclose = function(e) {
        console.log("WebSocket connection closed.");
    };

    chatSocket.onerror = function(e) {
        console.error("WebSocket error observed:", e);
    };

    function sendMessage() {
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value;
        if (message.trim() !== '') {
            appendMessage('outgoing-chats', message, false); // Display the sent message immediately
            console.log("Sending message:", message);
            chatSocket.send(JSON.stringify({
                'message': message,
                'type': 'text'
            }));
            messageInput.value = '';
        }
    }

    document.getElementById('send-button').addEventListener('click', function() {
        sendMessage();
    });

    document.getElementById('message-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });

    let mediaRecorder;
    let audioChunks = [];
    let recordingInterval;
    let isRecording = false;

    const activateVoiceChatButton = document.getElementById('activate_voice_chat');
    activateVoiceChatButton.addEventListener('click', function() {
        if (isRecording) {
            mediaRecorder.stop();
            clearInterval(recordingInterval);
            isRecording = false;
            activateVoiceChatButton.style.color = 'white'; // Change color back to white
            console.log('Voice chat deactivated');
        } else {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    mediaRecorder = new MediaRecorder(stream);

                    mediaRecorder.ondataavailable = event => {
                        audioChunks.push(event.data);
                    };

                    mediaRecorder.onstop = () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/mp3' });
                        audioChunks = [];

                        const reader = new FileReader();
                        reader.onloadend = () => {
                            const base64String = reader.result.split(',')[1];

                            appendVoiceMessage('outgoing-chats', base64String, false); // Display the sent voice message immediately
                            console.log("Sending voice message:", base64String);
                            chatSocket.send(JSON.stringify({
                                'message': base64String,
                                'type': 'voice'
                            }));
                        };
                        reader.readAsDataURL(audioBlob);
                    };

                    mediaRecorder.start();
                    isRecording = true;
                    activateVoiceChatButton.style.color = 'red'; // Change color to red
                    console.log('Voice chat activated');

                    recordingInterval = setInterval(() => {
                        if (mediaRecorder.state === 'recording') {
                            mediaRecorder.stop();
                        }
                    }, 5000); // Set the interval duration as needed
                })
                .catch(error => {
                    console.error('Error accessing user media:', error);
                });
        }
    });

    function appendMessage(chatType, message, isAi) {
        const userMessageDiv = document.createElement('div');
        userMessageDiv.classList.add(chatType);
        userMessageDiv.innerHTML = `
            <div class="outgoing-msg">
                <div class="${isAi ? 'received-msg-inbox' : 'outgoing-chats-msg'}">
                    <p>${message}</p>
                    <span class="time" data-timestamp="${Date.now()}">Now</span>
                </div>
            </div>
        `;
        chatMessages.appendChild(userMessageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function appendVoiceMessage(chatType, base64Audio, isAi) {
        const userVoiceDiv = document.createElement('div');
        userVoiceDiv.classList.add(chatType);
        const audioElement = document.createElement('audio');
        audioElement.controls = true;
        audioElement.src = `data:audio/mp3;base64,${base64Audio}`;

        const audioSource = document.createElement('source');
        audioSource.src = `data:audio/mp3;base64,${base64Audio}`;
        audioSource.type = 'audio/mp3';
        audioElement.appendChild(audioSource);

        const timeElement = document.createElement('span');
        timeElement.classList.add('time');
        timeElement.setAttribute('data-timestamp', Date.now().toString());
        timeElement.textContent = 'Now';

        const messageContainer = document.createElement('div');
        messageContainer.classList.add(isAi ? 'received-msg-inbox' : 'outgoing-chats-msg');
        messageContainer.appendChild(audioElement);
        messageContainer.appendChild(timeElement);

        const msgContainer = document.createElement('div');
        msgContainer.classList.add('outgoing-msg');
        msgContainer.appendChild(messageContainer);

        userVoiceDiv.appendChild(msgContainer);
        chatMessages.appendChild(userVoiceDiv);

        // Automatically play the audio after appending to DOM
        audioElement.addEventListener('loadedmetadata', () => {
            audioElement.play();
        });

        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    setInterval(updateTimestamps, 60000); // Update timestamps every minute

    function updateTimestamps() {
        const timeElements = document.querySelectorAll('.time');
        timeElements.forEach(element => {
            const timestamp = parseInt(element.getAttribute('data-timestamp'));
            const now = Date.now();
            const diff = Math.floor((now - timestamp) / 60000); // Difference in minutes

            if (diff >= 1) {
                const date = new Date(timestamp);
                const hours = date.getHours();
                const minutes = date.getMinutes();
                const formattedTime = `${hours}:${minutes < 10 ? '0' : ''}${minutes}`;
                const formattedDate = `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear()}`;
                element.textContent = `${formattedTime} | ${formattedDate}`;
            }
        });
    }
});
