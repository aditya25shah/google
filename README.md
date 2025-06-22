# DevCascade - Intelligent Workflow Automation Assistant

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Introduction

DevCascade is a revolutionary AI-powered workflow automation platform designed to streamline development team operations through natural language processing. By integrating seamlessly with essential development tools like GitHub, Jira, Jenkins, and Slack, DevCascade transforms complex multi-step workflows into simple conversational commands.

Instead of manually switching between different platforms to check repositories, create tickets, trigger builds, or send notifications, developers can simply chat with DevCascade using plain English commands. The platform intelligently understands your intent and executes the necessary actions across all connected services.

## Key Features

- ** Natural Language Processing**: Powered by Google's Gemini AI for intelligent command interpretation
- ** Multi-Service Integration**: Connect and orchestrate GitHub, Jira, Jenkins, and Slack in one platform
- ** Instant Workflow Execution**: Execute complex operations with simple conversational commands
- ** Secure Authentication**: Robust user authentication with JWT-based session management
- ** Real-time Chat Interface**: Interactive bot communication with instant feedback
- ** Service Management**: Visual dashboard to monitor connection status of all integrated services

##  Advanced Features

- ** Intelligent Context Understanding**: AI analyzes conversation history to provide contextual responses
- ** Cross-Platform Orchestration**: Coordinate actions across multiple services in a single workflow
- ** Comprehensive Workflow History**: Track, review, and retry executed workflows with detailed step-by-step logging
- ** Automatic Retry Mechanisms**: Smart retry logic for failed operations with exponential backoff
- ** Responsive Design**: Modern, mobile-friendly interface built with Tailwind CSS
- ** Real-time Notifications**: Instant updates on workflow progress and completion status

# DevCascade - How It Works

## Step 1: User Authentication

### Login Process
Users can register and log in using their email credentials to access the DevCascade platform.

### Session Management
Secure JWT token-based authentication ensures user sessions remain active and protected throughout their usage.

### Profile Creation
The system automatically creates personalized user profiles with customized settings upon registration.

## Step 2: Service Connection

After logging in, users need to connect their development services to enable full functionality:

### Connecting GitHub
1. Navigate to the integrations section in your dashboard
2. Click **"Connect GitHub"**
3. Obtain your GitHub Personal Access Token:
   - Go to GitHub Settings → Developer Settings → Personal Access Tokens
   - Generate a new token with appropriate permissions
4. Enter the token to establish the connection

### Connecting Jira
1. Click **"Connect Jira"** in the integrations panel
2. Get your Jira API token:
   - Access Jira Account Settings → Security → API Tokens
   - Create a new API token
3. Provide the following information:
   - Jira domain URL
   - Username
   - API token

### Connecting Jenkins
1. Select **"Connect Jenkins"** from the available integrations
2. Generate your Jenkins API token:
   - Go to Jenkins User Settings → Configure → API Token
   - Create a new API token
3. Enter the required details:
   - Jenkins server URL
   - Username
   - API token

### Connecting Slack
1. Choose **"Connect Slack"** to enable team communication
2. Create a Slack app:
   - Visit api.slack.com/apps
   - Create a new app for your workspace
3. Install the app to your workspace and copy the Bot User OAuth Token
4. Enter the token to complete the Slack integration

### Connecting Gemini AI
**Required for core functionality**
1. Visit Google AI Studio at aistudio.google.com/app/apikey
2. Generate your Gemini API key
3. Add the key to enable natural language processing capabilities

## Step 3: Using DevCascade

Once all services are connected, you can perform various operations through natural language commands:

### GitHub Operations

#### Repository Management
- **"Show me all repositories in my organization"** - View all repos within your organization
- **"List my personal repositories"** - Display repositories you own

#### Branch Information
- **"How many branches does the main repository have?"** - Get branch count for specific repos
- **"Show me all branches in [repository-name]"** - View branch details

#### Issue Tracking
- **"List all open issues assigned to me"** - View your assigned issues
- **"Show issues with high priority"** - Filter issues by priority level
- **"Create a new issue for [description]"** - Generate new issues

#### Commit History
- **"What are the latest 5 commits in the development branch?"** - View recent commits
- **"Show commit history for the last week"** - Time-based commit filtering

#### Pull Requests
- **"Show me pending pull requests that need review"** - View PRs awaiting review
- **"List my open pull requests"** - Display your submitted PRs

### Jira Operations

#### Ticket Management
- **"Create a new bug ticket for login issues"** - Generate bug reports
- **"Show all tickets assigned to me"** - View your assigned work
- **"Update ticket [TICKET-ID] with progress notes"** - Add updates to existing tickets

#### Sprint Planning
- **"Show me all tasks in the current sprint"** - View current sprint backlog
- **"Move [TICKET-ID] to next sprint"** - Manage sprint assignments
- **"Create sprint report for team review"** - Generate sprint summaries

#### Status Updates
- **"Move ticket PROJ-123 to In Progress"** - Update ticket status
- **"Mark [TICKET-ID] as completed"** - Close finished work
- **"Set [TICKET-ID] priority to high"** - Modify ticket priority

#### Reporting
- **"Generate a summary of completed tasks this week"** - Create progress reports
- **"Show team velocity for last sprint"** - View performance metrics
- **"Create burndown chart for current sprint"** - Generate visual reports

### Jenkins Operations

#### Build Management
- **"Trigger a build for the main branch"** - Initiate builds on demand
- **"Start build for [project-name]"** - Build specific projects
- **"Cancel running build for [job-name]"** - Stop active builds

#### Deployment
- **"Deploy the latest version to staging environment"** - Push to staging
- **"Promote staging build to production"** - Production deployments
- **"Rollback production to previous version"** - Revert deployments

#### Job Monitoring
- **"Check the status of the last deployment"** - Monitor deployment progress
- **"Show me running jobs"** - View active Jenkins jobs
- **"Get build logs for [job-name]"** - Access detailed build information

#### Build History
- **"Show me the last 10 build results"** - View recent build outcomes
- **"Display failed builds from this week"** - Filter by build status
- **"Generate build report for [project-name]"** - Create build summaries

### Slack Operations

#### Team Communication
- **"Send a deployment notification to the dev team"** - Broadcast deployment updates
- **"Notify QA team about new build availability"** - Coordinate testing activities
- **"Share sprint review summary with stakeholders"** - Distribute project updates

#### Status Updates
- **"Notify the team about the production release"** - Announce releases
- **"Send daily standup reminder"** - Facilitate team meetings
- **"Share code review completion status"** - Update on review progress

#### Alert Management
- **"Send an alert about the server downtime"** - Communicate urgent issues
- **"Notify on-call team about system errors"** - Escalate critical problems
- **"Create incident notification for database issues"** - Manage incident response

## Getting Started Tips

1. **Complete all integrations** - Ensure all required services are connected for full functionality
2. **Use natural language** - Speak to DevCascade as you would to a team member
3. **Be specific** - Include project names, ticket IDs, and branch names for accurate results
4. **Explore capabilities** - Try different command variations to discover all available features
5. **Monitor responses** - Review system feedback to understand command success and errors

## Support and Troubleshooting

If you encounter issues with service connections or commands, verify that:
- All API tokens are valid and have appropriate permissions
- Service URLs are correctly formatted
- Your account has necessary access rights for the requested operations
- Network connectivity to integrated services is available
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
You just need to get a API key From the Google AI Studio and You are Ready to Get Started.

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
