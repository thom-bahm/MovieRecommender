// Thomas Bahmandeji, Jackson Sanger

function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value;

    if (message.trim() === '') {
        return;
    }

    const messagesDiv = document.getElementById('messages');
    const userMessageDiv = document.createElement('div');
    userMessageDiv.className = 'message user';
    userMessageDiv.textContent = message;
    messagesDiv.appendChild(userMessageDiv);
    messageInput.value = '';

    fetch('/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'message': message
        })
    })
    .then(response => response.json())
    .then(data => {
        const botMessageDiv = document.createElement('div');
        botMessageDiv.className = 'message bot';
        botMessageDiv.innerHTML = data.api_response;
        messagesDiv.appendChild(botMessageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    });
}
