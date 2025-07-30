// Chat interface JavaScript functionality

class ChatInterface {
    constructor() {
        this.ws = null;
        this.conversationId = this.generateConversationId();
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.messageQueue = [];
        
        // DOM elements
        this.elements = {
            chatMessages: document.getElementById('chatMessages'),
            messageInput: document.getElementById('messageInput'),
            sendButton: document.getElementById('sendButton'),
            chatForm: document.getElementById('chatForm'),
            connectionStatus: document.getElementById('connectionStatus'),
            typingIndicator: document.getElementById('typingIndicator'),
            clearChatBtn: document.getElementById('clearChatBtn'),
            charCounter: document.getElementById('charCounter'),
            chatSuggestions: document.getElementById('chatSuggestions'),
            connectionModal: document.getElementById('connectionModal'),
            toastContainer: document.getElementById('toastContainer'),
            welcomeTime: document.getElementById('welcomeTime')
        };
        
        this.init();
    }
    
    init() {
        console.log('🧠 Initializing Chat Interface...');
        
        // Set welcome time
        this.setWelcomeTime();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Connect WebSocket
        this.connectWebSocket();
        
        // Setup auto-resize for textarea
        this.setupTextareaResize();
        
        // Initialize suggestions
        this.setupSuggestions();
        
        console.log('✅ Chat Interface initialized');
    }
    
    setWelcomeTime() {
        if (this.elements.welcomeTime) {
            const now = new Date();
            const timeString = now.toLocaleTimeString('es-ES', {
                hour: '2-digit',
                minute: '2-digit'
            });
            this.elements.welcomeTime.textContent = timeString;
        }
    }
    
    generateConversationId() {
        return 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    setupEventListeners() {
        // Form submission
        this.elements.chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });
        
        // Input events
        this.elements.messageInput.addEventListener('input', () => {
            this.updateCharCounter();
            this.adjustTextareaHeight();
        });
        
        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Clear chat button
        this.elements.clearChatBtn.addEventListener('click', () => {
            this.clearChat();
        });
        
        // Window events
        window.addEventListener('beforeunload', () => {
            this.disconnect();
        });
        
        window.addEventListener('online', () => {
            this.showToast('Conexión restaurada', 'success');
            this.connectWebSocket();
        });
        
