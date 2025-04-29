document.addEventListener('DOMContentLoaded', () => {
    const roomSlug = JSON.parse(document.getElementById('json-roomname').textContent);
    const username = JSON.parse(document.getElementById('json-username').textContent);

    // Form and input elements
    const chatForm = document.getElementById('chat-form');
    const chatMessageInput = document.getElementById('chat-message-input');
    const chatMessageSubmit = document.getElementById('chat-message-submit');
    const chatMessages = document.getElementById('chat-messages');
    const imageUpload = document.getElementById('image-upload');
    const fileUpload = document.getElementById('file-upload');
    const translationToggle = document.getElementById('translation-toggle');

    // Set translation preference from localStorage
    if (localStorage.getItem('auto_translate') === 'false') {
        translationToggle.checked = false;
    }
    
    // Store translation preference when changed
    translationToggle.addEventListener('change', function() {
        localStorage.setItem('auto_translate', this.checked);
    });

    // WebSocket connection setup
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const chatSocket = new WebSocket(
        protocol + window.location.host + '/ws/' + roomSlug + '/'
    );

    // WebSocket event handlers
    chatSocket.onopen = function (e) {
        console.log('WebSocket connection established');
    };

    chatSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        // Handle incoming messages
        displayMessageOnFrontend(data);
    };

    chatSocket.onclose = function (e) {
        console.error('Chat socket closed unexpectedly');
    };

    // Send message function
    function sendMessageToBackend(e) {
        e.preventDefault(); // Prevent default form submission

        // Check if there's a message or file
        const message = chatMessageInput.value.trim();
        const image = imageUpload.files[0];
        const file = fileUpload.files[0];

        // Validation
        if (!message && !image && !file) {
            alert('Please enter a message or select a file');
            return;
        }

        // Determine message type
        let messageType = 'text';
        let fileToSend = null;
        let filename = null;

        if (image || file) {
            if (image) {
                messageType = 'image';
                fileToSend = image;
                filename = image.name;
            } else {
                messageType = 'file';
                fileToSend = file;
                filename = file.name;
            }

            const reader = new FileReader();

            reader.onload = function (event) {
                const fileData = event.target.result;
                const maxSize = 5000000;

                if (fileData.length > maxSize) {
                    console.warn(`File is very large (${(fileData.length / 1000000).toFixed(2)}MB) and may cause issues with WebSocket`);
                }

                const messageData = {
                    'message': message,
                    'username': username,
                    'roomslug': roomSlug,
                    'message_type': messageType,
                    'has_file': true,
                    'file': fileData,
                    'filename': filename,
                };
                chatSocket.send(JSON.stringify(messageData));
            };
            reader.readAsDataURL(fileToSend);

        } else {
            // Prepare message data
            const messageData = {
                'message': message,
                'username': username,
                'roomslug': roomSlug,
                'message_type': messageType,
            };

            // Send message via WebSocket
            chatSocket.send(JSON.stringify(messageData));
        }

        // Reset form
        chatMessageInput.value = '';
        imageUpload.value = '';
        fileUpload.value = '';
        
        // Hide file preview if shown
        const filePreviewContainer = document.getElementById('file-preview-container');
        if (filePreviewContainer) {
            filePreviewContainer.classList.add('d-none');
        }
    }

    // Display message to chat window with translation support
    function displayMessageOnFrontend(data) {
        const messageBox = document.querySelector('.message-box');
        const messageDiv = document.createElement('div');
        
        // Determine message direction
        messageDiv.classList.add('message');
        if (data.username === username) {
            messageDiv.classList.add('sent');
        } else {
            messageDiv.classList.add('received');
        }
        
        // Create message avatar
        const avatarDiv = document.createElement('div');
        avatarDiv.classList.add('message-avatar');
        const avatarImg = document.createElement('img');
        avatarImg.src = data.picture;
        avatarImg.alt = data.username;
        avatarDiv.appendChild(avatarImg);
        messageDiv.appendChild(avatarDiv);
        
        // Create message content container
        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');
        
        // Create message info
        const infoDiv = document.createElement('div');
        infoDiv.classList.add('message-info');
        
        const usernameDiv = document.createElement('div');
        usernameDiv.classList.add('message-username');
        usernameDiv.textContent = data.username;
        infoDiv.appendChild(usernameDiv);
        
        const timeDiv = document.createElement('div');
        timeDiv.classList.add('message-time');
        const now = new Date();
        timeDiv.textContent = now.getHours() + ':' + (now.getMinutes() < 10 ? '0' : '') + now.getMinutes();
        infoDiv.appendChild(timeDiv);
        
        contentDiv.appendChild(infoDiv);

        // Handle different message types
        if (data.message_type === 'text') {
            const textDiv = document.createElement('div');
            textDiv.classList.add('message-text');
            
            // Show translated or original based on user preference
            const shouldTranslate = translationToggle.checked;
            textDiv.textContent = data.message;
            
            // If message is translated and auto-translate is enabled
            if (data.translated && shouldTranslate) {
                // Add translation indicator
                const translatedSpan = document.createElement('span');
                translatedSpan.classList.add('message-translated-indicator');
                translatedSpan.textContent = 'Translated';
                translatedSpan.onclick = function() { toggleOriginal(this); };
                textDiv.appendChild(translatedSpan);
                
                // Add original message in hidden div
                const originalDiv = document.createElement('div');
                originalDiv.classList.add('original-message');
                originalDiv.textContent = `Original: ${data.original_message}`;
                textDiv.appendChild(originalDiv);
            }
            
            contentDiv.appendChild(textDiv);
        } else if (data.message_type === 'image') {
            const imageDiv = document.createElement('div');
            imageDiv.classList.add('message-image');
            const img = document.createElement('img');
            img.src = data.file_url;
            img.alt = 'Image';
            imageDiv.appendChild(img);
            contentDiv.appendChild(imageDiv);
        } else if (data.message_type === 'file') {
            const fileDiv = document.createElement('div');
            fileDiv.classList.add('message-file');
            const fileLink = document.createElement('a');
            fileLink.href = data.file_url;
            fileLink.download = data.filename || getFilenameFromUrl(data.file_url);
            
            const fileIcon = document.createElement('i');
            fileIcon.classList.add('bi', 'bi-file-earmark');
            fileLink.appendChild(fileIcon);
            
            const fileName = document.createTextNode(' ' + (data.filename || getFilenameFromUrl(data.file_url)));
            fileLink.appendChild(fileName);
            
            fileDiv.appendChild(fileLink);
            contentDiv.appendChild(fileDiv);
        }
        
        messageDiv.appendChild(contentDiv);
        
        // Add the new message to the chat
        messageBox.appendChild(messageDiv);
        
        // Scroll to bottom of messages
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Helper function to toggle original message display
    window.toggleOriginal = function(element) {
        const originalMessage = element.nextElementSibling;
        if (originalMessage.style.display === 'block') {
            originalMessage.style.display = 'none';
            element.textContent = 'Translated';
        } else {
            originalMessage.style.display = 'block';
            element.textContent = 'Hide Original';
        }
    };

    // Helper function to extract filename from URL
    function getFilenameFromUrl(url) {
        if (!url) return "File";
        return url.split('/').pop();
    }

    function handleTranslationStatus(element, success) {
        const indicator = element.querySelector('.message-translated-indicator');
        
        if (indicator) {
            if (!success) {
                indicator.textContent = 'Translation unavailable';
                indicator.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
                indicator.style.color = '#ef4444';
                indicator.style.cursor = 'default';
                indicator.onclick = null;
            }
        }
    }

    // Activate Submit event
    chatForm.addEventListener('submit', sendMessageToBackend);
    chatMessageSubmit.addEventListener('click', sendMessageToBackend);

    // Add a change event listener to both image and file upload inputs to preview the selected file
    [imageUpload, fileUpload].forEach(input => {
        if (!input) return;
        
        input.addEventListener('change', function () {
            if (this.files.length > 0) {
                const fileType = this.id === 'image-upload' ? 'Image' : 'File';
                
                if (this.id === 'image-upload') {
                    // Show image preview
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const imagePreview = document.getElementById('image-preview');
                        if (imagePreview) {
                            imagePreview.src = e.target.result;
                            document.getElementById('file-preview-container').classList.remove('d-none');
                        }
                    }
                    reader.readAsDataURL(this.files[0]);
                } else {
                    // Just show the filename for non-image files
                    chatMessageInput.value = `${this.files[0].name}`;
                }
            }
        });
    });
});