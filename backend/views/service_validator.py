from typing import Any, Dict, Optional

from .enums import ServiceType
from .github_validator import GitHubValidator
from .jenkins_validator import JenkinsValidator
from .jira_validator import JiraValidator
from .slack_validator import SlackValidator


# Service validation classes
class ServiceValidator:
    """Base class for service validation"""

    @staticmethod
    async def validate_service(
        service_type: ServiceType, service_url: str, api_token: str, username: Optional[str] = None
    ) -> Dict[str, Any]:
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
