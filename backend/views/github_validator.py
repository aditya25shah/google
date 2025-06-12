from typing import Any, Dict

import httpx
from fastapi import HTTPException


class GitHubValidator:
    """GitHub API validation"""

    @staticmethod
    async def validate(service_url: str, api_token: str) -> Dict[str, Any]:
        """Validate GitHub token and return user info"""
        headers = {
            "Authorization": f"token {api_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AutoFlowBot/1.0",
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
                        "followers": user_data.get("followers"),
                    },
                }

            except httpx.TimeoutException:
                raise HTTPException(status_code=408, detail="GitHub API timeout")
            except httpx.RequestError as e:
                raise HTTPException(status_code=400, detail=f"GitHub API connection error: {str(e)}")
