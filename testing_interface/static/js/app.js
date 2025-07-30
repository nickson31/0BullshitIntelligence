// 0BullshitIntelligence Testing Interface JavaScript

class TestingInterface {
    constructor() {
        this.currentTab = 'dashboard';
        this.websocket = null;
        this.init();
    }

    init() {
        this.setupTabNavigation();
        this.setupEventListeners();
        this.checkConnectionStatus();
        this.loadDashboard();
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            if (this.currentTab === 'dashboard') {
                this.loadDashboard();
            }
        }, 30000);
    }

    setupTabNavigation() {
        const tabs = document.querySelectorAll('.nav-tab');
        const contents = document.querySelectorAll('.tab-content');

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetTab = tab.dataset.tab;
                
                // Update active tab
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                // Update active content
                contents.forEach(c => c.classList.remove('active'));
                document.getElementById(`${targetTab}-tab`).classList.add('active');
                
                this.currentTab = targetTab;
                this.loadTabContent(targetTab);
            });
        });
    }

    setupEventListeners() {
        // Chat form
        const chatForm = document.getElementById('chat-form');
        if (chatForm) {
            chatForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendChatMessage();
            });
        }

        // Search forms
        const investorSearchForm = document.getElementById('investor-search-form');
        if (investorSearchForm) {
            investorSearchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.searchInvestors();
            });
        }

        const fundSearchForm = document.getElementById('fund-search-form');
        if (fundSearchForm) {
            fundSearchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.searchFunds();
            });
        }

        // Connection test button
        const testConnectionBtn = document.getElementById('test-connection');
        if (testConnectionBtn) {
            testConnectionBtn.addEventListener('click', () => {
                this.checkConnectionStatus();
            });
        }
    }

    async loadTabContent(tabName) {
        switch (tabName) {
            case 'dashboard':
                await this.loadDashboard();
                break;
            case 'chat':
                await this.loadConversations();
                break;
            case 'data':
                await this.loadSearchResults();
                break;
            case 'investors':
                await this.loadInvestorData();
                break;
            case 'funds':
                await this.loadFundData();
                break;
        }
    }

    async checkConnectionStatus() {
        const statusElement = document.getElementById('connection-status');
        const statusDot = document.querySelector('.status-dot');
        
        try {
            const response = await fetch('/test-connection');
            const data = await response.json();
            
            if (data.status === 'connected') {
                statusElement.textContent = 'Connected';
                statusDot.classList.remove('error');
                this.showAlert('Database connection successful', 'success');
            } else {
                statusElement.textContent = 'Error';
                statusDot.classList.add('error');
                this.showAlert(`Connection error: ${data.error}`, 'error');
            }
        } catch (error) {
            statusElement.textContent = 'Error';
            statusDot.classList.add('error');
            this.showAlert(`Failed to test connection: ${error.message}`, 'error');
        }
    }

    async loadDashboard() {
        try {
            const response = await fetch('/api/dashboard-stats');
            const stats = await response.json();
            
            if (stats.error) {
                this.showAlert(`Error loading dashboard: ${stats.error}`, 'error');
                return;
            }

            this.updateDashboardStats(stats);
        } catch (error) {
            this.showAlert(`Failed to load dashboard: ${error.message}`, 'error');
        }
    }

    updateDashboardStats(stats) {
        // Update user stats
        document.getElementById('total-users').textContent = stats.users?.total || 0;
        document.getElementById('free-users').textContent = stats.users?.by_plan?.free || 0;
        document.getElementById('pro-users').textContent = stats.users?.by_plan?.pro || 0;
        document.getElementById('outreach-users').textContent = stats.users?.by_plan?.outreach || 0;

        // Update activity stats
        document.getElementById('conversations-24h').textContent = stats.activity_24h?.conversations || 0;
        document.getElementById('messages-24h').textContent = stats.activity_24h?.messages || 0;
        document.getElementById('searches-24h').textContent = stats.activity_24h?.searches || 0;

        // Update database stats
        document.getElementById('total-angels').textContent = stats.database?.angel_investors || 0;
        document.getElementById('total-funds').textContent = stats.database?.investment_funds || 0;
        document.getElementById('total-companies').textContent = stats.database?.companies || 0;
    }

    async loadConversations() {
        try {
            const response = await fetch('/api/conversations');
            const conversations = await response.json();
            
            const container = document.getElementById('conversations-container');
            if (!container) return;

            if (conversations.length === 0) {
                container.innerHTML = '<p class="text-muted">No conversations found</p>';
                return;
            }

            container.innerHTML = conversations.map(conv => `
                <div class="card" onclick="this.loadConversationMessages('${conv.id}')">
                    <div class="card-header">
                        <h3 class="card-title">${conv.title || 'Untitled Conversation'}</h3>
                        <span class="text-muted">${this.formatDate(conv.created_at)}</span>
                    </div>
                    <div>
                        <p><strong>User:</strong> ${conv.users?.name || 'Unknown'} (${conv.users?.email || 'No email'})</p>
                        <p><strong>Plan:</strong> ${conv.users?.plan || 'free'}</p>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            this.showAlert(`Failed to load conversations: ${error.message}`, 'error');
        }
    }

    async loadConversationMessages(conversationId) {
        try {
            const response = await fetch(`/api/conversations/${conversationId}/messages`);
            const messages = await response.json();
            
            const chatMessages = document.getElementById('chat-messages');
            if (!chatMessages) return;

            chatMessages.innerHTML = messages.map(msg => `
                <div class="message ${msg.role}">
                    <div class="message-content">${msg.content}</div>
                    <div class="message-time">${this.formatDate(msg.created_at)}</div>
                    ${msg.gemini_prompt_used ? `<div class="text-muted"><small>Prompt: ${msg.gemini_prompt_used}</small></div>` : ''}
                </div>
            `).join('');

            chatMessages.scrollTop = chatMessages.scrollHeight;
        } catch (error) {
            this.showAlert(`Failed to load messages: ${error.message}`, 'error');
        }
    }

    async sendChatMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) return;

        const chatMessages = document.getElementById('chat-messages');
        const sendButton = document.querySelector('#chat-form button');
        
        // Disable input and show loading
        input.disabled = true;
        sendButton.disabled = true;
        sendButton.innerHTML = '<div class="spinner"></div> Sending...';

        // Add user message to chat
        chatMessages.innerHTML += `
            <div class="message user">
                <div class="message-content">${message}</div>
                <div class="message-time">${this.formatDate(new Date())}</div>
            </div>
        `;

        try {
            const response = await fetch('/api/simulate-chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            });

            const result = await response.json();

            if (result.status === 'success') {
                // Add AI response to chat
                chatMessages.innerHTML += `
                    <div class="message assistant">
                        <div class="message-content">${result.ai_response}</div>
                        <div class="message-time">${this.formatDate(new Date())}</div>
                        <div class="text-muted"><small>Processing time: ${result.processing_time_ms}ms</small></div>
                    </div>
                `;
                
                input.value = '';
                this.showAlert('Message sent successfully', 'success');
            } else {
                this.showAlert(`Error: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showAlert(`Failed to send message: ${error.message}`, 'error');
        } finally {
            // Re-enable input
            input.disabled = false;
            sendButton.disabled = false;
            sendButton.innerHTML = 'Send';
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    async searchInvestors() {
        const searchTerm = document.getElementById('investor-search-term').value.trim();
        const resultsContainer = document.getElementById('investor-results');
        const searchButton = document.querySelector('#investor-search-form button');
        
        searchButton.disabled = true;
        searchButton.innerHTML = '<div class="spinner"></div> Searching...';
        
        try {
            const response = await fetch(`/api/investors/search?q=${encodeURIComponent(searchTerm)}`);
            const investors = await response.json();
            
            if (investors.length === 0) {
                resultsContainer.innerHTML = '<p class="text-muted">No investors found</p>';
                return;
            }

            resultsContainer.innerHTML = investors.map(investor => `
                <div class="result-item">
                    <div class="result-header">
                        <div>
                            <h3 class="result-title">${investor.fullName || 'Unknown'}</h3>
                            <p class="result-subtitle">${investor.headline || 'No headline'}</p>
                            <p class="result-subtitle">${investor.addressWithCountry || 'No location'}</p>
                        </div>
                        <div class="result-score">${investor.angel_score || 'N/A'}</div>
                    </div>
                    <div>
                        <p><strong>Categories:</strong> ${investor.categories_general_en || 'None'}</p>
                        <p><strong>Stages:</strong> ${investor.stages_general_en || 'None'}</p>
                        ${investor.linkedinUrl ? `<p><strong>LinkedIn:</strong> <a href="${investor.linkedinUrl}" target="_blank" class="text-primary">View Profile</a></p>` : ''}
                    </div>
                </div>
            `).join('');
            
        } catch (error) {
            this.showAlert(`Search failed: ${error.message}`, 'error');
        } finally {
            searchButton.disabled = false;
            searchButton.innerHTML = 'Search Investors';
        }
    }

    async searchFunds() {
        const searchTerm = document.getElementById('fund-search-term').value.trim();
        const resultsContainer = document.getElementById('fund-results');
        const searchButton = document.querySelector('#fund-search-form button');
        
        searchButton.disabled = true;
        searchButton.innerHTML = '<div class="spinner"></div> Searching...';
        
        try {
            const response = await fetch(`/api/funds/search?q=${encodeURIComponent(searchTerm)}`);
            const funds = await response.json();
            
            if (funds.length === 0) {
                resultsContainer.innerHTML = '<p class="text-muted">No funds found</p>';
                return;
            }

            resultsContainer.innerHTML = funds.map(fund => `
                <div class="result-item">
                    <div class="result-header">
                        <div>
                            <h3 class="result-title">${fund.name || 'Unknown Fund'}</h3>
                            <p class="result-subtitle">${fund.short_description || 'No description'}</p>
                            <p class="result-subtitle">${fund['location_identifiers/0/value'] || 'No location'}</p>
                        </div>
                    </div>
                    <div>
                        <p><strong>Description:</strong> ${(fund.description || '').substring(0, 200)}${fund.description && fund.description.length > 200 ? '...' : ''}</p>
                        <p><strong>Categories:</strong> ${fund.category_keywords || 'None'}</p>
                        <p><strong>Stages:</strong> ${fund.stage_keywords || 'None'}</p>
                        ${fund['linkedin/value'] ? `<p><strong>LinkedIn:</strong> <a href="${fund['linkedin/value']}" target="_blank" class="text-primary">View Profile</a></p>` : ''}
                        ${fund['website/value'] ? `<p><strong>Website:</strong> <a href="${fund['website/value']}" target="_blank" class="text-primary">Visit Website</a></p>` : ''}
                    </div>
                </div>
            `).join('');
            
        } catch (error) {
            this.showAlert(`Search failed: ${error.message}`, 'error');
        } finally {
            searchButton.disabled = false;
            searchButton.innerHTML = 'Search Funds';
        }
    }

    async loadSearchResults() {
        try {
            const response = await fetch('/api/search-results');
            const results = await response.json();
            
            const container = document.getElementById('search-results-container');
            if (!container) return;

            if (results.length === 0) {
                container.innerHTML = '<p class="text-muted">No search results found</p>';
                return;
            }

            container.innerHTML = results.map(result => `
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">${result.search_type || 'Unknown'} Search</h3>
                        <span class="text-muted">${this.formatDate(result.created_at)}</span>
                    </div>
                    <div>
                        <p><strong>User:</strong> ${result.users?.name || 'Unknown'} (${result.users?.plan || 'free'})</p>
                        <p><strong>Project:</strong> ${result.projects?.name || 'No project'} - ${result.projects?.stage || 'Unknown stage'} in ${result.projects?.category || 'Unknown category'}</p>
                        <p><strong>Results Found:</strong> ${result.total_found || 0}</p>
                        <p><strong>Average Relevance:</strong> ${result.average_relevance ? result.average_relevance.toFixed(2) : 'N/A'}</p>
                        <p><strong>Credits Used:</strong> ${result.credits_used || 0}</p>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            this.showAlert(`Failed to load search results: ${error.message}`, 'error');
        }
    }

    async loadInvestorData() {
        try {
            const response = await fetch('/api/investors?limit=50');
            const investors = await response.json();
            
            const container = document.getElementById('investors-container');
            if (!container) return;

            if (investors.length === 0) {
                container.innerHTML = '<p class="text-muted">No investor data found</p>';
                return;
            }

            container.innerHTML = `
                <div class="table-container">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Location</th>
                                <th>Score</th>
                                <th>Categories</th>
                                <th>Stages</th>
                                <th>LinkedIn</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${investors.map(investor => `
                                <tr>
                                    <td>
                                        <strong>${investor.fullName || 'Unknown'}</strong><br>
                                        <small>${investor.headline || 'No headline'}</small>
                                    </td>
                                    <td>${investor.addressWithCountry || 'Unknown'}</td>
                                    <td><span class="result-score">${investor.angel_score || 'N/A'}</span></td>
                                    <td>${(investor.categories_general_en || '').substring(0, 50)}${investor.categories_general_en && investor.categories_general_en.length > 50 ? '...' : ''}</td>
                                    <td>${(investor.stages_general_en || '').substring(0, 50)}${investor.stages_general_en && investor.stages_general_en.length > 50 ? '...' : ''}</td>
                                    <td>${investor.linkedinUrl ? `<a href="${investor.linkedinUrl}" target="_blank" class="text-primary">View</a>` : 'N/A'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } catch (error) {
            this.showAlert(`Failed to load investor data: ${error.message}`, 'error');
        }
    }

    async loadFundData() {
        try {
            const response = await fetch('/api/funds?limit=50');
            const funds = await response.json();
            
            const container = document.getElementById('funds-container');
            if (!container) return;

            if (funds.length === 0) {
                container.innerHTML = '<p class="text-muted">No fund data found</p>';
                return;
            }

            container.innerHTML = `
                <div class="table-container">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Location</th>
                                <th>Description</th>
                                <th>Categories</th>
                                <th>Stages</th>
                                <th>Links</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${funds.map(fund => `
                                <tr>
                                    <td>
                                        <strong>${fund.name || 'Unknown Fund'}</strong><br>
                                        <small>${fund.short_description || 'No description'}</small>
                                    </td>
                                    <td>${fund['location_identifiers/0/value'] || 'Unknown'}</td>
                                    <td>${(fund.description || '').substring(0, 100)}${fund.description && fund.description.length > 100 ? '...' : ''}</td>
                                    <td>${(fund.category_keywords || '').substring(0, 50)}${fund.category_keywords && fund.category_keywords.length > 50 ? '...' : ''}</td>
                                    <td>${(fund.stage_keywords || '').substring(0, 50)}${fund.stage_keywords && fund.stage_keywords.length > 50 ? '...' : ''}</td>
                                    <td>
                                        ${fund['linkedin/value'] ? `<a href="${fund['linkedin/value']}" target="_blank" class="text-primary">LinkedIn</a>` : ''}
                                        ${fund['website/value'] ? `<a href="${fund['website/value']}" target="_blank" class="text-primary">Website</a>` : ''}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } catch (error) {
            this.showAlert(`Failed to load fund data: ${error.message}`, 'error');
        }
    }

    showAlert(message, type = 'info') {
        // Remove existing alerts
        const existingAlerts = document.querySelectorAll('.alert');
        existingAlerts.forEach(alert => alert.remove());

        // Create new alert
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;

        // Add to page
        const mainContent = document.querySelector('.main-content');
        mainContent.insertBefore(alert, mainContent.firstChild);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TestingInterface();
});