from typing import Any, Dict

import httpx
from fastapi import HTTPException


class SlackValidator:
    """Slack API validation"""

    @staticmethod
    async def validate(service_url: str, api_token: str) -> Dict[str, Any]:
        """Validate Slack token and return user/team info"""
        headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}

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
                    f"https://slack.com/api/users.info?user={data.get('user_id')}", headers=headers, timeout=10.0
                )

                user_data = {}
                if user_response.status_code == 200:
                    user_info = user_response.json()
                    if user_info.get("ok"):
                        profile = user_info.get("user", {}).get("profile", {})
                        user_data = {
                            "real_name": profile.get("real_name"),
                            "email": profile.get("email"),
                            "avatar": profile.get("image_512"),
                        }

                return {
                    "valid": True,
                    "username": data.get("user"),
                    "user_id": data.get("user_id"),
                    "team_id": data.get("team_id"),
                    "team_name": data.get("team"),
                    "service_info": {"url": data.get("url"), "bot_id": data.get("bot_id"), **user_data},
                }

            except httpx.TimeoutException:
                raise HTTPException(status_code=408, detail="Slack API timeout")
            except httpx.RequestError as e:
                raise HTTPException(status_code=400, detail=f"Slack API connection error: {str(e)}")
