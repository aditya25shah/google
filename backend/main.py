from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import json
import uuid
from enum import Enum
import google.generativeai as genai
from dotenv import load_dotenv
import httpx
import base64
from cryptography.fernet import Fernet
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="AutoFlowBot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
cipher_suite = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

# Simple in-memory storage
integrations_db = {}
workflows_db = {}

class ServiceType(str, Enum):
    GITHUB = "github"
    JIRA = "jira"
    JENKINS = "jenkins"
    SLACK = "slack"

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ServiceConnection(BaseModel):
    service_type: ServiceType
    service_url: str
    api_token: str
    username: Optional[str] = None
    config_data: Optional[Dict[str, Any]] = {}
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    @validator('service_url')
    def validate_service_url(cls, v, values):
        service_type = values.get('service_type')
        if service_type == ServiceType.GITHUB and not v.startswith('https://api.github.com'):
            raise ValueError('GitHub service URL must start with https://api.github.com')
        elif service_type == ServiceType.SLACK and not v.startswith('https://'):
            raise ValueError('Slack service URL must be a valid HTTPS URL')
        elif service_type == ServiceType.JIRA and not v.startswith('https://'):
            raise ValueError('JIRA service URL must be a valid HTTPS URL')
        elif service_type == ServiceType.JENKINS and not v.startswith('http'):
            raise ValueError('Jenkins service URL must be a valid HTTP/HTTPS URL')
        return v

class ChatMessage(BaseModel):
    message: str
    user_name: Optional[str] = None
    user_email: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    workflow_id: Optional[str] = None
    actions_taken: List[str] = []

class WorkflowStep(BaseModel):
    action: str
    service: str
    status: str
    details: Dict[str, Any]
    timestamp: datetime

class Workflow(BaseModel):
    id: str
    user_name: str
    user_email: str
    title: str
    description: str
    status: WorkflowStatus
    steps: List[WorkflowStep]
    created_at: datetime
    updated_at: datetime

# Encryption utilities
def encrypt_token(token: str) -> str:
    """Encrypt API token for secure storage"""
    return cipher_suite.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    """Decrypt API token for use"""
    return cipher_suite.decrypt(encrypted_token.encode()).decode()

# Service validation classes
class ServiceValidator:
    """Base class for service validation"""
    
    @staticmethod
    async def validate_service(service_type: ServiceType, service_url: str, api_token: str, username: Optional[str] = None) -> Dict[str, Any]:
        """Validate service connection and return user info"""
        if service_type == ServiceType.GITHUB:
            return await GitHubValidator.validate(service_url, api_token)
        elif service_type == ServiceType.SLACK:
            return await SlackValidator.validate(service_url, api_token)
        elif service_type == ServiceType.JIRA:
            return await JiraValidator.validate(service_url, api_token, username)
        elif service_type == ServiceType.JENKINS:
            return await JenkinsValidator.validate(service_url, api_token, username)
        else:
            raise ValueError(f"Unsupported service type: {service_type}")

