import base64
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException


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
        auth_bytes = auth_string.encode("ascii")
        auth_b64 = base64.b64encode(auth_bytes).decode("ascii")

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json",
            "Content-Type": "application/json",
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
                server_response = await client.get(
                    f"{service_url}/rest/api/3/serverInfo", headers=headers, timeout=10.0
                )
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
                        "version": server_info.get("version"),
                    },
                }

            except httpx.TimeoutException:
                raise HTTPException(status_code=408, detail="JIRA API timeout")
            except httpx.RequestError as e:
                raise HTTPException(status_code=400, detail=f"JIRA API connection error: {str(e)}")
