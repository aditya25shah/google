import base64
from typing import Any, Dict, Optional

import httpx
from core.security import get_decrypted_integration
from fastapi import HTTPException


async def make_service_api_call(
    integration_id: str, user_email: str, endpoint: str, method: str = "GET", data: Optional[Dict] = None
) -> Dict[str, Any]:
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
            "User-Agent": "AutoFlowBot/1.0",
        }
        full_url = f"{service_url}{endpoint}"
    elif service_type == "slack":
        headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
        full_url = f"https://slack.com/api{endpoint}"
    elif service_type == "jira":
        username = integration["username"]
        auth_string = f"{username}:{api_token}"
        auth_b64 = base64.b64encode(auth_string.encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        full_url = f"{service_url}{endpoint}"
    elif service_type == "jenkins":
        username = integration["username"]
        auth_string = f"{username}:{api_token}"
        auth_b64 = base64.b64encode(auth_string.encode()).decode()
        headers = {"Authorization": f"Basic {auth_b64}", "Accept": "application/json"}
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
                "headers": dict(response.headers),
            }

        except httpx.TimeoutException:
            raise HTTPException(status_code=408, detail=f"{service_type.title()} API timeout")
        except httpx.RequestError as e:
            raise HTTPException(status_code=400, detail=f"{service_type.title()} API connection error: {str(e)}")
