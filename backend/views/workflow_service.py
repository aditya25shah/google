import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

import google.generativeai as genai
from core.config import settings
from fastapi import Request
from views.enums import WorkflowStatus
from views.schemas.workflow import Workflow, WorkflowStep

logger = logging.getLogger(__name__)

workflows_db = {}

GEMINI_API_KEY = settings.GEMINI_API_KEY


def get_user_info(request: Request) -> Dict[str, str]:
    """Extract user info from headers or return defaults"""
    return {
        "name": request.headers.get("X-User-Name", "Anonymous User"),
        "email": request.headers.get("X-User-Email", "user@example.com"),
    }


async def process_with_gemini(message: str, user_context: dict) -> Dict[str, Any]:
    """Process user message with Gemini AI"""
    if not GEMINI_API_KEY:
        return {
            "response": "AI processing is not available. Please configure GEMINI_API_KEY.",
            "workflow_needed": False,
            "services_required": [],
            "actions": [],
        }

    try:
        prompt = f"""
You are DevCascade, an intelligent and conversational DevOps assistant with dual capabilities: engaging in natural conversation AND automating complex workflows.

## Your Personality
- Friendly, professional, and knowledgeable
- Always helpful and understanding
- Can chat naturally about any topic
- Expert in DevOps, software development, and workflow automation
- Proactive in suggesting automation opportunities

## User Context
User: {user_context.get('name', 'Team Member')}
Role: {user_context.get('role', 'Developer')}
Connected Services: {', '.join(user_context.get('connected_services', []))}
Current Project: {user_context.get('current_project', 'Not specified')}

## Message Analysis
User Message: {message}

## Core Capabilities

### 1. Natural Conversation
Handle ANY topic naturally and helpfully:
- Greetings and casual chat
- Technical questions and explanations
- General knowledge and advice
- Troubleshooting and problem-solving
- Code help and best practices

### 2. Workflow Automation Detection
Identify when users want to automate tasks involving:
- **GitHub**: Creating issues, PRs, managing repositories
- **Jira**: Ticket management, project tracking
- **Jenkins**: Build automation, deployment pipelines
- **Slack**: Team communication, notifications
- **General DevOps**: CI/CD, monitoring, deployment

### 3. Smart Response Logic
For EVERY message, determine:

**CONVERSATION TYPE:**
- `general_chat`: Casual conversation, greetings, general questions
- `technical_help`: Programming help, explanations, troubleshooting
- `workflow_automation`: Clear automation request
- `workflow_suggestion`: Could benefit from automation

**RESPONSE STRATEGY:**
- **General Chat**: Respond naturally and conversationally
- **Technical Help**: Provide detailed, helpful explanations
- **Workflow Automation**: Process the automation request
- **Workflow Suggestion**: Answer the question AND suggest automation

## Response Guidelines

### For General Conversation:
- Be warm, friendly, and natural
- Show genuine interest in helping
- Provide thoughtful, relevant responses
- Use conversational language
- Don't force automation unless clearly requested

### For Technical Questions:
- Give clear, detailed explanations
- Provide examples when helpful
- Offer multiple approaches when applicable
- Suggest best practices
- If relevant, mention how automation could help

### For Automation Requests:
- Confirm understanding of the request
- Identify required services and parameters
- Provide step-by-step workflow plan
- Explain what will happen at each step
- Ask for confirmation if anything is unclear

### For Workflow Suggestions:
- Answer the immediate question first
- Then suggest: "I could help automate this process..."
- Explain the automation benefits
- Keep suggestions optional and non-pushy

## Example Responses

**General Chat:**
User: "hello 4"
Response: "Hello! Good to see you again! How can I help you today? Whether you need to chat, have technical questions, or want to automate some workflows, I'm here for you."

**Technical Help:**
User: "How do I fix a merge conflict?"
Response: "Merge conflicts happen when Git can't automatically combine changes. Here's how to resolve them: [detailed explanation]. By the way, if you deal with merge conflicts frequently, I could help set up automated conflict detection and team notifications."

**Automation Request:**
User: "Create a GitHub issue for the login bug"
Response: "I'll help you create a GitHub issue for the login bug. I need a few details: Which repository should I create this in? What specific details should I include about the bug?"

## Important Rules
1. **Always respond helpfully** - Never say you can't understand simple greetings or general questions
2. **Be contextually aware** - Remember the user's role and connected services
3. **Suggest automation naturally** - When it makes sense, not forced
4. **Maintain conversation flow** - Keep responses natural and engaging
5. **Provide value immediately** - Answer questions first, then suggest improvements

## Task
Analyze the user's message and provide an appropriate response based on the conversation type identified. Be helpful, natural, and genuinely useful in every interaction.
"""

        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")

        response = model.generate_content(prompt)

        try:
            # Try to parse as JSON first
            result = json.loads(response.text)
            return result
        except json.JSONDecodeError:
            # If not JSON, extract the response text and create a basic structure
            return {
                "response": response.text,
                "workflow_needed": False,
                "services_required": [],
                "actions": [],
                "workflow_title": "",
            }
    except Exception as e:
        logger.error(f"Gemini processing error: {str(e)}")
        return {
            "response": f"I encountered an error processing your request: {str(e)}. Please try again or rephrase your question.",
            "workflow_needed": False,
            "services_required": [],
            "actions": [],
            "workflow_title": "",
        }


async def execute_workflow_actions(
    actions: List[str], services: List[str], user_name: str, user_email: str, workflow_title: str = ""
) -> str:
    """Execute workflow actions and store in database"""
    workflow_id = str(uuid.uuid4())
    workflow_steps = []

    # Create workflow steps
    for i, action in enumerate(actions):
        service = services[i] if i < len(services) else "system"

        # Simulate different execution results
        status = "completed"
        details = {"message": f"Successfully executed: {action}"}

        # Simulate some realistic workflow actions
        if "create" in action.lower() and "jira" in service.lower():
            details["ticket_id"] = f"PROJ-{uuid.uuid4().hex[:4].upper()}"
        elif "deploy" in action.lower() and "jenkins" in service.lower():
            details["build_number"] = f"#{uuid.uuid4().hex[:3]}"
        elif "slack" in service.lower():
            details["channel"] = "#general"
            details["message_id"] = f"msg_{uuid.uuid4().hex[:6]}"
        elif "github" in service.lower():
            details["repository"] = "user/repo"
            details["commit_sha"] = uuid.uuid4().hex[:7]

        step = WorkflowStep(
            action=action, service=service, status=status, details=details, timestamp=datetime.utcnow()
        )
        workflow_steps.append(step)

    # Create workflow record
    workflow = Workflow(
        id=workflow_id,
        user_name=user_name,
        user_email=user_email,
        title=workflow_title or f"Automated Workflow - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        description=f"AI-generated workflow with {len(actions)} steps",
        status=WorkflowStatus.COMPLETED,
        steps=workflow_steps,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Store in database
    workflows_db[workflow_id] = workflow.dict()
    return workflow_id
