from enum import Enum


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
