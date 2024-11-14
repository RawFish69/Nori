document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('chatHistory').innerHTML = '';
    let savedHistory = JSON.parse(localStorage.getItem('chatHistory')) || [];
    const uniqueHistory = Array.from(new Set(savedHistory.map(JSON.stringify))).map(JSON.parse);
    localStorage.setItem('chatHistory', JSON.stringify(uniqueHistory));

    uniqueHistory.forEach(({ sender, message }) => {
        addMessageToChatHistory(sender, message, false);
    });

    document.getElementById('inputForm').addEventListener('submit', async function(event) {
        event.preventDefault();
        const userInput = document.getElementById('userInput').value.trim();
        if (userInput) {
            addMessageToChatHistory('User', userInput, true);
            document.getElementById('userInput').value = '';
            try {
                const response = await fetch('https://nori.fish/api/chat', { 
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ user_input: userInput })
                });
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                const data = await response.json();
                const botMessage = data.output.trim();
                addMessageToChatHistory('Nori', botMessage, true);
            } catch (error) {
                console.error('There has been a problem with fetch operation:', error);
                addMessageToChatHistory('Error', error.message, true);
            }
        }
    });

    document.getElementById('userInput').addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault(); 
            document.getElementById('sendButton').click(); 
        }
    });

    document.getElementById('clearHistory').addEventListener('click', function() {
        if (confirm('Are you sure you want to clear chat history?')) {
            localStorage.removeItem('chatHistory');
            document.getElementById('chatHistory').innerHTML = '';
        }
    });

    function addMessageToChatHistory(sender, message, saveToLocalStorage = true) {
        const chatHistory = document.getElementById('chatHistory');
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message');
        let formattedMessage = marked.parse(message.trim()).replace(/^<p>|<\/p>$/g, '');
        messageDiv.innerHTML = `<strong>${sender}:</strong> ${formattedMessage}`;
        if (!Array.from(chatHistory.children).some(child => child.innerHTML === messageDiv.innerHTML)) {
            chatHistory.appendChild(messageDiv);
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
        if (saveToLocalStorage) {
            savedHistory.push({ sender, message });
            const uniqueSavedHistory = Array.from(new Set(savedHistory.map(JSON.stringify))).map(JSON.parse);
            localStorage.setItem('chatHistory', JSON.stringify(uniqueSavedHistory));
        }
    }
});