        window.addEventListener('offline', () => {
            this.showToast('Sin conexión a internet', 'warning');
        });
    }
    
    setupTextareaResize() {
        const textarea = this.elements.messageInput;
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    }
    
    adjustTextareaHeight() {
        const textarea = this.elements.messageInput;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
    
    updateCharCounter() {
        const length = this.elements.messageInput.value.length;
        const maxLength = this.elements.messageInput.maxLength;
        this.elements.charCounter.textContent = `${length}/${maxLength}`;
        
        // Update counter color based on length
        if (length > maxLength * 0.9) {
            this.elements.charCounter.style.color = 'var(--error-color)';
        } else if (length > maxLength * 0.7) {
            this.elements.charCounter.style.color = 'var(--warning-color)';
        } else {
            this.elements.charCounter.style.color = 'var(--text-muted)';
        }
    }
    
    setupSuggestions() {
        const suggestions = this.elements.chatSuggestions.querySelectorAll('.suggestion-chip');
        suggestions.forEach(suggestion => {
            suggestion.addEventListener('click', () => {
                const text = suggestion.textContent;
                this.elements.messageInput.value = text;
                this.elements.messageInput.focus();
                this.updateCharCounter();
                this.adjustTextareaHeight();
                
                // Hide suggestions after selection
                this.elements.chatSuggestions.style.display = 'none';
            });
        });
    }
    
    connectWebSocket() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            return;
        }
        
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/chat/${this.conversationId}`;
            
            console.log('🔌 Connecting to WebSocket:', wsUrl);
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('✅ WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('connected');
                this.hideConnectionModal();
                
                // Send queued messages
                this.sendQueuedMessages();
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleIncomingMessage(data);
            };
            
            this.ws.onclose = (event) => {
                console.log('🔌 WebSocket disconnected:', event.code, event.reason);
                this.isConnected = false;
                this.updateConnectionStatus('disconnected');
                
                if (!event.wasClean) {
                    this.attemptReconnect();
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                this.showToast('Error de conexión', 'error');
            };
            
        } catch (error) {
            console.error('❌ Failed to create WebSocket:', error);
            this.showToast('No se pudo conectar al servidor', 'error');
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            this.showToast('No se pudo reconectar al servidor', 'error');
            return;
        }
        
        this.reconnectAttempts++;
        this.showConnectionModal();
        
        setTimeout(() => {
            console.log(`🔄 Reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            this.connectWebSocket();
        }, this.reconnectDelay * this.reconnectAttempts);
    }
    
    sendMessage() {
        const message = this.elements.messageInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        this.addMessage('user', message);
        
        // Clear input
        this.elements.messageInput.value = '';
        this.updateCharCounter();
        this.adjustTextareaHeight();
        
        // Hide suggestions
        this.elements.chatSuggestions.style.display = 'none';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // Prepare message data
        const messageData = {
            type: 'chat_message',
            message: message,
            timestamp: new Date().toISOString(),
            conversation_id: this.conversationId
        };
        
        if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(messageData));
        } else {
            // Queue message for later
            this.messageQueue.push(messageData);
            this.showToast('Mensaje en cola, reconectando...', 'warning');
            this.connectWebSocket();
        }
    }
    
    sendQueuedMessages() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            if (this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify(message));
            }
        }
    }
    
    handleIncomingMessage(data) {
        console.log('📨 Received message:', data);
        console.log('📨 Message type:', data.type);
        console.log('📨 Message content:', data.content || data.message);
        
        this.hideTypingIndicator();
        
        if (data.type === 'ai_response') {
            this.addMessage('bot', data.content);
        } else if (data.type === 'chat_response') {
            this.addMessage('bot', data.message);
        } else if (data.type === 'error') {
            this.showToast(data.content || data.message || 'Error en el servidor', 'error');
        } else if (data.type === 'ai_typing') {
            // AI is typing, keep showing typing indicator
        } else {
            console.log('🤷 Unknown message type:', data.type, data);
        }
    }
    
    addMessage(sender, content, timestamp = null) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}-message`;
        
        const now = timestamp ? new Date(timestamp) : new Date();
        const timeString = now.toLocaleTimeString('es-ES', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const avatar = sender === 'bot' ? '🧠' : '👤';
        
        messageElement.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <p>${this.formatMessage(content)}</p>
                <span class="message-time">${timeString}</span>
            </div>
        `;
        
        this.elements.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
        
        // Remove welcome message if it exists
        const welcomeMessage = this.elements.chatMessages.querySelector('.welcome-message');
        if (welcomeMessage && sender === 'user') {
            welcomeMessage.remove();
        }
    }
    
    formatMessage(content) {
        // Basic message formatting
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }
    
    showTypingIndicator() {
        this.elements.typingIndicator.classList.add('show');
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.elements.typingIndicator.classList.remove('show');
    }
    
    scrollToBottom() {
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }
    
    updateConnectionStatus(status) {
        const statusElement = this.elements.connectionStatus;
        
        switch (status) {
            case 'connected':
                statusElement.textContent = '🟢 Conectado';
                statusElement.style.color = 'var(--success-color)';
                break;
            case 'connecting':
                statusElement.textContent = '🟡 Conectando...';
                statusElement.style.color = 'var(--warning-color)';
                break;
            case 'disconnected':
                statusElement.textContent = '🔴 Desconectado';
                statusElement.style.color = 'var(--error-color)';
                break;
        }
    }
    
    showConnectionModal() {
        this.elements.connectionModal.classList.add('show');
    }
    
    hideConnectionModal() {
        this.elements.connectionModal.classList.remove('show');
    }
    
    showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        this.elements.toastContainer.appendChild(toast);
        
        // Auto-remove toast
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, duration);
    }
    
    clearChat() {
        if (confirm('¿Estás seguro de que quieres limpiar la conversación?')) {
            // Clear messages
            this.elements.chatMessages.innerHTML = `
                <div class="welcome-message">
                    <div class="message bot-message">
                        <div class="message-avatar">🧠</div>
                        <div class="message-content">
                            <p>¡Hola! Soy tu asistente de IA sin tonterías. ¿En qué puedo ayudarte hoy?</p>
                            <span class="message-time" id="welcomeTime"></span>
                        </div>
                    </div>
                </div>
            `;
            
            // Reset welcome time
            this.setWelcomeTime();
            
            // Show suggestions again
            this.elements.chatSuggestions.style.display = 'flex';
            
            // Generate new conversation ID
            this.conversationId = this.generateConversationId();
            
            // Reconnect with new conversation ID
            this.disconnect();
            this.connectWebSocket();
            
            this.showToast('Conversación limpiada', 'success');
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close(1000, 'User disconnected');
            this.ws = null;
        }
        this.isConnected = false;
    }
}

// Initialize chat interface when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.chatInterface = new ChatInterface();
});

// Handle page visibility for connection management
document.addEventListener('visibilitychange', function() {
    if (window.chatInterface) {
        if (document.hidden) {
            // Page is hidden, consider pausing some operations
            console.log('🔇 Page hidden, reducing activity');
        } else {
            // Page is visible again
            console.log('👁️ Page visible, resuming normal activity');
            if (!window.chatInterface.isConnected) {
                window.chatInterface.connectWebSocket();
            }
        }
    }
});

// Utility functions for enhanced UX
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        if (window.chatInterface) {
            window.chatInterface.showToast('Copiado al portapapeles', 'success');
        }
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}

// Add copy functionality to code blocks (if any)
document.addEventListener('click', function(e) {
    if (e.target.tagName === 'CODE') {
        copyToClipboard(e.target.textContent);
    }
});

// Performance monitoring for chat
if ('performance' in window) {
    window.addEventListener('load', function() {
        setTimeout(() => {
            const perfData = performance.getEntriesByType('navigation')[0];
            if (perfData) {
                console.log(`🚀 Chat page load time: ${Math.round(perfData.loadEventEnd)}ms`);
            }
        }, 0);
    });
}