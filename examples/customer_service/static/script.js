document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const chatMessages = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const passengerName = document.getElementById('passenger-name');
    const confirmationNumber = document.getElementById('confirmation-number');
    const flightNumber = document.getElementById('flight-number');
    const seatNumber = document.getElementById('seat-number');
    const currentAgent = document.getElementById('current-agent');
    
    // Conversation state
    let conversationId = null;
    let eventSource = null;
    
    // Initialize conversation
    initializeConversation();
    
    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Initialize conversation
    async function initializeConversation() {
        try {
            const response = await fetch('/conversation', {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error('Failed to start conversation');
            }
            
            const data = await response.json();
            conversationId = data.conversation_id;
            
            // Connect to SSE for updates
            connectToEventSource(conversationId);
            
        } catch (error) {
            console.error('Error starting conversation:', error);
            addSystemMessage('Error starting conversation. Please try again later.');
        }
    }
    
    // Connect to event source for updates
    function connectToEventSource(conversationId) {
        console.log('Connecting to event source for conversation:', conversationId);
        
        // Close existing connection if any
        if (eventSource) {
            console.log('Closing existing event source');
            eventSource.close();
        }
        
        // Connect to SSE endpoint
        const sseUrl = `/conversation/${conversationId}/stream`;
        console.log('SSE URL:', sseUrl);
        eventSource = new EventSource(sseUrl);
        
        eventSource.onopen = function() {
            console.log('SSE connection opened');
        };
        
        eventSource.onmessage = function(event) {
            console.log('SSE message received:', event.data);
            try {
                const data = JSON.parse(event.data);
                
                if (data.error) {
                    console.error('SSE error:', data.error);
                    addSystemMessage('Error: ' + data.error);
                    return;
                }
                
                // Add message to chat
                addMessageToChat(data);
            } catch (error) {
                console.error('Error parsing SSE message:', error, event.data);
            }
        };
        
        eventSource.onerror = function(error) {
            console.error('EventSource failed:', error);
            eventSource.close();
            addSystemMessage('Connection lost. Trying to reconnect...');
            
            // Try to reconnect after a delay
            setTimeout(() => {
                console.log('Reconnecting to event source...');
                connectToEventSource(conversationId);
            }, 3000);
        };
    }
    
    // Send message
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;
        
        // If conversation is not initialized yet, show an error
        if (!conversationId) {
            addSystemMessage('Conversation is still initializing. Please try again in a moment.');
            return;
        }
        
        // Add user message to chat immediately
        const userMessageElement = document.createElement('div');
        userMessageElement.className = 'message user';
        userMessageElement.innerHTML = `<div class="message-content"><p>${message}</p></div>`;
        chatMessages.appendChild(userMessageElement);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Clear input
        messageInput.value = '';
        
        // Add loading indicator
        const loadingElement = document.createElement('div');
        loadingElement.className = 'message system loading';
        loadingElement.innerHTML = `<div class="message-content"><p>Processing your message...</p></div>`;
        chatMessages.appendChild(loadingElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        try {
            const response = await fetch(`/conversation/${conversationId}/message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });
            
            // Remove loading indicator
            if (loadingElement.parentNode) {
                loadingElement.parentNode.removeChild(loadingElement);
            }
            
            if (!response.ok) {
                throw new Error('Failed to send message');
            }
            
            // Get conversation context
            fetchConversationContext();
            
        } catch (error) {
            console.error('Error sending message:', error);
            
            // Remove loading indicator
            if (loadingElement.parentNode) {
                loadingElement.parentNode.removeChild(loadingElement);
            }
            
            addSystemMessage('Error sending message. Please try again.');
        }
    }
    
    // Fetch conversation context
    async function fetchConversationContext() {
        try {
            const response = await fetch(`/conversation/${conversationId}`);
            
            if (!response.ok) {
                throw new Error('Failed to fetch conversation context');
            }
            
            const data = await response.json();
            updateContextPanel(data.context);
            
        } catch (error) {
            console.error('Error fetching conversation context:', error);
        }
    }
    
    // Update context panel
    function updateContextPanel(context) {
        passengerName.textContent = context.passenger_name || 'Not set';
        confirmationNumber.textContent = context.confirmation_number || 'Not set';
        flightNumber.textContent = context.flight_number || 'Not set';
        seatNumber.textContent = context.seat_number || 'Not set';
    }
    
    // Add message to chat
    function addMessageToChat(message) {
        console.log('Adding message to chat:', message);
        
        // Check if message has an ID
        if (!message.id) {
            console.error('Message has no ID:', message);
            // Generate a random ID for the message
            message.id = Math.random().toString(36).substring(2, 15);
            console.log('Generated ID for message:', message.id);
        }
        
        // Skip if message already exists (for reconnections)
        if (document.querySelector(`[data-message-id="${message.id}"]`)) {
            console.log('Message already exists, skipping:', message.id);
            return;
        }
        
        // Skip user messages from SSE since we already add them when sending
        if (message.role === 'user') {
            console.log('Skipping user message from SSE');
            return;
        }
        
        // Handle handoff messages - update agent but don't show the message
        if (message.role === 'system' && message.type === 'handoff') {
            console.log('Processing handoff message');
            // Extract the target agent name from the handoff message
            const handoffMatch = message.content.match(/to (.+)$/);
            if (handoffMatch && handoffMatch[1]) {
                const targetAgent = handoffMatch[1];
                console.log('Handoff to agent:', targetAgent);
                
                // Update current agent display with highlight
                currentAgent.textContent = targetAgent;
                
                // Add highlight animation
                currentAgent.classList.remove('highlight');
                void currentAgent.offsetWidth; // Trigger reflow to restart animation
                currentAgent.classList.add('highlight');
            }
            return;
        }
        
        // Skip other system messages
        if (message.role === 'system') {
            console.log('Skipping system message:', message.type);
            return;
        }
        
        console.log('Creating message element for:', message.role, message.content);
        
        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.role}`;
        if (message.type) {
            messageElement.classList.add(message.type);
        }
        messageElement.setAttribute('data-message-id', message.id);
        
        let messageContent = '';
        
        // Add agent name for assistant messages
        if (message.role === 'assistant' && message.agent_name) {
            messageContent += `<div class="message-header">${message.agent_name}</div>`;
            
            // Update current agent display with highlight
            const previousAgent = currentAgent.textContent;
            if (previousAgent !== message.agent_name) {
                currentAgent.textContent = message.agent_name;
                
                // Add highlight animation
                currentAgent.classList.remove('highlight');
                void currentAgent.offsetWidth; // Trigger reflow to restart animation
                currentAgent.classList.add('highlight');
            }
        }
        
        messageContent += `<div class="message-content"><p>${message.content}</p></div>`;
        messageElement.innerHTML = messageContent;
        
        chatMessages.appendChild(messageElement);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Add system message
    function addSystemMessage(content) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message system';
        messageElement.innerHTML = `<div class="message-content"><p>${content}</p></div>`;
        
        chatMessages.appendChild(messageElement);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
