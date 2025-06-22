# DevCascade - Intelligent Workflow Automation Assistant

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Introduction

DevCascade is a revolutionary AI-powered workflow automation platform designed to streamline development team operations through natural language processing. By integrating seamlessly with essential development tools like GitHub, Jira, Jenkins, and Slack, DevCascade transforms complex multi-step workflows into simple conversational commands.

Instead of manually switching between different platforms to check repositories, create tickets, trigger builds, or send notifications, developers can simply chat with DevCascade using plain English commands. The platform intelligently understands your intent and executes the necessary actions across all connected services.

## ✨ Key Features

- **🤖 Natural Language Processing**: Powered by Google's Gemini AI for intelligent command interpretation
- **🔗 Multi-Service Integration**: Connect and orchestrate GitHub, Jira, Jenkins, and Slack in one platform
- **⚡ Instant Workflow Execution**: Execute complex operations with simple conversational commands
- **🔐 Secure Authentication**: Robust user authentication with JWT-based session management
- **📊 Real-time Chat Interface**: Interactive bot communication with instant feedback
- **🔍 Service Management**: Visual dashboard to monitor connection status of all integrated services

## 🎯 Advanced Features

- **🧠 Intelligent Context Understanding**: AI analyzes conversation history to provide contextual responses
- **🔄 Cross-Platform Orchestration**: Coordinate actions across multiple services in a single workflow
- **📈 Comprehensive Workflow History**: Track, review, and retry executed workflows with detailed step-by-step logging
- **🛠️ Automatic Retry Mechanisms**: Smart retry logic for failed operations with exponential backoff
- **🎨 Responsive Design**: Modern, mobile-friendly interface built with Tailwind CSS
- **📱 Real-time Notifications**: Instant updates on workflow progress and completion status

## 🔄 How It Works

### Step 1: User Authentication
- **Login Process**: Users can register and log in using their email credentials
- **Session Management**: Secure JWT token-based authentication ensures user sessions remain active
- **Profile Creation**: System automatically creates user profiles with personalized settings

### Step 2: Service Connection
After logging in, users need to connect their development services:

#### Connecting GitHub
- Navigate to the integrations section
- Click "Connect GitHub"
- Obtain your GitHub Personal Access Token from GitHub Settings → Developer Settings → Personal Access Tokens
- Enter the token to establish connection

#### Connecting Jira
- Click "Connect Jira" 
- Get your Jira API token from Jira Account Settings → Security → API Tokens
- Provide your Jira domain URL, username, and API token

#### Connecting Jenkins
- Select "Connect Jenkins"
- Generate Jenkins API token from Jenkins User Settings → Configure → API Token
- Enter Jenkins server URL, username, and API token

#### Connecting Slack
- Choose "Connect Slack"
- Create a Slack app at api.slack.com/apps
- Install the app to your workspace and copy the Bot User OAuth Token
- Enter the token to enable Slack integration

#### Connecting Gemini AI
- **Required for core functionality**
- Visit Google AI Studio (aistudio.google.com/app/apikey)
- Generate your Gemini API key
- Add the key to enable natural language processing

### Step 3: Using DevCascade
Once services are connected, you can perform various operations through natural language:

#### GitHub Operations
- **Repository Management**: "Show me all repositories in my organization"
- **Branch Information**: "How many branches does the main repository have?"
- **Issue Tracking**: "List all open issues assigned to me"
- **Commit History**: "What are the latest 5 commits in the development branch?"
- **Pull Requests**: "Show me pending pull requests that need review"

#### Jira Operations
- **Ticket Management**: "Create a new bug ticket for login issues"
- **Sprint Planning**: "Show me all tasks in the current sprint"
- **Status Updates**: "Move ticket PROJ-123 to In Progress"
- **Reporting**: "Generate a summary of completed tasks this week"

#### Jenkins Operations
- **Build Management**: "Trigger a build for the main branch"
- **Deployment**: "Deploy the latest version to staging environment"
- **Job Monitoring**: "Check the status of the last deployment"
- **Build History**: "Show me the last 10 build results"

#### Slack Operations
- **Team Communication**: "Send a deployment notification to the dev team"
- **Status Updates**: "Notify the team about the production release"
- **Alert Management**: "Send an alert about the server downtime"

## 🏗️ Architecture Overview

### Frontend Layer
- **Technology**: HTML5, Tailwind CSS, Vanilla JavaScript
- **Components**: 
  - Real-time chat interface with WebSocket communication
  - Service integration dashboard with visual status indicators
  - Workflow history viewer with expandable execution details
  - Responsive design optimized for desktop and mobile devices
- **Features**: 
  - Dynamic UI updates without page refresh
  - Interactive service connection management
  - Real-time workflow progress tracking

### Backend Layer
- **Framework**: FastAPI (Python) with async/await support
- **Core Components**:
  - **Authentication System**: JWT-based user management with secure token handling
  - **AI Processing Engine**: Google Gemini AI integration for natural language understanding
  - **Service Adapters**: Modular connectors for each integrated service (GitHub, Jira, Jenkins, Slack)
  - **Workflow Orchestrator**: Manages multi-step operations across different services
  - **API Gateway**: Centralized endpoint management with rate limiting and validation
- **Data Storage**: In-memory storage (suitable for development; database recommended for production)

