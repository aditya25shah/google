# DevCascade - Intelligent Workflow Automation Assistant

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Table of Contents
- [Introduction](#introduction)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [Architecture Overview](#architecture-overview)
- [System Requirements](#system-requirements)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [Support](#support)

## Introduction

DevCascade is a revolutionary AI-powered workflow automation platform that streamlines development team operations through natural language processing. Instead of manually switching between GitHub, Jira, Jenkins, and Slack, simply chat with DevCascade using plain English commands.

**Transform this:**
```
1. Open GitHub → Check repositories
2. Switch to Jira → Create ticket
3. Go to Jenkins → Trigger build  
4. Open Slack → Notify team
```

**Into this:**
```
"Create a bug ticket for login issues, trigger a build for main branch, and notify the dev team"
```

## Key Features

### **Natural Language Processing**
Powered by Google's Gemini AI for intelligent command interpretation

### **Multi-Service Integration** 
Connect GitHub, Jira, Jenkins, and Slack in one unified platform

### **Instant Workflow Execution**
Execute complex operations with simple conversational commands

### **Secure Authentication**
Robust JWT-based session management with encrypted API tokens

### **Real-time Chat Interface**
Interactive bot communication with instant feedback and progress updates

### **Service Management Dashboard**
Visual monitoring of all integrated services with connection status

### **Advanced Features**
- Intelligent context understanding with conversation history
- Cross-platform workflow orchestration
- Comprehensive execution logging and retry mechanisms
- Mobile-responsive design built with Tailwind CSS

## Quick Start

Get DevCascade running in under 5 minutes:

```bash
# 1. Clone and setup
git clone <your-repository-url>
cd <repository-directory>

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure (minimum required)
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 4. Start the application
python main.py

# 5. Open browser
# Backend: http://localhost:8000
# Frontend: Open index.html in browser or use Live Server
```

**First steps after setup:**
1. Register your account
2. Connect at least GitHub and Gemini AI
3. Try: *"Show me my repositories"*

## How It Works

### Step 1: User Authentication

#### Login Process
Users can register and log in using their email credentials to access the DevCascade platform.

#### Session Management
Secure JWT token-based authentication ensures user sessions remain active and protected throughout their usage.

#### Profile Creation
The system automatically creates personalized user profiles with customized settings upon registration.

### Step 2: Service Connection

After logging in, users need to connect their development services to enable full functionality:

#### Connecting GitHub
1. Navigate to the integrations section in your dashboard
2. Click **"Connect GitHub"**
3. Obtain your GitHub Personal Access Token:
   - Go to GitHub Settings → Developer Settings → Personal Access Tokens
   - Generate a new token with appropriate permissions
4. Enter the token to establish the connection

#### Connecting Jira
1. Click **"Connect Jira"** in the integrations panel
2. Get your Jira API token:
   - Access Jira Account Settings → Security → API Tokens
   - Create a new API token
3. Provide the following information:
   - Jira domain URL
   - Username
   - API token

#### Connecting Jenkins
1. Select **"Connect Jenkins"** from the available integrations
2. Generate your Jenkins API token:
   - Go to Jenkins User Settings → Configure → API Token
   - Create a new API token
3. Enter the required details:
   - Jenkins server URL
   - Username
   - API token

#### Connecting Slack
1. Choose **"Connect Slack"** to enable team communication
2. Create a Slack app:
   - Visit api.slack.com/apps
   - Create a new app for your workspace
3. Install the app to your workspace and copy the Bot User OAuth Token
4. Enter the token to complete the Slack integration

![image](https://github.com/user-attachments/assets/d1a9005a-a18a-4390-984d-7a4d139b1a8e)

#### Connecting Gemini AI
**Required for core functionality**
1. Visit Google AI Studio at aistudio.google.com/app/apikey
2. Generate your Gemini API key
3. Add the key to enable natural language processing capabilities

### Step 3: Using DevCascade

Once all services are connected, you can perform various operations through natural language commands:

#### GitHub Operations

**Repository Management**
- *"Show me all repositories in my organization"* - View all repos within your organization
- *"List my personal repositories"* - Display repositories you own

**Branch Information**
- *"How many branches does the main repository have?"* - Get branch count for specific repos
- *"Show me all branches in [repository-name]"* - View branch details

**Issue Tracking**
- *"List all open issues assigned to me"* - View your assigned issues
- *"Show issues with high priority"* - Filter issues by priority level
- *"Create a new issue for [description]"* - Generate new issues

**Commit History**
- *"What are the latest 5 commits in the development branch?"* - View recent commits
- *"Show commit history for the last week"* - Time-based commit filtering

**Pull Requests**
- *"Show me pending pull requests that need review"* - View PRs awaiting review
- *"List my open pull requests"* - Display your submitted PRs
- 
![image](https://github.com/user-attachments/assets/73c71d59-6938-4226-8086-f91399e3c11f)

#### The Issue he raise :-

![image](https://github.com/user-attachments/assets/262f5e38-bdae-4b72-baa0-752248645447)

#### Jira Operations

**Ticket Management**
- *"Create a new bug ticket for login issues"* - Generate bug reports
- *"Show all tickets assigned to me"* - View your assigned work
- *"Update ticket [TICKET-ID] with progress notes"* - Add updates to existing tickets

**Sprint Planning**
- *"Show me all tasks in the current sprint"* - View current sprint backlog
- *"Move [TICKET-ID] to next sprint"* - Manage sprint assignments
- *"Create sprint report for team review"* - Generate sprint summaries

**Status Updates**
- *"Move ticket PROJ-123 to In Progress"* - Update ticket status
- *"Mark [TICKET-ID] as completed"* - Close finished work
- *"Set [TICKET-ID] priority to high"* - Modify ticket priority

**Reporting**
- *"Generate a summary of completed tasks this week"* - Create progress reports
- *"Show team velocity for last sprint"* - View performance metrics
- *"Create burndown chart for current sprint"* - Generate visual reports

#### Jenkins Operations

**Build Management**
- *"Trigger a build for the main branch"* - Initiate builds on demand
- *"Start build for [project-name]"* - Build specific projects
- *"Cancel running build for [job-name]"* - Stop active builds

**Deployment**
- *"Deploy the latest version to staging environment"* - Push to staging
- *"Promote staging build to production"* - Production deployments
- *"Rollback production to previous version"* - Revert deployments

**Job Monitoring**
- *"Check the status of the last deployment"* - Monitor deployment progress
- *"Show me running jobs"* - View active Jenkins jobs
- *"Get build logs for [job-name]"* - Access detailed build information

**Build History**
- *"Show me the last 10 build results"* - View recent build outcomes
- *"Display failed builds from this week"* - Filter by build status
- *"Generate build report for [project-name]"* - Create build summaries

#### Slack Operations

**Team Communication**
- *"Send a deployment notification to the dev team"* - Broadcast deployment updates
- *"Notify QA team about new build availability"* - Coordinate testing activities
- *"Share sprint review summary with stakeholders"* - Distribute project updates

**Status Updates**
- *"Notify the team about the production release"* - Announce releases
- *"Send daily standup reminder"* - Facilitate team meetings
- *"Share code review completion status"* - Update on review progress

**Alert Management**
- *"Send an alert about the server downtime"* - Communicate urgent issues
- *"Notify on-call team about system errors"* - Escalate critical problems
- *"Create incident notification for database issues"* - Manage incident response

#### Getting Started Tips

1. **Complete all integrations** - Ensure all required services are connected for full functionality
2. **Use natural language** - Speak to DevCascade as you would to a team member
3. **Be specific** - Include project names, ticket IDs, and branch names for accurate results
4. **Explore capabilities** - Try different command variations to discover all available features
5. **Monitor responses** - Review system feedback to understand command success and errors

#### Support and Troubleshooting

If you encounter issues with service connections or commands, verify that:
- All API tokens are valid and have appropriate permissions
- Service URLs are correctly formatted
- Your account has necessary access rights for the requested operations
- Network connectivity to integrated services is available

## Architecture Overview

### Frontend Layer
- **Technology**: HTML5, Tailwind CSS, Vanilla JavaScript
- **Features**: Real-time chat interface, service integration dashboard, workflow history viewer, responsive design

### Backend Layer
- **Framework**: FastAPI (Python) with async/await support
- **Core Components**: JWT authentication, AI processing engine, service adapters, workflow orchestrator, API gateway
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

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10, macOS 10.14, or Linux (Ubuntu 18.04+)
- **Python**: Version 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 1GB free disk space
- **Network**: Stable internet connection for API communications

### Technology Stack

#### Backend Technologies
- **FastAPI**: High-performance, async Python web framework
- **Google Gemini AI**: Advanced large language model for natural language processing
- **Uvicorn**: Lightning-fast ASGI server for Python applications
- **Pydantic**: Data validation and serialization using Python type hints

#### Frontend Technologies
- **HTML5**: Modern semantic markup with accessibility features
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **Vanilla JavaScript**: Pure JavaScript for DOM manipulation and API communication
- **WebSocket API**: Real-time bidirectional communication

## Configuration

### Environment Variables
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key
```

You just need to get an API key from Google AI Studio and you're ready to get started.

### Development vs Production
- **Development**: Uses in-memory storage, debug logging enabled
- **Production**: Requires database setup, secure HTTPS, environment-specific configurations

## API Documentation

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

For complete interactive API documentation, visit `http://localhost:8000/docs` after starting the backend server.

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## Support

- **Documentation**: Visit `http://localhost:8000/docs` for API reference
- **Issues**: Report bugs on GitHub repository
- **License**: This project is licensed under the MIT License

---

## Get Started Now!

Ready to streamline your development workflow? Get DevCascade running in 5 minutes:

```bash
git clone <your-repository-url> && cd <repository-directory>
pip install -r requirements.txt && python main.py
```

Start chatting with your development tools today! 🚀
