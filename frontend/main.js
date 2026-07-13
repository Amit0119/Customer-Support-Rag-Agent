document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');

    // Keep track of chat history for context
    let chatHistory = [];

    // Helper to escape HTML to prevent XSS (if needed, but marked.js handles some of it)
    const escapeHTML = (str) => {
        const p = document.createElement('p');
        p.textContent = str;
        return p.innerHTML;
    };

    // Render a message
    const renderMessage = (role, content, sources = []) => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        
        let htmlContent = '';
        if (role === 'bot') {
            // Render Markdown for bot messages
            htmlContent = marked.parse(content);
        } else {
            // Simple text for user
            htmlContent = `<p>${escapeHTML(content)}</p>`;
        }
        
        msgDiv.innerHTML = htmlContent;

        // Add sources if available
        if (sources && sources.length > 0) {
            const sourcesId = `sources-${Date.now()}`;
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'sources-container';
            
            const toggleBtn = document.createElement('button');
            toggleBtn.className = 'sources-toggle';
            toggleBtn.innerHTML = `📚 View Sources & Citations (▾)`;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'sources-content';
            contentDiv.id = sourcesId;
            
            sources.forEach((src, idx) => {
                const srcItem = document.createElement('div');
                srcItem.className = 'source-item';
                srcItem.innerHTML = `<strong>Source ${idx + 1}:</strong><br><small>${escapeHTML(src.content)}</small>`;
                contentDiv.appendChild(srcItem);
            });
            
            toggleBtn.onclick = () => {
                contentDiv.classList.toggle('show');
                if(contentDiv.classList.contains('show')){
                    toggleBtn.innerHTML = `📚 Hide Sources & Citations (▴)`;
                } else {
                    toggleBtn.innerHTML = `📚 View Sources & Citations (▾)`;
                }
            };
            
            sourcesDiv.appendChild(toggleBtn);
            sourcesDiv.appendChild(contentDiv);
            msgDiv.appendChild(sourcesDiv);
        }

        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    // Render loading indicator
    const renderTypingIndicator = () => {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message bot typing';
        msgDiv.id = 'typing-indicator';
        msgDiv.innerHTML = `
            <div class="typing-indicator">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        `;
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    const removeTypingIndicator = () => {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    };

    // Send Message to Backend
    const sendMessage = async () => {
        const text = userInput.value.trim();
        if (!text) return;

        // 1. Render User Message
        renderMessage('user', text);
        userInput.value = '';
        
        // 2. Render Loading
        renderTypingIndicator();

        try {
            // 3. Send Request
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_query: text,
                    chat_history: chatHistory
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Remove loading
            removeTypingIndicator();
            
            // 4. Render Bot Response
            renderMessage('bot', data.answer, data.sources);
            
            // 5. Update History
            chatHistory.push({ role: 'user', content: text });
            chatHistory.push({ role: 'assistant', content: data.answer });
            
        } catch (error) {
            console.error("Error communicating with API:", error);
            removeTypingIndicator();
            renderMessage('bot', "I'm having trouble connecting to the server. Please try again later.");
        }
    };

    // Initial Welcome Message
    renderMessage('bot', "Hello! I am the GigaCorp Support Agent. How can I assist you today? My 3D premium interface is ready to help.");
    chatHistory.push({ role: 'assistant', content: "Hello! I am the GigaCorp Support Agent. How can I assist you today? My 3D premium interface is ready to help." });

    // Event Listeners
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});