### Integration Layer
- **GitHub API**: Repository management, issue tracking, pull requests, branch operations
- **Jira REST API**: Ticket creation, status updates, project management, sprint planning
- **Jenkins API**: Build triggering, job monitoring, deployment automation, build history
- **Slack Web API**: Message sending, channel management, user notifications
- **Gemini AI API**: Natural language processing, intent recognition, context understanding

### Workflow Execution Process
1. **Input Processing**: User sends natural language command through chat interface
2. **AI Analysis**: Gemini AI processes the command and extracts actionable intent
3. **Service Mapping**: System determines which services need to be involved
4. **Workflow Planning**: Creates step-by-step execution plan with proper sequencing
5. **Sequential Execution**: Executes each step with comprehensive error handling
6. **Progress Updates**: Provides real-time feedback throughout the workflow
7. **Result Compilation**: Aggregates results and presents comprehensive summary

## 🛠️ Technology Stack

### Backend Technologies
- **FastAPI**: High-performance, async Python web framework
- **Google Gemini AI**: Advanced large language model for natural language processing
- **Uvicorn**: Lightning-fast ASGI server for Python applications
- **Pydantic**: Data validation and serialization using Python type hints
- **Python Requests**: HTTP library for external API integrations
- **JWT (PyJWT)**: JSON Web Tokens for secure authentication

### Frontend Technologies
- **HTML5**: Modern semantic markup with accessibility features
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **Vanilla JavaScript**: Pure JavaScript for DOM manipulation and API communication
- **WebSocket API**: Real-time bidirectional communication
- **CSS Grid & Flexbox**: Modern responsive layout techniques

### APIs and Integrations
- **GitHub REST API v4**: Repository and organization management
- **Jira REST API v2/v3**: Project management and issue tracking
- **Jenkins REST API**: Continuous integration and deployment
- **Slack Web API**: Team communication and collaboration
- **Google Gemini AI API**: Natural language processing and understanding

## 💻 System Requirements

### Minimum Requirements
- **Operating System**: Windows 10, macOS 10.14, or Linux (Ubuntu 18.04+)
- **Python**: Version 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 1GB free disk space
- **Network**: Stable internet connection for API communications

### Software Dependencies
- **Python Package Manager**: pip (included with Python)
- **Web Browser**: Modern browser with JavaScript support
  - Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Git**: For repository cloning and version control

### Development Tools (Optional)
- **VS Code**: Recommended IDE with Live Server extension
- **Postman**: For API testing and documentation
- **Python Virtual Environment**: For dependency isolation

## 🚀 Getting Started

### 1. Repository Setup
```bash
# Clone the repository
git clone <your-repository-url>
cd <repository-directory>

# Verify Python installation
python --version  # Should output 3.8 or higher
```

### 2. Backend Setup

#### Install Dependencies
```bash
# Install required packages
pip install -r requirements.txt

# Alternative: Using virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your API keys
# At minimum, set GEMINI_API_KEY for core functionality
```

#### Start Backend Server
```bash
# Method 1: Direct execution
python main.py

# Method 2: Using Uvicorn (recommended)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API server will be available at `http://localhost:8000`
Interactive documentation at `http://localhost:8000/docs`

### 3. Frontend Setup

#### Option 1: VS Code Live Server
1. Install "Live Server" extension in VS Code
2. Right-click on `index.html`
3. Select "Open with Live Server"
4. Application opens automatically in browser

#### Option 2: Python HTTP Server
```bash
# Serve static files
python -m http.server 3000

# Access application at http://localhost:3000
```

### 4. First-Time Setup
1. **Register Account**: Create new user account with email and password
2. **Connect Services**: Add API keys for desired services (GitHub, Jira, Jenkins, Slack)
3. **Test Integration**: Send a simple command like "Show me my GitHub repositories"
4. **Explore Features**: Try different natural language commands to familiarize yourself with capabilities

## 📚 API Documentation

### Authentication Endpoints
- `POST /auth/register`: Create new user account
- `POST /auth/login`: Authenticate existing user
- `GET /auth/me`: Get current user information

### Integration Management
- `POST /integrations/connect`: Connect new service integration
- `GET /integrations/list`: List all connected services
- `DELETE /integrations/{id}`: Remove service integration

### Chat and Workflows
- `POST /chat/process`: Process natural language commands
- `GET /workflows/history`: Retrieve workflow execution history
- `GET /workflows/{id}`: Get specific workflow details
- `POST /workflows/{id}/retry`: Retry failed workflow

### Service-Specific Endpoints
- **GitHub**: `/github/*` - Repository operations, issue management
- **Jira**: `/jira/*` - Ticket operations, project management  
- **Jenkins**: `/jenkins/*` - Build operations, deployment management
- **Slack**: `/slack/*` - Messaging, notification management

For complete API documentation, visit `http://localhost:8000/docs` after starting the backend server.

## 🔧 Configuration

### Environment Variables
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key

# Optional service integrations
GITHUB_TOKEN=your_github_token
JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your_email@example.com
JIRA_API_TOKEN=your_jira_token
JENKINS_URL=http://your-jenkins:8080
JENKINS_USERNAME=your_username
JENKINS_API_TOKEN=your_jenkins_token
SLACK_BOT_TOKEN=xoxb-your-slack-token
```

### Development vs Production
- **Development**: Uses in-memory storage, debug logging enabled
- **Production**: Requires database setup, secure HTTPS, environment-specific configurations

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Visit `http://localhost:8000/docs` for API reference
- **Issues**: Report bugs on GitHub repository
- **Community**: Join our Discord server for community support
