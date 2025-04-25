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
    }

    // Display message to chat window
    function displayMessageOnFrontend(data) {
        const messageBox = document.querySelector('.message-box');
        const messageDiv = document.createElement('div');

        // Determine if the message is from the current user
        const isCurrentUser = data.username === username;
        if (isCurrentUser) {
            messageDiv.classList.add('flex-row-reverse');
        }
        messageDiv.classList.add('d-flex', 'mb-3');

        let messageContent = '';

        // Message HTML template
        if (data.message_type === 'image' && data.file_url) {
            messageContent = `<img src="${data.file_url}" class="img-fluid rounded my-2" alt="${data.filename}" width="300" height="300">`;
        } else if (data.message_type === 'file' && data.file_url) {
            messageContent = `<a href="${data.file_url}" download><i class="bi bi-file-earmark-arrow-down-fill h1 text-warning"></i> ${data.filename}</a>`;
        } else {
            messageContent = `<p>${data.message}</p>`;
        }

        messageDiv.innerHTML = `
            <img src="${data.picture}" class="rounded-circle" alt="${data.username}" width="40" height="40">
            <div class="${isCurrentUser ? 'bg-success me-2' : 'bg-dark ms-2'} d-flex flex-column align-items-start text-white rounded p-2">
                <strong>${isCurrentUser ? 'You' : data.username}</strong>
                ${messageContent}
                <small style="lavender">${data.timestamp ? new Date(data.timestamp).toLocaleString() : new Date().toLocaleString()}</small>
            </div>
        `;

        messageBox.appendChild(messageDiv);

        // Scroll to bottom of messages
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Activate Submit event
    chatForm.addEventListener('submit', sendMessageToBackend);
    chatMessageSubmit.addEventListener('click', sendMessageToBackend);

    // Add a change event listener to both image and file upload inputs to preview the selected file
    [imageUpload, fileUpload].forEach(input => {
        input.addEventListener('change', function () {
            if (this.files.length > 0) {
                const fileType = this.id === 'image-upload' ? 'Image' : 'File';
                chatMessageInput.value = `Uploading: ${this.files[0].name} (${fileType})`;
            }
        });
    });
});