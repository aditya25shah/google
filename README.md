# DevCascade - Your Intelligent Workflow Automation Assistant

DevCascade streamlines your development processes by integrating with essential tools like GitHub, Jira, Jenkins, and Slack. Leverage the power of natural language commands to manage complex workflows effortlessly.

## Features

Natural Language Processing: Powered by Google's Gemini AI
Multi-Service Integration: Connect GitHub, Jira, Jenkins, Slack
Workflow Automation: Execute complex workflows with simple commands
User Authentication: Secure login and registration system
Workflow History: Track and review executed workflows
Real-time Chat Interface: Interactive bot communication

## Prerequisites

- Python 3.8+
- pip (Python package installer)

## Getting Started

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd <repository-directory>
```

### 2. Backend Setup

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

### 3. Frontend Setup

Serve the HTML file:

Use a local web server (like Live Server in VS Code)
Or use Python's built-in server:
```bash
python -m http.server 3000
```


Access the application:

Open http://localhost:3000 in your browser



### 4. Getting API Keys

#### Gemini AI (Required)
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey) (or search for "Google AI Studio API Key").
2. Create a new API key.
3. Add it to your `.env` file as `GEMINI_API_KEY`.

#### GitHub (Optional)
1. Go to GitHub **Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
2. Click **Generate new token** (or "Generate new token (classic)").
3. Give your token a descriptive name.
4. Select the necessary scopes/permissions (e.g., `repo` for accessing repositories, `workflow` for GitHub Actions, etc., depending on your bot's needs).
5. Click **Generate token**.
6. Copy the token immediately (you won't see it again).
7. Add it to your `.env` file as `GITHUB_TOKEN`.

#### Jira (Optional)
1. Go to your Jira account settings:
    - Click on your profile picture in the bottom left.
    - Select **Profile**.
    - Go to **Security** > **Create and manage API tokens** (or similar wording depending on your Jira version).
2. Click **Create API token**.
3. Give your token a label.
4. Click **Create**.
5. Copy the token immediately.
6. Add your Jira URL (e.g., `JIRA_URL=https://your-domain.atlassian.net`), your Jira email/username (e.g., `JIRA_USERNAME=your_email@example.com`), and the API token (e.g., `JIRA_API_TOKEN=your_token`) to your `.env` file.

#### Jenkins (Optional)
1. Log in to your Jenkins instance.
2. Click on your username in the top right corner.
3. Select **Configure** (or **My Views** > **Configure** depending on the version).
4. Under the "API Token" section, click **Add new Token**.
5. Give the token a name and click **Generate**.
6. Copy the generated token immediately.
7. Add your Jenkins URL (e.g., `JENKINS_URL=http://your-jenkins-server:8080`), your Jenkins username (e.g., `JENKINS_USERNAME=your_username`), and the API token (e.g., `JENKINS_API_TOKEN=your_token`) to your `.env` file.

#### Slack (Optional)
1. Go to api.slack.com/apps and click **Create New App**.
2. Choose "From scratch", give your app a name, and select your workspace.
3. Under "Add features and functionality", select **Bots**.
4. Configure your bot user and add necessary scopes under **OAuth & Permissions** (e.g., `chat:write`, `commands`).
5. Install the app to your workspace.
6. Copy the **Bot User OAuth Token** (starts with `xoxb-`).
7. Add this token to your `.env` file (e.g., `SLACK_BOT_TOKEN=your_xoxb_token`).
8. (Optional) If you need a Webhook URL for incoming messages to Slack, navigate to **Incoming Webhooks**, activate it, and add a new webhook to your workspace. Copy the Webhook URL and add it to `.env` (e.g., `SLACK_WEBHOOK_URL=your_webhook_url`).

## Usage

### 1. User Registration/Login

- Create an account or log in with existing credentials.
- Note: All user data is currently stored in memory. This should be replaced with a persistent database solution in a production environment.

### 2. Connect Services

- Click the "Connect" button for each service (GitHub, Jira, Jenkins, Slack) you wish to integrate.
- Provide the necessary API credentials when prompted.
- Services will indicate a "Connected" status once successfully configured.

### 3. Chat with DevCascade

Interact with DevCascade using natural language commands in the chat interface. Examples include:
- "Deploy the latest release to staging"
- "Create a new GitHub issue for bug fix"
- "Trigger Jenkins build for main branch"
- "Send deployment notification to team"
- "Create a Jira ticket for feature request"