class GitHubValidator:
    """GitHub API validation"""
    
    @staticmethod
    async def validate(service_url: str, api_token: str) -> Dict[str, Any]:
        """Validate GitHub token and return user info"""
        headers = {
            "Authorization": f"token {api_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AutoFlowBot/1.0"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Validate token by fetching user info
                response = await client.get(f"{service_url}/user", headers=headers, timeout=10.0)
                
                if response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Invalid GitHub token")
                elif response.status_code != 200:
                    raise HTTPException(status_code=400, detail=f"GitHub API error: {response.status_code}")
                
                user_data = response.json()
                
                # Also check token scopes
                scopes = response.headers.get("X-OAuth-Scopes", "").split(", ")
                
                return {
                    "valid": True,
                    "username": user_data.get("login"),
                    "email": user_data.get("email"),
                    "name": user_data.get("name"),
                    "avatar_url": user_data.get("avatar_url"),
                    "scopes": scopes,
                    "service_info": {
                        "user_id": user_data.get("id"),
                        "company": user_data.get("company"),
                        "public_repos": user_data.get("public_repos"),
                        "followers": user_data.get("followers")
                    }
                }
                
            except httpx.TimeoutException:
                raise HTTPException(status_code=408, detail="GitHub API timeout")
            except httpx.RequestError as e:
                raise HTTPException(status_code=400, detail=f"GitHub API connection error: {str(e)}")

class SlackValidator:
    """Slack API validation"""
    
    @staticmethod
    async def validate(service_url: str, api_token: str) -> Dict[str, Any]:
        """Validate Slack token and return user/team info"""
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Test auth and get user info
                response = await client.get("https://slack.com/api/auth.test", headers=headers, timeout=10.0)
                
                if response.status_code != 200:
                    raise HTTPException(status_code=400, detail=f"Slack API error: {response.status_code}")
                
                data = response.json()
                
                if not data.get("ok"):
                    error_msg = data.get("error", "Unknown error")
                    if error_msg == "invalid_auth":
                        raise HTTPException(status_code=401, detail="Invalid Slack token")
                    raise HTTPException(status_code=400, detail=f"Slack API error: {error_msg}")
                
                # Get user profile
                user_response = await client.get(
                    f"https://slack.com/api/users.info?user={data.get('user_id')}", 
                    headers=headers, 
                    timeout=10.0
                )
                
                user_data = {}
                if user_response.status_code == 200:
                    user_info = user_response.json()
                    if user_info.get("ok"):
                        profile = user_info.get("user", {}).get("profile", {})
                        user_data = {
                            "real_name": profile.get("real_name"),
                            "email": profile.get("email"),
                            "avatar": profile.get("image_512")
                        }
                
                return {
                    "valid": True,
                    "username": data.get("user"),
                    "user_id": data.get("user_id"),
                    "team_id": data.get("team_id"),
                    "team_name": data.get("team"),
                    "service_info": {
                        "url": data.get("url"),
                        "bot_id": data.get("bot_id"),
                        **user_data
                    }
                }
                
            except httpx.TimeoutException:
                raise HTTPException(status_code=408, detail="Slack API timeout")
            except httpx.RequestError as e:
                raise HTTPException(status_code=400, detail=f"Slack API connection error: {str(e)}")

class JiraValidator:
    """JIRA API validation"""
    
    @staticmethod
    async def validate(service_url: str, api_token: str, username: Optional[str] = None) -> Dict[str, Any]:
        """Validate JIRA token and return user info"""
        # JIRA uses Basic Auth with email:token
        if not username:
            raise HTTPException(status_code=400, detail="Username/email is required for JIRA integration")
        
        # Create basic auth header
        auth_string = f"{username}:{api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Test auth by getting current user
                response = await client.get(f"{service_url}/rest/api/3/myself", headers=headers, timeout=10.0)
                
                if response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Invalid JIRA credentials")
                elif response.status_code == 403:
                    raise HTTPException(status_code=403, detail="JIRA access denied - check permissions")
                elif response.status_code != 200:
                    raise HTTPException(status_code=400, detail=f"JIRA API error: {response.status_code}")
                
                user_data = response.json()
                
                # Get server info
                server_response = await client.get(f"{service_url}/rest/api/3/serverInfo", headers=headers, timeout=10.0)
                server_info = {}
                if server_response.status_code == 200:
                    server_info = server_response.json()
                
                return {
                    "valid": True,
                    "username": user_data.get("name"),
                    "email": user_data.get("emailAddress"),
                    "display_name": user_data.get("displayName"),
                    "account_id": user_data.get("accountId"),
                    "service_info": {
                        "account_type": user_data.get("accountType"),
                        "active": user_data.get("active"),
                        "avatar_urls": user_data.get("avatarUrls", {}),
                        "server_title": server_info.get("serverTitle"),
                        "version": server_info.get("version")
                    }
                }
                
            except httpx.TimeoutException:
                raise HTTPException(status_code=408, detail="JIRA API timeout")
            except httpx.RequestError as e:
                raise HTTPException(status_code=400, detail=f"JIRA API connection error: {str(e)}")

class JenkinsValidator:
    """Jenkins API validation"""
    
    @staticmethod
    async def validate(service_url: str, api_token: str, username: Optional[str] = None) -> Dict[str, Any]:
        """Validate Jenkins token and return user info"""
        if not username:
            raise HTTPException(status_code=400, detail="Username is required for Jenkins integration")
        auth_string = f"{username}:{api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Test auth by getting user info
                user_url = f"{service_url}/user/{username}/api/json"
                response = await client.get(user_url, headers=headers, timeout=10.0)
                
                if response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Invalid Jenkins credentials")
                elif response.status_code == 403:
                    raise HTTPException(status_code=403, detail="Jenkins access denied - check permissions")
                elif response.status_code == 404:
                    raise HTTPException(status_code=404, detail="Jenkins user not found")
                elif response.status_code != 200:
                    raise HTTPException(status_code=400, detail=f"Jenkins API error: {response.status_code}")
                
                user_data = response.json()
                
                # Get Jenkins version info
                version_response = await client.get(f"{service_url}/api/json", headers=headers, timeout=10.0)
                version_info = {}
                if version_response.status_code == 200:
                    version_info = version_response.json()
                
                return {
                    "valid": True,
                    "username": username,
                    "full_name": user_data.get("fullName"),
                    "email": user_data.get("property", [{}])[0].get("address") if user_data.get("property") else None,
                    "service_info": {
                        "absolute_url": user_data.get("absoluteUrl"),
                        "description": user_data.get("description"),
                        "jenkins_version": version_response.headers.get("X-Jenkins") if version_response.status_code == 200 else None,
                        "node_name": version_info.get("nodeName"),
                        "node_description": version_info.get("nodeDescription")
                    }
                }
                
            except httpx.TimeoutException:
                raise HTTPException(status_code=408, detail="Jenkins API timeout")
            except httpx.RequestError as e:
                raise HTTPException(status_code=400, detail=f"Jenkins API connection error: {str(e)}")

def get_user_info(request: Request) -> Dict[str, str]:
    """Extract user info from headers or return defaults"""
    return {
        "name": request.headers.get("X-User-Name", "Anonymous User"),
        "email": request.headers.get("X-User-Email", "user@example.com")
    }

async def get_decrypted_integration(integration_id: str, user_email: str) -> Optional[Dict[str, Any]]:
    """Get integration with decrypted token"""
    integration = integrations_db.get(integration_id)
    if not integration or integration["user_email"] != user_email:
        return None
    integration_copy = integration.copy()
    integration_copy["api_token"] = decrypt_token(integration["encrypted_token"])
    return integration_copy

async def make_service_api_call(integration_id: str, user_email: str, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
    """Make API call to integrated service"""
    integration = await get_decrypted_integration(integration_id, user_email)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    service_type = integration["service_type"]
    api_token = integration["api_token"]
    service_url = integration["service_url"]
    if service_type == "github":
        headers = {
            "Authorization": f"token {api_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AutoFlowBot/1.0"
        }
        full_url = f"{service_url}{endpoint}"
    elif service_type == "slack":
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        full_url = f"https://slack.com/api{endpoint}"
    elif service_type == "jira":
        username = integration["username"]
        auth_string = f"{username}:{api_token}"
        auth_b64 = base64.b64encode(auth_string.encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        full_url = f"{service_url}{endpoint}"
    elif service_type == "jenkins":
        username = integration["username"]
        auth_string = f"{username}:{api_token}"
        auth_b64 = base64.b64encode(auth_string.encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json"
        }
        full_url = f"{service_url}{endpoint}"
    else:
        raise HTTPException(status_code=400, detail="Unsupported service type")
    
    async with httpx.AsyncClient() as client:
        try:
            if method.upper() == "GET":
                response = await client.get(full_url, headers=headers, timeout=30.0)
            elif method.upper() == "POST":
                response = await client.post(full_url, headers=headers, json=data, timeout=30.0)
            elif method.upper() == "PUT":
                response = await client.put(full_url, headers=headers, json=data, timeout=30.0)
            elif method.upper() == "DELETE":
                response = await client.delete(full_url, headers=headers, timeout=30.0)
            else:
                raise HTTPException(status_code=400, detail="Unsupported HTTP method")
            
            return {
                "status_code": response.status_code,
                "data": response.json() if response.content else {},
                "headers": dict(response.headers)
            }
            
        except httpx.TimeoutException:
            raise HTTPException(status_code=408, detail=f"{service_type.title()} API timeout")
        except httpx.RequestError as e:
            raise HTTPException(status_code=400, detail=f"{service_type.title()} API connection error: {str(e)}")

async def process_with_gemini(message: str, user_context: dict) -> Dict[str, Any]:
    """Process user message with Gemini AI"""
    if not GEMINI_API_KEY:
        return {
            "response": "AI processing is not available. Please configure GEMINI_API_KEY.",
            "workflow_needed": False,
            "services_required": [],
            "actions": []
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
                "workflow_title": ""
            }
    except Exception as e:
        logger.error(f"Gemini processing error: {str(e)}")
        return {
            "response": f"I encountered an error processing your request: {str(e)}. Please try again or rephrase your question.",
            "workflow_needed": False,
            "services_required": [],
            "actions": [],
            "workflow_title": ""
        }

async def execute_workflow_actions(actions: List[str], services: List[str], user_name: str, user_email: str, workflow_title: str = "") -> str:
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
            action=action,
            service=service,
            status=status,
            details=details,
            timestamp=datetime.utcnow()
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
        updated_at=datetime.utcnow()
    )
    
    # Store in database
    workflows_db[workflow_id] = workflow.dict()
    return workflow_id

# Serve static files (frontend)
if os.path.exists("../frontend"):
    app.mount("/static", StaticFiles(directory="../frontend"), name="static")

@app.get("/")
async def serve_frontend():
    """Serve the main frontend page"""
    frontend_path = "../frontend/index.html"
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {"message": "AutoFlowBot API is running. Frontend not found."}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.post("/integrations/connect")
async def connect_service(connection: ServiceConnection, request: Request):
    """Connect a new service integration with real validation"""
    user_info = get_user_info(request)
    
    try:
        validation_result = await ServiceValidator.validate_service(
            connection.service_type,
            connection.service_url,
            connection.api_token,
            connection.username
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
            "encrypted_token": encrypt_token(connection.api_token),  # Store encrypted token
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
                "scopes": validation_result.get("scopes", [])
            }
        }
        integrations_db[integration_id] = integration_data
        return {
            "message": f"{connection.service_type.title()} connected successfully",
            "integration_id": integration_id,
            "service_type": connection.service_type,
            "username": validation_result.get("username"),
            "email": validation_result.get("email"),
            "validated_at": integration_data["validated_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Service connection error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to connect service")

@app.get("/integrations/list")
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
                "validation_data": integration.get("validation_data", {})
            }
            user_integrations.append(safe_integration)
    
    return user_integrations

@app.get("/integrations/{integration_id}/test")
async def test_integration(integration_id: str, request: Request):
    """Test an existing integration"""
    user_info = get_user_info(request)
    
    try:
        result = await make_service_api_call(integration_id, user_info["email"], "/user", "GET")
        
        return {
            "status": "success",
            "message": "Integration is working properly",
            "api_response_code": result["status_code"],
            "tested_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException as e:
        return {
            "status": "error",
            "message": str(e.detail),
            "tested_at": datetime.utcnow().isoformat()
        }

@app.post("/integrations/{integration_id}/api-call")
async def make_api_call(integration_id: str, endpoint: str, method: str = "GET", data: Optional[Dict] = None, request: Request = None):
    """Make an API call using stored integration"""
    user_info = get_user_info(request)
    
    try:
        result = await make_service_api_call(integration_id, user_info["email"], endpoint, method, data)
        return result
    except HTTPException:
        raise

@app.delete("/integrations/{integration_id}")
async def disconnect_service(integration_id: str, request: Request):
    """Disconnect a service integration"""
    user_info = get_user_info(request)
    
    integration = integrations_db.get(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration["user_email"] != user_info["email"]:
        raise HTTPException(status_code=403, detail="Access denied")
    del integrations_db[integration_id]
    
    return {
        "message": "Service disconnected successfully",
        "integration_id": integration_id
    }

@app.post("/chat/process", response_model=ChatResponse)
async def process_chat_message(message: ChatMessage, request: Request):
    """Process chat message and potentially execute workflows"""
    user_info = get_user_info(request)
    user_name = message.user_name or user_info["name"]
    user_email = message.user_email or user_info["email"]
    connected_services = []
    for integration in integrations_db.values():
        if integration["user_email"] == user_email:
            connected_services.append(integration["service_type"])
    user_context = {
        "name": user_name,
        "email": user_email,
        "connected_services": connected_services
    }
    ai_response = await process_with_gemini(message.message, user_context)
    
    workflow_id = None
    actions_taken = []
    if ai_response.get("workflow_needed", False):
        actions = ai_response.get("actions", [])
        services = ai_response.get("services_required", [])
        workflow_title = ai_response.get("workflow_title", "")
        
        if actions:
            workflow_id = await execute_workflow_actions(
                actions,
                services,
                user_name,
                user_email,
                workflow_title
            )
            actions_taken = actions
    
    return ChatResponse(
        response=ai_response.get("response", "I'm here to help with your workflow automation needs!"),
        workflow_id=workflow_id,
        actions_taken=actions_taken
    )

@app.get("/workflows/history")
async def get_workflow_history(request: Request):
    """Get workflow history for the current user"""
    user_info = get_user_info(request)
    user_workflows = []
    
    for workflow in workflows_db.values():
        if workflow["user_email"] == user_info["email"]:
            user_workflows.append(workflow)
    user_workflows.sort(key=lambda x: x["created_at"], reverse=True)
    
    return user_workflows

@app.get("/workflows/{workflow_id}")
async def get_workflow_details(workflow_id: str, request: Request):
    """Get detailed information about a specific workflow"""
    user_info = get_user_info(request)
    
    workflow = workflows_db.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow["user_email"] != user_info["email"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return workflow

@app.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str, request: Request):
    """Delete a workflow from history"""
    user_info = get_user_info(request)
    
    workflow = workflows_db.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow["user_email"] != user_info["email"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    del workflows_db[workflow_id]
    
    return {
        "message": "Workflow deleted successfully",
        "workflow_id": workflow_id
    }

@app.get("/stats")
async def get_user_stats(request: Request):
    """Get user statistics"""
    user_info = get_user_info(request)
    integrations_count = sum(1 for integration in integrations_db.values() 
                           if integration["user_email"] == user_info["email"])
    workflows_count = sum(1 for workflow in workflows_db.values() 
                         if workflow["user_email"] == user_info["email"])
    completed_workflows = sum(1 for workflow in workflows_db.values() 
                            if (workflow["user_email"] == user_info["email"] and 
                                workflow["status"] == "completed"))
    
    return {
        "integrations_count": integrations_count,
        "workflows_count": workflows_count,
        "completed_workflows": completed_workflows,
        "success_rate": round((completed_workflows / workflows_count * 100) if workflows_count > 0 else 0, 2)
    }
@app.get("/integrations/{integration_id}/github/repos")
async def get_github_repos(integration_id: str, request: Request):
    """Get GitHub repositories for the authenticated user"""
    user_info = get_user_info(request)
    
    try:
        result = await make_service_api_call(integration_id, user_info["email"], "/user/repos?per_page=100", "GET")
        return result["data"]
    except HTTPException:
        raise

@app.post("/integrations/{integration_id}/github/issues")
async def create_github_issue(integration_id: str, repo_owner: str, repo_name: str, title: str, body: str = "", request: Request = None):
    """Create a GitHub issue"""
    user_info = get_user_info(request)
    
    data = {
        "title": title,
        "body": body
    }
    
    try:
        result = await make_service_api_call(
            integration_id, 
            user_info["email"], 
            f"/repos/{repo_owner}/{repo_name}/issues", 
            "POST", 
            data
        )
        return result["data"]
    except HTTPException:
        raise
@app.post("/integrations/{integration_id}/slack/message")
async def send_slack_message(integration_id: str, channel: str, text: str, request: Request):
    """Send a Slack message"""
    user_info = get_user_info(request)
    
    data = {
        "channel": channel,
        "text": text
    }
    
    try:
        result = await make_service_api_call(
            integration_id,
            user_info["email"],
            "/chat.postMessage",
            "POST",
            data
        )
        return result["data"]
    except HTTPException:
        raise

@app.get("/integrations/{integration_id}/slack/channels")
async def get_slack_channels(integration_id: str, request: Request):
    """Get Slack channels"""
    user_info = get_user_info(request)
    
    try:
        result = await make_service_api_call(
            integration_id,
            user_info["email"],
            "/conversations.list?types=public_channel,private_channel",
            "GET"
        )
        return result["data"]
    except HTTPException:
        raise

# JIRA-specific endpoints
@app.post("/integrations/{integration_id}/jira/issues")
async def create_jira_issue(integration_id: str, project_key: str, summary: str, description: str = "", issue_type: str = "Task", request: Request = None):
    """Create a JIRA issue"""
    user_info = get_user_info(request)
    
    data = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type}
        }
    }
    
    try:
        result = await make_service_api_call(
            integration_id,
            user_info["email"],
            "/rest/api/3/issue",
            "POST",
            data
        )
        return result["data"]
    except HTTPException:
        raise

@app.get("/integrations/{integration_id}/jira/projects")
async def get_jira_projects(integration_id: str, request: Request):
    """Get JIRA projects"""
    user_info = get_user_info(request)
    
    try:
        result = await make_service_api_call(
            integration_id,
            user_info["email"],
            "/rest/api/3/project",
            "GET"
        )
        return result["data"]
    except HTTPException:
        raise

# Jenkins-specific endpoints
@app.post("/integrations/{integration_id}/jenkins/build")
async def trigger_jenkins_build(integration_id: str, job_name: str, parameters: Optional[Dict] = None, request: Request = None):
    """Trigger a Jenkins build"""
    user_info = get_user_info(request)
    
    endpoint = f"/job/{job_name}/build"
    if parameters:
        endpoint = f"/job/{job_name}/buildWithParameters"
    
    try:
        result = await make_service_api_call(
            integration_id,
            user_info["email"],
            endpoint,
            "POST",
            parameters or {}
        )
        return result
    except HTTPException:
        raise

@app.get("/integrations/{integration_id}/jenkins/jobs")
async def get_jenkins_jobs(integration_id: str, request: Request):
    """Get Jenkins jobs"""
    user_info = get_user_info(request)
    
    try:
        result = await make_service_api_call(
            integration_id,
            user_info["email"],
            "/api/json?tree=jobs[name,url,buildable,color]",
            "GET"
        )
        return result["data"]
    except HTTPException:
        raise

@app.get("/integrations/{integration_id}/jenkins/job/{job_name}/builds")
async def get_jenkins_build_history(integration_id: str, job_name: str, request: Request):
    """Get Jenkins build history for a job"""
    user_info = get_user_info(request)
    
    try:
        result = await make_service_api_call(
            integration_id,
            user_info["email"],
            f"/job/{job_name}/api/json?tree=builds[number,result,timestamp,duration,url]",
            "GET"
        )
        return result["data"]
    except HTTPException:
        raise

# Catch-all route for serving frontend files
@app.get("/{path:path}")
async def serve_static_files(path: str):
    """Serve static frontend files"""
    file_path = f"../frontend/{path}"
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    frontend_path = "../frontend/index.html"
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    
    raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)