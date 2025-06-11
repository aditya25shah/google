from typing import Any, Dict, Optional

from pydantic import BaseModel, validator

from .enums import ServiceType


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