import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from core.config import settings
from core.security import encrypt_token, integrations_db
from views.api_service import make_service_api_call
from views.schemas.chat import ChatMessage, ChatResponse
from views.service_connection import ServiceConnection
from views.service_validator import ServiceValidator
from views.workflow_processor import WorkflowProcessor
from views.workflow_service import (
    execute_workflow_actions,
    get_user_info,
    process_with_gemini,
    workflows_db,
)

router = APIRouter(tags=["agent"])

logger = logging.getLogger(__name__)

GEMINI_API_KEY = settings.GEMINI_API_KEY


@router.get("/")
async def serve_frontend():
    """Serve the main frontend page"""
    frontend_path = "../frontend/index.html"
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {"message": "AutoFlowBot API is running. Frontend not found."}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "version": "1.0.0"}


@router.post("/integrations/connect")
async def connect_service(connection: ServiceConnection, request: Request):
    """Connect a new service integration with real validation"""
    user_info = get_user_info(request)

    try:
        validation_result = await ServiceValidator.validate_service(
            connection.service_type, connection.service_url, connection.api_token, connection.username
        )

        if not validation_result.get("valid"):
            raise HTTPException(status_code=401, detail="Service validation failed")

        # Create integration record
        integration_id = str(uuid.uuid4())
        integration_data = {
            "id": integration_id,
            "user_name": connection.user_name or user_info["name"],
            "user_email": connection.user_email or user_info["email"],
            "service_type": connection.service_type,
            "service_url": connection.service_url,
            # "encrypted_token": encrypt_token(connection.api_token),  # Store encrypted token
            "encrypted_token": connection.api_token,  # Store encrypted token
            "username": connection.username or validation_result.get("username"),
            "config_data": connection.config_data or {},
            "created_at": datetime.utcnow().isoformat(),
            "status": "active",
            "service_info": validation_result.get("service_info", {}),
            "validated_at": datetime.utcnow().isoformat(),
            "validation_data": {
                "email": validation_result.get("email"),
                "display_name": validation_result.get("display_name") or validation_result.get("name"),
                "avatar_url": validation_result.get("avatar_url"),
                "scopes": validation_result.get("scopes", []),
            },
        }
        integrations_db[integration_id] = integration_data
        return {
            "message": f"{connection.service_type.title()} connected successfully",
            "integration_id": integration_id,
            "service_type": connection.service_type,
            "username": validation_result.get("username"),
            "email": validation_result.get("email"),
            "validated_at": integration_data["validated_at"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Service connection error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to connect service")


@router.get("/integrations/list")
async def list_integrations(request: Request):
    """List all integrations for the current user"""
    user_info = get_user_info(request)
    user_integrations = []

    for integration in integrations_db.values():
        if integration["user_email"] == user_info["email"]:
            safe_integration = {
                "id": integration["id"],
                "service_type": integration["service_type"],
                "service_url": integration["service_url"],
                "username": integration["username"],
                "status": integration["status"],
                "created_at": integration["created_at"],
                "validated_at": integration.get("validated_at"),
                "service_info": integration.get("service_info", {}),
                "validation_data": integration.get("validation_data", {}),
            }
            user_integrations.append(safe_integration)

    return user_integrations


@router.get("/integrations/{integration_id}/test")
async def test_integration(integration_id: str, request: Request):
    """Test an existing integration"""
    user_info = get_user_info(request)

    try:
        result = await make_service_api_call(integration_id, user_info["email"], "/user", "GET")

        return {
            "status": "success",
            "message": "Integration is working properly",
            "api_response_code": result["status_code"],
            "tested_at": datetime.utcnow().isoformat(),
        }

    except HTTPException as e:
        return {"status": "error", "message": str(e.detail), "tested_at": datetime.utcnow().isoformat()}


@router.post("/integrations/{integration_id}/api-call")
async def make_api_call(
    integration_id: str, endpoint: str, method: str = "GET", data: Optional[Dict] = None, request: Request = None
):
    """Make an API call using stored integration"""
    user_info = get_user_info(request)

    try:
        result = await make_service_api_call(integration_id, user_info["email"], endpoint, method, data)
        return result
    except HTTPException:
        raise


@router.delete("/integrations/{integration_id}")
async def disconnect_service(integration_id: str, request: Request):
    """Disconnect a service integration"""
    user_info = get_user_info(request)

    integration = integrations_db.get(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    if integration["user_email"] != user_info["email"]:
        raise HTTPException(status_code=403, detail="Access denied")
    del integrations_db[integration_id]

    return {"message": "Service disconnected successfully", "integration_id": integration_id}


@router.post("/chat/process", response_model=ChatResponse)
async def process_chat_message(message: ChatMessage, request: Request):
    """Process chat message and potentially execute workflows"""
    user_info = get_user_info(request)
    user_name = message.user_name or user_info["name"]
    user_email = message.user_email or user_info["email"]
    connected_services = []
    for integration in integrations_db.values():
        if integration["user_email"] == user_email:
            connected_services.append(integration["service_type"])
    user_context = {"name": user_name, "email": user_email, "connected_services": connected_services}
    ai_response = await process_with_gemini(message.message, user_context)

    # get the github token and user from connected services
    GITHUB_TOKEN = None
    GITHUB_OWNER = None
    SLACK_TOKEN = None

    for con in connected_services:
        if con == "github":
            github_integration = next(
                (
                    i
                    for i in integrations_db.values()
                    if i["service_type"] == "github" and i["user_email"] == user_email
                ),
                None,
            )
            if github_integration:
                GITHUB_TOKEN = github_integration["encrypted_token"]
                GITHUB_OWNER = github_integration["username"]
                print(f"Using GitHub token for {GITHUB_OWNER}: {GITHUB_TOKEN}")
                break
        elif con == "slack":
            slack_integration = next(
                (
                    i
                    for i in integrations_db.values()
                    if i["service_type"] == "slack" and i["user_email"] == user_email
                ),
                None,
            )
            if slack_integration:
                SLACK_TOKEN = slack_integration["encrypted_token"]
                print(f"Using Slack token: {SLACK_TOKEN}")
                break

    processor = WorkflowProcessor(
        gemini_api_key=GEMINI_API_KEY, github_token=GITHUB_TOKEN, github_owner=GITHUB_OWNER, slack_token=SLACK_TOKEN
    )

    response = processor.process_query(message.message)

    # workflow_id = None
    # actions_taken = []
    # if ai_response.get("workflow_needed", False):
    #     actions = ai_response.get("actions", [])
    #     services = ai_response.get("services_required", [])
    #     workflow_title = ai_response.get("workflow_title", "")

    #     if actions:
    #         workflow_id = await execute_workflow_actions(actions, services, user_name, user_email, workflow_title)
    #         actions_taken = actions

    # return ChatResponse(
    #     response=ai_response.get("response", "I'm here to help with your workflow automation needs!"),
    #     workflow_id=workflow_id,
    #     actions_taken=actions_taken,
    # )

    return ChatResponse(
        response=response,
        workflow_id=None,
        actions_taken=[],
    )


@router.get("/workflows/history")
async def get_workflow_history(request: Request):
    """Get workflow history for the current user"""
    user_info = get_user_info(request)
    user_workflows = []

    for workflow in workflows_db.values():
        if workflow["user_email"] == user_info["email"]:
            user_workflows.append(workflow)
    user_workflows.sort(key=lambda x: x["created_at"], reverse=True)

    return user_workflows


@router.get("/workflows/{workflow_id}")
async def get_workflow_details(workflow_id: str, request: Request):
    """Get detailed information about a specific workflow"""
    user_info = get_user_info(request)

    workflow = workflows_db.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if workflow["user_email"] != user_info["email"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return workflow


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str, request: Request):
    """Delete a workflow from history"""
    user_info = get_user_info(request)

    workflow = workflows_db.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if workflow["user_email"] != user_info["email"]:
        raise HTTPException(status_code=403, detail="Access denied")

    del workflows_db[workflow_id]

    return {"message": "Workflow deleted successfully", "workflow_id": workflow_id}


@router.get("/stats")
async def get_user_stats(request: Request):
    """Get user statistics"""
    user_info = get_user_info(request)
    integrations_count = sum(
        1 for integration in integrations_db.values() if integration["user_email"] == user_info["email"]
    )
    workflows_count = sum(1 for workflow in workflows_db.values() if workflow["user_email"] == user_info["email"])
    completed_workflows = sum(
        1
        for workflow in workflows_db.values()
        if (workflow["user_email"] == user_info["email"] and workflow["status"] == "completed")
    )

    return {
        "integrations_count": integrations_count,
        "workflows_count": workflows_count,
        "completed_workflows": completed_workflows,
        "success_rate": round((completed_workflows / workflows_count * 100) if workflows_count > 0 else 0, 2),
    }


@router.get("/integrations/{integration_id}/github/repos")
async def get_github_repos(integration_id: str, request: Request):
    """Get GitHub repositories for the authenticated user"""
    user_info = get_user_info(request)

    try:
        result = await make_service_api_call(integration_id, user_info["email"], "/user/repos?per_page=100", "GET")
        return result["data"]
    except HTTPException:
        raise


@router.post("/integrations/{integration_id}/github/issues")
async def create_github_issue(
    integration_id: str, repo_owner: str, repo_name: str, title: str, body: str = "", request: Request = None
):
    """Create a GitHub issue"""
    user_info = get_user_info(request)

    data = {"title": title, "body": body}

    try:
        result = await make_service_api_call(
            integration_id, user_info["email"], f"/repos/{repo_owner}/{repo_name}/issues", "POST", data
        )
        return result["data"]
    except HTTPException:
        raise


@router.post("/integrations/{integration_id}/slack/message")
async def send_slack_message(integration_id: str, channel: str, text: str, request: Request):
    """Send a Slack message"""
    user_info = get_user_info(request)

    data = {"channel": channel, "text": text}

    try:
        result = await make_service_api_call(integration_id, user_info["email"], "/chat.postMessage", "POST", data)
        return result["data"]
    except HTTPException:
        raise


@router.get("/integrations/{integration_id}/slack/channels")
async def get_slack_channels(integration_id: str, request: Request):
    """Get Slack channels"""
    user_info = get_user_info(request)

    try:
        result = await make_service_api_call(
            integration_id, user_info["email"], "/conversations.list?types=public_channel,private_channel", "GET"
        )
        return result["data"]
    except HTTPException:
        raise


# JIRA-specific endpoints
@router.post("/integrations/{integration_id}/jira/issues")
async def create_jira_issue(
    integration_id: str,
    project_key: str,
    summary: str,
    description: str = "",
    issue_type: str = "Task",
    request: Request = None,
):
    """Create a JIRA issue"""
    user_info = get_user_info(request)

    data = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
        }
    }

    try:
        result = await make_service_api_call(integration_id, user_info["email"], "/rest/api/3/issue", "POST", data)
        return result["data"]
    except HTTPException:
        raise


@router.get("/integrations/{integration_id}/jira/projects")
async def get_jira_projects(integration_id: str, request: Request):
    """Get JIRA projects"""
    user_info = get_user_info(request)

    try:
        result = await make_service_api_call(integration_id, user_info["email"], "/rest/api/3/project", "GET")
        return result["data"]
    except HTTPException:
        raise


# Jenkins-specific endpoints
@router.post("/integrations/{integration_id}/jenkins/build")
async def trigger_jenkins_build(
    integration_id: str, job_name: str, parameters: Optional[Dict] = None, request: Request = None
):
    """Trigger a Jenkins build"""
    user_info = get_user_info(request)

    endpoint = f"/job/{job_name}/build"
    if parameters:
        endpoint = f"/job/{job_name}/buildWithParameters"

    try:
        result = await make_service_api_call(integration_id, user_info["email"], endpoint, "POST", parameters or {})
        return result
    except HTTPException:
        raise


@router.get("/integrations/{integration_id}/jenkins/jobs")
async def get_jenkins_jobs(integration_id: str, request: Request):
    """Get Jenkins jobs"""
    user_info = get_user_info(request)

    try:
        result = await make_service_api_call(
            integration_id, user_info["email"], "/api/json?tree=jobs[name,url,buildable,color]", "GET"
        )
        return result["data"]
    except HTTPException:
        raise


@router.get("/integrations/{integration_id}/jenkins/job/{job_name}/builds")
async def get_jenkins_build_history(integration_id: str, job_name: str, request: Request):
    """Get Jenkins build history for a job"""
    user_info = get_user_info(request)

    try:
        result = await make_service_api_call(
            integration_id,
            user_info["email"],
            f"/job/{job_name}/api/json?tree=builds[number,result,timestamp,duration,url]",
            "GET",
        )
        return result["data"]
    except HTTPException:
        raise


# Catch-all route for serving frontend files
@router.get("/{path:path}")
async def serve_static_files(path: str):
    """Serve static frontend files"""
    file_path = f"../frontend/{path}"
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    frontend_path = "../frontend/index.html"
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)

    raise HTTPException(status_code=404, detail="File not found")