### 4. View Workflow History

- Executed workflows are logged in the history section.
- Click "View Details" for a specific workflow to see its individual steps and their statuses.

## API Reference

The backend exposes the following API endpoints. For detailed interactive documentation (Swagger UI), navigate to `http://localhost:8000/docs` after starting the backend server.

### Authentication
- `POST /auth/register`: Register a new user.
- `POST /auth/login`: Log in an existing user.
- `GET /auth/me`: Get information about the currently authenticated user.

### Integrations
- `POST /integrations/connect`: Connect a new service.
- `GET /integrations/list`: List all currently connected services.
- `DELETE /integrations/{id}`: Disconnect a specific service by its ID.

### Chat & Workflows
- `POST /chat/process`: Process a chat message and potentially trigger a workflow.
- `GET /workflows/history`: Retrieve the history of executed workflows.
- `GET /workflows/{id}`: Get details for a specific workflow by its ID.
- `POST /workflows/{id}/retry`: Retry a failed workflow by its ID.

### Service-Specific Endpoints
- **GitHub:** `/github/*` (e.g., for repository actions, issue management)
- **Jira:** `/jira/*` (e.g., for ticket creation, status updates)
- **Jenkins:** `/jenkins/*` (e.g., for triggering builds, checking job status)
- **Slack:** `/slack/*` (e.g., for sending messages, notifications)

## Developer Information

### Current Limitations
- **In-memory Storage:** User data and workflow history are stored in memory and will be lost on server restart. Implement a database (e.g., PostgreSQL, MongoDB) for production.
- **Simulated Service Integrations:** Some service integrations might be simulated. Implement actual API calls for full functionality.
- **Basic Error Handling:** Error handling is currently basic. Enhance this for robustness in a production environment.
- **No API Token Encryption:** Sensitive data like API tokens are not encrypted at rest. Implement encryption for production.

### Security Considerations
- **Data Encryption:** Encrypt sensitive data, including API tokens and user passwords, both in transit (HTTPS) and at rest.
- **CORS Policy:** Implement and configure a proper Cross-Origin Resource Sharing (CORS) policy.
- **Rate Limiting:** Add rate limiting to API endpoints to prevent abuse.
- **HTTPS:** Always use HTTPS in production environments.
- **Session Management:** Implement secure and robust session management.
- **Input Validation:** Thoroughly validate and sanitize all user inputs.

### Future Enhancements / Roadmap
- Database integration (e.g., PostgreSQL, MongoDB)
- Full implementation of real service API integrations
- Advanced workflow orchestration and customization
- Webhook support for real-time updates from integrated services
- Multi-tenant support
- Advanced user and permission management
- Workflow templates for common tasks
- Scheduled and recurring workflows

## Troubleshooting

### Common Issues

#### CORS Errors
- Ensure the frontend is served from a web server (e.g., `python -m http.server` or VS Code Live Server) and not opened directly as a `file:///` URL.
- Verify the CORS configuration in `main.py` (FastAPI backend) allows requests from your frontend's origin.

#### API Connection Issues
- Confirm the backend server is running (typically on `http://localhost:8000`).
- Double-check the `baseURL` or API endpoint configuration in your frontend JavaScript (`script.js`).

#### Gemini AI Not Working
- Verify that your `GEMINI_API_KEY` in the `.env` file is correct and active.
- Check your usage quota and API status in the Google AI Studio.

#### Service Connection Failures
- Ensure the API credentials (tokens, URLs, usernames) entered for GitHub, Jira, Jenkins, or Slack are accurate.
- Consult the respective service's API documentation for specific error messages or connection requirements.
- Verify that the API tokens/keys have the necessary permissions/scopes granted for the intended operations.

## Contributing

We welcome contributions to DevCascade! Please follow these steps:
1. Fork the repository.
2. Create a new feature branch (`git checkout -b feature/YourAmazingFeature`).
3. Make your changes and commit them with clear, descriptive messages.
4. Test your changes thoroughly.
5. Push your branch to your fork (`git push origin feature/YourAmazingFeature`).
6. Open a pull request against the main repository.

Please ensure your code adheres to the project's coding standards and includes relevant tests where applicable.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Support

If you encounter issues or have questions:
- First, check the **Troubleshooting** section above.
- Review the interactive API documentation available at `http://localhost:8000/docs` (once the backend is running).
- Open an issue on the project's GitHub repository, providing as much detail as possible.
