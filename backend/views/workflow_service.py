import json
import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import Request

from backend.views.enums import WorkflowStatus
from backend.views.schemas.workflow import Workflow, WorkflowStep

workflows_db = {}


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
        You are AutoFlowBot, a workflow automation assistant. 
        User: {user_context.get('name', 'Unknown')}
        Connected Services: {', '.join(user_context.get('connected_services', []))}
        
        User Message: {message}
        
        Analyze this message and determine if the user wants to:
        1. Create a workflow automation
        2. Get information about their services
        3. Ask a general question
        
        If it's a workflow request, identify:
        - Which services need to be involved
        - What actions should be performed
        - Step-by-step workflow actions
        
        Respond in a very professional way:
        1) Use full stops, commas to express and change paragraphs. Don't get carried away as it would be difficult for the user to read.
        2) Be respectful
        
        Examples of workflow requests:
        - "Create a JIRA ticket when GitHub issue is created"
        - "Deploy to Jenkins when PR is merged"
        - "Send Slack notification when build fails"
        
        Be helpful and explain what you understand from their request.
        """

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
