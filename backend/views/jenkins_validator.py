import base64
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException


class JenkinsValidator:
    """Jenkins API validation"""

    @staticmethod
    async def validate(service_url: str, api_token: str, username: Optional[str] = None) -> Dict[str, Any]:
        """Validate Jenkins token and return user info"""
        if not username:
            raise HTTPException(status_code=400, detail="Username is required for Jenkins integration")
        auth_string = f"{username}:{api_token}"
        auth_bytes = auth_string.encode("ascii")
        auth_b64 = base64.b64encode(auth_bytes).decode("ascii")

        headers = {"Authorization": f"Basic {auth_b64}", "Accept": "application/json"}

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
                        "jenkins_version": (
                            version_response.headers.get("X-Jenkins") if version_response.status_code == 200 else None
                        ),
                        "node_name": version_info.get("nodeName"),
                        "node_description": version_info.get("nodeDescription"),
                    },
                }

            except httpx.TimeoutException:
                raise HTTPException(status_code=408, detail="Jenkins API timeout")
            except httpx.RequestError as e:
                raise HTTPException(status_code=400, detail=f"Jenkins API connection error: {str(e)}")
