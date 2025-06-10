class AutoFlowBot {
    constructor() {
        this.baseURL = window.location.hostname === 'localhost' ? 
            'http://localhost:8000' : 
            window.location.origin;
        
        // Use in-memory storage instead of localStorage
        this.user = null;
        this.connectedServices = new Set();
        this.sessionData = {
            user: null,
            services: []
        };
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkUserStatus();
    }

    // Remove localStorage dependencies - use session memory instead
    loadUserFromStorage() {
        return this.sessionData.user;
    }

    saveUserToStorage(user) {
        this.sessionData.user = user;
        this.user = user;
    }

    setupEventListeners() {
        const loginForm = document.getElementById('login-form');
        if (loginForm) loginForm.addEventListener('submit', (e) => this.handleSimpleLogin(e));
        
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) logoutBtn.addEventListener('click', () => this.handleLogout());
        
        document.querySelectorAll('.connect-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const service = e.target.closest('[data-service]')?.dataset.service;
                if (service) this.showConnectionModal(service);
            });
        });

        const connectionForm = document.getElementById('connection-form');
        const cancelBtn = document.getElementById('cancel-connection');
        const closeBtn = document.querySelector('.close');
        
        if (connectionForm) connectionForm.addEventListener('submit', (e) => this.handleServiceConnection(e));
        if (cancelBtn) cancelBtn.addEventListener('click', () => this.hideConnectionModal());
        if (closeBtn) closeBtn.addEventListener('click', () => this.hideConnectionModal());

        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');
        
        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !chatInput.disabled) this.sendMessage();
            });
        }
        if (sendBtn) sendBtn.addEventListener('click', () => this.sendMessage());

        window.addEventListener('click', (e) => {
            const modal = document.getElementById('connection-modal');
            if (e.target === modal) {
                this.hideConnectionModal();
            }
        });
    }

    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...(this.user && { 
                    'X-User-Name': this.user.name, 
                    'X-User-Email': this.user.email 
                })
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            let data;
            const contentType = response.headers.get('content-type');
            
            if (contentType && contentType.includes('application/json')) {
                try {
                    data = await response.json();
                } catch (jsonError) {
                    // If JSON parsing fails, treat as text
                    data = { message: await response.text() };
                }
            } else {
                data = { message: await response.text() };
            }
            
            if (!response.ok) {
                // Better error message extraction
                let errorMessage = 'Request failed';
                
                if (data && typeof data === 'object') {
                    errorMessage = data.detail || data.message || data.error || 
                                 (data.errors && Array.isArray(data.errors) ? data.errors.join(', ') : null) ||
                                 `HTTP ${response.status}: ${response.statusText}`;
                } else if (typeof data === 'string') {
                    errorMessage = data;
                } else {
                    errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                }
                
                throw new Error(errorMessage);
            }
            
            return data;
        } catch (error) {
            console.error('API Request failed:', error);
            
            // Better error message for display
            let displayMessage = 'An error occurred while processing your request';
            
            if (error.message && error.message !== '[object Object]') {
                displayMessage = error.message;
            } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
                displayMessage = 'Unable to connect to the server. Please check your connection.';
            } else if (error.name === 'SyntaxError') {
                displayMessage = 'Server returned invalid response format';
            }
            
            this.showMessage(displayMessage, 'error');
            throw error;
        }
    }

    handleSimpleLogin(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const user = {
            name: formData.get('name') || 'Anonymous User',
            email: formData.get('email') || 'user@example.com',
            id: Date.now().toString(),
            created_at: new Date().toISOString()
        };
        
        this.saveUserToStorage(user);
        this.showDashboard();
        this.loadConnectedServices();
        this.showMessage('Welcome! You can now start using AutoFlowBot.', 'success');
    }

    handleLogout() {
        this.user = null;
        this.connectedServices.clear();
        this.sessionData = { user: null, services: [] };
        this.showLogin();
        this.showMessage('Logged out successfully!', 'success');
    }

    checkUserStatus() {
        const user = this.loadUserFromStorage();
        if (user) {
            this.user = user;
            this.showDashboard();
            this.loadConnectedServices();
        } else {
            this.showLogin();
        }
    }

    showLogin() {
        this.toggleSections('auth-section');
    }

    showDashboard() {
        this.toggleSections('dashboard');
        const userNameEl = document.getElementById('user-name');
        if (userNameEl) userNameEl.textContent = this.user?.name || 'User';
        
        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');
        if (chatInput) chatInput.disabled = false;
        if (sendBtn) sendBtn.disabled = false;
        
        this.loadWorkflowHistory();
    }

    toggleSections(activeSection) {
        const sections = ['auth-section', 'register-section', 'dashboard'];
        sections.forEach(section => {
            const el = document.getElementById(section);
            if (el) {
                el.style.display = section === activeSection ? 'block' : 'none';
            }
        });
    }

    showConnectionModal(service) {
        const modal = document.getElementById('connection-modal');
        const title = document.getElementById('modal-title');
        const serviceType = document.getElementById('service-type');
        
        if (title) title.textContent = `Connect ${service.charAt(0).toUpperCase() + service.slice(1)}`;
        if (serviceType) serviceType.value = service;
        
        this.configureModalForService(service);
        if (modal) modal.style.display = 'flex';
    }

    configureModalForService(service) {
        const usernameGroup = document.getElementById('username-group');
        const additionalConfig = document.getElementById('additional-config');
        const serviceUrl = document.getElementById('service-url');
        
        if (usernameGroup) usernameGroup.style.display = 'none';
        if (additionalConfig) additionalConfig.style.display = 'none';
        
        if (!serviceUrl) {
            console.error('Service URL input not found');
            return;
        }

        // Clear previous values and reset
        serviceUrl.disabled = false;
        serviceUrl.value = '';
        serviceUrl.placeholder = '';

        switch(service.toLowerCase()) {
            case 'github':
                serviceUrl.value = 'https://api.github.com';
                serviceUrl.disabled = true;
                serviceUrl.placeholder = 'GitHub API URL';
                if (usernameGroup) usernameGroup.style.display = 'block';
                break;
            case 'jira':
                serviceUrl.value = '';
                serviceUrl.placeholder = 'https://yourcompany.atlassian.net';
                serviceUrl.disabled = false;
                if (usernameGroup) usernameGroup.style.display = 'block';
                if (additionalConfig) additionalConfig.style.display = 'block';
                break;
            case 'jenkins':
                serviceUrl.value = '';
                serviceUrl.placeholder = 'https://your-jenkins-server.com';
                serviceUrl.disabled = false;
                if (usernameGroup) usernameGroup.style.display = 'block';
                break;
            case 'slack':
                serviceUrl.value = 'https://slack.com/api';
                serviceUrl.disabled = true;
                serviceUrl.placeholder = 'Slack API URL';
                if (additionalConfig) additionalConfig.style.display = 'block';
                break;
            default:
                serviceUrl.value = '';
                serviceUrl.placeholder = 'Enter service URL';
                break;
        }
        
        console.log(`Configured ${service} with URL: ${serviceUrl.value}`);
    }

    hideConnectionModal() {
        const modal = document.getElementById('connection-modal');
        const form = document.getElementById('connection-form');
        
        if (modal) modal.style.display = 'none';
        if (form) form.reset();
    }

    async handleServiceConnection(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        try {
            this.showLoading();
            
            let configData = {};
            const configText = formData.get('config_data');
            if (configText && configText.trim()) {
                try {
                    configData = JSON.parse(configText);
                } catch (parseError) {
                    throw new Error('Invalid JSON in configuration data. Please check the format.');
                }
            }

            const serviceData = {
                service_type: formData.get('service_type'),
                service_url: formData.get('service_url')?.trim(),
                api_token: formData.get('api_token')?.trim(),
                username: formData.get('username')?.trim() || null,
                config_data: configData,
                user_name: this.user.name,
                user_email: this.user.email
            };

            console.log('Form data collected:', {
                service_type: serviceData.service_type,
                service_url: serviceData.service_url,
                has_api_token: !!serviceData.api_token,
                username: serviceData.username
            });

            // Validate required fields
            if (!serviceData.service_type) {
                throw new Error('Service type is required');
            }
            if (!serviceData.api_token) {
                throw new Error('API token is required');
            }
            if (!serviceData.service_url) {
                // Try to get the URL from the input directly as fallback
                const urlInput = document.getElementById('service-url');
                if (urlInput && urlInput.value.trim()) {
                    serviceData.service_url = urlInput.value.trim();
                } else {
                    throw new Error(`Service URL is required for ${serviceData.service_type}`);
                }
            }

            console.log('Connecting service:', serviceData.service_type, 'to:', serviceData.service_url);
            
            const response = await this.makeRequest('/integrations/connect', {
                method: 'POST',
                body: JSON.stringify(serviceData)
            });

            this.connectedServices.add(serviceData.service_type);
            this.updateServiceStatus(serviceData.service_type, 'connected');
            this.saveConnectedServices(response.id, serviceData.service_type);
            this.hideConnectionModal();
            this.showMessage(`${serviceData.service_type} connected successfully!`, 'success');
        } catch (error) {
            console.error('Service connection failed:', error);
            // Error message will be shown by makeRequest, but we can add specific handling
            if (error.message.includes('fetch')) {
                this.showMessage('Cannot connect to server. Please check if the backend is running.', 'error');
            } else if (error.message.includes('required')) {
                // For validation errors, show them directly
                this.showMessage(error.message, 'error');
            }
        } finally {
            this.hideLoading();
        }
    }

    saveConnectedServices(integrationId, serviceType) {
        this.sessionData.services.push({
            id: integrationId,
            service_type: serviceType,
            connected_at: new Date().toISOString()
        });
    }

    async loadConnectedServices() {
        if (!this.user) return;
        
        try {
            // First load from session data
            this.sessionData.services.forEach(service => {
                this.connectedServices.add(service.service_type);
                this.updateServiceStatus(service.service_type, 'connected');
            });

            // Then sync with backend
            const services = await this.makeRequest('/integrations/list');
            this.connectedServices.clear();
            
            services.forEach(service => {
                this.connectedServices.add(service.service_type);
                this.updateServiceStatus(service.service_type, 'connected');
            });
            
            // Update session data
            this.sessionData.services = services.map(s => ({
                id: s.id,
                service_type: s.service_type,
                connected_at: s.created_at
            }));
        } catch (error) {
            console.error('Failed to load connected services:', error);
            // Fallback to session data if API fails
            this.sessionData.services.forEach(service => {
                this.connectedServices.add(service.service_type);
                this.updateServiceStatus(service.service_type, 'connected');
            });
        }
    }

    updateServiceStatus(service, status) {
        const statusElement = document.getElementById(`${service}-status`);
        const button = document.querySelector(`[data-service="${service}"] .connect-btn`);
        
        if (statusElement) {
            statusElement.textContent = status === 'connected' ? 'Connected' : 'Not Connected';
            statusElement.className = `connection-status px-3 py-1 rounded-full text-xs font-medium ${
                status === 'connected' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`;
        }
        
        if (button && status === 'connected') {
            button.innerHTML = `<i class="${this.getServiceIcon(service)} mr-2"></i>Reconnect`;
        }
    }

    getServiceIcon(service) {
        const icons = {
            github: 'fab fa-github',
            jira: 'fab fa-jira',
            jenkins: 'fas fa-cogs',
            slack: 'fab fa-slack'
        };
        return icons[service] || 'fas fa-plug';
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        if (!input) return;
        
        const message = input.value.trim();
        if (!message) return;
        
        this.addMessageToChat('user', message);
        input.value = '';
        
        try {
            const response = await this.makeRequest('/chat/process', {
                method: 'POST',
                body: JSON.stringify({ 
                    message,
                    user_name: this.user.name,
                    user_email: this.user.email
                })
            });

            // Add bot response to chat
            this.addMessageToChat('bot', response.response);
            
            // If workflow was executed, update history
            if (response.workflow_id) {
                this.loadWorkflowHistory();
                if (response.actions_taken && response.actions_taken.length > 0) {
                    this.showMessage('Workflow executed successfully!', 'success');
                }
            }
        } catch (error) {
            this.addMessageToChat('bot', 'Sorry, I encountered an error processing your request. Please try again.');
            console.error('Chat request failed:', error);
        }
    }

    addMessageToChat(sender, message) {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex items-start space-x-3 animate-slide-up';
        
        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <i class="fas fa-user text-white text-sm"></i>
                </div>
                <div class="bg-gray-100 rounded-2xl p-4 max-w-md">
                    <p class="text-gray-900">${this.escapeHtml(message)}</p>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <i class="fas fa-robot text-white text-sm"></i>
                </div>
                <div class="bg-primary-50 rounded-2xl p-4 max-w-md">
                    <p class="text-gray-900">${this.escapeHtml(message)}</p>
                </div>
            `;
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async loadWorkflowHistory() {
        if (!this.user) return;
        
        try {
            const workflows = await this.makeRequest('/workflows/history');
            this.displayWorkflowHistory(workflows);
        } catch (error) {
            console.error('Failed to load workflow history:', error);
            // Show empty state on error
            this.displayWorkflowHistory([]);
        }
    }

    displayWorkflowHistory(workflows) {
        const historyContainer = document.getElementById('workflow-history');
        if (!historyContainer) return;
        
        if (workflows.length === 0) {
            historyContainer.innerHTML = `
                <div class="text-center text-gray-500 py-8">
                    <i class="fas fa-clock text-3xl mb-3"></i>
                    <p>No workflows executed yet</p>
                    <p class="text-sm">Your automation history will appear here</p>
                </div>
            `;
            return;
        }
        
        historyContainer.innerHTML = '';
        workflows.forEach(workflow => {
            const workflowDiv = document.createElement('div');
            workflowDiv.className = 'bg-white rounded-xl p-4 border border-gray-200 hover:shadow-md transition duration-200';
            
            const statusColor = this.getStatusColor(workflow.status);
            const stepsCount = Array.isArray(workflow.steps) ? workflow.steps.length : 0;
            
            workflowDiv.innerHTML = `
                <div class="flex items-center justify-between mb-2">
                    <h4 class="font-semibold text-gray-900 truncate">${this.escapeHtml(workflow.title || 'Untitled Workflow')}</h4>
                    <span class="px-2 py-1 rounded-full text-xs font-medium ${statusColor}">
                        ${workflow.status || 'unknown'}
                    </span>
                </div>
                <p class="text-sm text-gray-600 mb-2">${stepsCount} steps</p>
                <p class="text-xs text-gray-500">${new Date(workflow.created_at).toLocaleString()}</p>
                <button class="mt-3 text-primary-600 hover:text-primary-700 text-sm font-medium" 
                        onclick="autoFlowBot.showWorkflowDetails('${workflow.id}')">
                    View Details
                </button>
            `;
            historyContainer.appendChild(workflowDiv);
        });
    }

    getStatusColor(status) {
        const colors = {
            'completed': 'bg-green-100 text-green-700',
            'running': 'bg-blue-100 text-blue-700',
            'failed': 'bg-red-100 text-red-700',
            'pending': 'bg-yellow-100 text-yellow-700'
        };
        return colors[status] || 'bg-gray-100 text-gray-700';
    }

    async showWorkflowDetails(workflowId) {
        try {
            const workflow = await this.makeRequest(`/workflows/${workflowId}`);
            const steps = Array.isArray(workflow.steps) ? 
                workflow.steps.map(s => `• ${s.action || s.description || 'Unknown step'}`).join('\n') :
                'No steps available';
            
            alert(`Workflow: ${workflow.title || 'Untitled'}\nStatus: ${workflow.status}\nSteps:\n${steps}`);
        } catch (error) {
            console.error('Failed to load workflow details:', error);
            alert('Failed to load workflow details. Please try again.');
        }
    }

    showLoading() {
        const loadingEl = document.getElementById('loading');
        if (loadingEl) loadingEl.style.display = 'flex';
    }

    hideLoading() {
        const loadingEl = document.getElementById('loading');
        if (loadingEl) loadingEl.style.display = 'none';
    }

    showMessage(message, type = 'info') {
        const container = document.getElementById('status-messages');
        if (!container) {
            console.log(`[${type.toUpperCase()}] ${message}`);
            return;
        }
        
        const messageDiv = document.createElement('div');
        const colors = {
            success: 'bg-green-100 border-green-200 text-green-800',
            error: 'bg-red-100 border-red-200 text-red-800',
            info: 'bg-blue-100 border-blue-200 text-blue-800'
        };
        
        messageDiv.className = `p-4 rounded-xl border ${colors[type]} animate-slide-up`;
        messageDiv.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} mr-2"></i>
                <span>${this.escapeHtml(message)}</span>
                <button class="ml-auto text-lg" onclick="this.parentElement.parentElement.remove()">&times;</button>
            </div>
        `;
        
        container.appendChild(messageDiv);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentElement) {
                messageDiv.remove();
            }
        }, 5000);
    }

    // Additional utility methods for testing service connections
    async testServiceConnection(serviceType) {
        try {
            const service = this.sessionData.services.find(s => s.service_type === serviceType);
            if (!service) {
                throw new Error('Service not found');
            }
            
            const result = await this.makeRequest(`/integrations/${service.id}/test`);
            this.showMessage(`${serviceType} connection test: ${result.status}`, 
                result.status === 'success' ? 'success' : 'error');
        } catch (error) {
            console.error('Service test failed:', error);
            this.showMessage(`Failed to test ${serviceType} connection`, 'error');
        }
    }

    // Method to get application stats
    async loadStats() {
        try {
            const stats = await this.makeRequest('/stats');
            return stats;
        } catch (error) {
            console.error('Failed to load stats:', error);
            return null;
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.autoFlowBot = new AutoFlowBot();
});

// Fallback for older browsers
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.autoFlowBot = new AutoFlowBot();
    });
} else {
    window.autoFlowBot = new AutoFlowBot();
}