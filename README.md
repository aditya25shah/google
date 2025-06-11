AutoFlowBot - Workflow Automation Assistant
AutoFlowBot is a comprehensive workflow automation assistant that integrates with various development tools like GitHub, Jira, Jenkins, and Slack to streamline your development processes through natural language commands.
Features

Natural Language Processing: Powered by Google's Gemini AI
Multi-Service Integration: Connect GitHub, Jira, Jenkins, Slack
Workflow Automation: Execute complex workflows with simple commands
User Authentication: Secure login and registration system
Workflow History: Track and review executed workflows
Real-time Chat Interface: Interactive bot communication

Setup Instructions
1. Backend Setup

Install Python dependencies:
```bash
pip install -r requirements.txt
```

Configure environment variables:

Copy the .env file and update the values
Required: Set your GEMINI_API_KEY from Google AI Studio
Optional: Configure API keys for GitHub, Jira, Jenkins, Slack


Run the FastAPI server:
```bash
python main.py
```
or
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
The API will be available at http://localhost:8000

2. Frontend Setup

Serve the HTML file:

Use a local web server (like Live Server in VS Code)
Or use Python's built-in server:
```bash
python -m http.server 3000
```


Access the application:

Open http://localhost:3000 in your browser



3. Getting API Keys
Gemini AI (Required)

Go to Google AI Studio
Create a new API key
Add it to your .env file as GEMINI_API_KEY

GitHub (Optional)

Go to GitHub Settings > Developer settings > Personal access tokens
Generate a new token with appropriate permissions
Add to .env as GITHUB_TOKEN

Jira (Optional)

Go to your Jira account settings
Create an API token
Add your Jira URL, username, and token to .env

Jenkins (Optional)

Generate an API token in Jenkins user settings
Add Jenkins URL, username, and token to .env

Slack (Optional)

Create a Slack app at api.slack.com
Get the bot token and webhook URL
Add to .env

Usage
1. User Registration/Login

Create an account or login with existing credentials
All user data is stored in memory (replace with database in production)

2. Connect Services

Click "Connect" buttons for each service you want to integrate
Provide API credentials for each service
Services will show as "Connected" once configured

3. Chat with AutoFlowBot
Use natural language commands like:

"Deploy the latest release to staging"
"Create a new GitHub issue for bug fix"
"Trigger Jenkins build for main branch"
"Send deployment notification to team"
"Create a Jira ticket for feature request"

4. View Workflow History

See executed workflows in the history section
Click "View Details" to see workflow steps and status

API Endpoints
Authentication

POST /auth/register - Register new user
POST /auth/login - User login
GET /auth/me - Get current user info

Integrations

POST /integrations/connect - Connect a service
GET /integrations/list - List connected services
DELETE /integrations/{id} - Disconnect service

Chat & Workflows

POST /chat/process - Process chat message
GET /workflows/history - Get workflow history
GET /workflows/{id} - Get workflow details
POST /workflows/{id}/retry - Retry failed workflow

Service-Specific Endpoints

GitHub: /github/* endpoints
Jira: /jira/* endpoints
Jenkins: /jenkins/* endpoints
Slack: /slack/* endpoints

Development Notes
Current Limitations

In-memory storage (implement database for production)
Simulated service integrations (implement actual API calls)
Basic error handling (enhance for production)
No data encryption for API tokens (implement for production)

Security Considerations

Encrypt sensitive data (API tokens, passwords)
Implement proper CORS policies
Add rate limiting
Use HTTPS in production
Implement proper session management

Future Enhancements

Database integration (PostgreSQL/MongoDB)
Real service API integrations
Advanced workflow orchestration
Webhook support for real-time updates
Multi-tenant support
Advanced user management
Workflow templates
Scheduled workflows

Troubleshooting
Common Issues

CORS Errors

Ensure the frontend is served from a web server, not opened directly as a file
Check CORS configuration in main.py


API Connection Issues

Verify the backend is running on port 8000
Check the baseURL in script.js


Gemini AI Not Working

Verify your GEMINI_API_KEY is valid
Check your Google AI Studio quota


Service Connection Failures

Verify API credentials are correct
Check service-specific API documentation
Ensure proper permissions are granted



Contributing

Fork the repository
Create a feature branch
Make your changes
Test thoroughly
Submit a pull request

License
This project is licensed under the MIT License.
Support
For issues and questions:

Check the troubleshooting section
Review the API documentation at http://localhost:8000/docs
Open an issue on the project repository
