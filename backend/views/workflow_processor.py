import json
from typing import Any, Dict, Optional, TypedDict, Union, List
import httpx
import google.generativeai as genai
import requests  # type: ignore
from langgraph.graph import END, START, StateGraph
import re
# Set up Gemini API
# TODO: Move API keys to environment variables or a secure configuration manager.


# Define the state for our graph
class WorkflowState(TypedDict):
    user_query: str
    action_type: Optional[str]  # e.g., "github_create_issue", "slack_send_message", "compound_action"
    repo_name: Optional[str]
    issue_number: Optional[int]
    comment_body: Optional[str]
    issue_title: Optional[str]  # For creating issues
    issue_body: Optional[str]  # For creating issues
    api_response: Union[Dict[str, Any], None]  # To store the response from GitHub/Slack API calls
    error_message: Optional[str]  # FIXED: Only one error_message field
    branch_name: Optional[str]  # For future use, e.g., for GitHub branches
    branch_list: Optional[Dict[str, Any]]  # For storing branch details if needed
    source_branch: Optional[str]  # For branch operations
    slack_message: Optional[str]  # For Slack messages
    slack_channel: Optional[str]  # For Slack channel
    slack_user: Optional[str]  # For Slack user
    compound_actions: Optional[List[str]]  
    primary_response: Optional[Dict[str, Any]]  
    secondary_responses: Optional[List[Dict[str, Any]]] 

class WorkflowProcessor:
    def __init__(self, gemini_api_key: str, github_token: str, slack_token: str, github_owner: str):
        # TODO: Make GitHub owner dynamic instead of hardcoded.
        self.github_token = github_token
        self.slack_token = slack_token
        self.github_owner = github_owner

        if not gemini_api_key:
            raise ValueError("Gemini API key is required.")
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

        self.app = self._build_graph()

    # --- GitHub API Helper Functions ---
    def _call_list_github_branches(self, repo_name: str) -> Dict[str, Any]:
        """Lists all branches for a GitHub repository."""
        if not repo_name:
            return {"error": "Repository name not provided"}
        url = f"https://api.github.com/repos/{self.github_owner}/{repo_name}/branches"
        headers = {"Authorization": f"token {self.github_token}"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": f"GitHub API Error: {response.status_code}", "details": response.text}
        return response.json()

    def _call_get_github_branch(self, repo_name: str, branch_name: str) -> Dict[str, Any]:
        """Gets details for a specific GitHub branch."""
        if not repo_name or not branch_name:
            return {"error": "Repository name or branch name not provided"}
        url = f"https://api.github.com/repos/{self.github_owner}/{repo_name}/branches/{branch_name}"
        headers = {"Authorization": f"token {self.github_token}"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": f"GitHub API Error: {response.status_code}", "details": response.text}
        return response.json()

    def _call_create_github_branch(
        self, repo_name: str, branch_name: str, source_branch: str = "main"
    ) -> Dict[str, Any]:
        """Creates a new branch from a source branch."""
        if not repo_name or not branch_name:
            return {"error": "Repository name or branch name not provided"}

        # First, get the SHA of the source branch
        source_url = f"https://api.github.com/repos/{self.github_owner}/{repo_name}/git/refs/heads/{source_branch}"
        headers = {"Authorization": f"token {self.github_token}"}
        source_response = requests.get(source_url, headers=headers)

        if source_response.status_code != 200:
            return {"error": f"Could not find source branch '{source_branch}'", "details": source_response.text}

        source_sha = source_response.json()["object"]["sha"]

        # Create the new branch
        create_url = f"https://api.github.com/repos/{self.github_owner}/{repo_name}/git/refs"
        create_data = {"ref": f"refs/heads/{branch_name}", "sha": source_sha}
        create_response = requests.post(create_url, json=create_data, headers=headers)

        if create_response.status_code not in [200, 201]:
            return {"error": f"GitHub API Error: {create_response.status_code}", "details": create_response.text}
        return create_response.json()

    def _call_create_github_issue(self, repo_name: str, title: str, body: str) -> Dict[str, Any]:
        """Creates a GitHub issue dynamically based on user query."""
        if not repo_name:
            return {"error": "Repository name not found in query"}
        if not title:
            return {"error": "Issue title not provided"}

        url = f"https://api.github.com/repos/{self.github_owner}/{repo_name}/issues"
        headers = {"Authorization": f"token {self.github_token}"}
        data = {"title": title, "body": body or f"Issue created via AutoFlowBot based on user query."}
        print(f"DEBUG: Creating GitHub issue: URL={url}, Data={data}")
        response = requests.post(url, json=data, headers=headers)
        if response.status_code not in [200, 201]:
            print(f"DEBUG: GitHub API Error: {response.status_code} - {response.text}")
            return {"error": f"GitHub API Error: {response.status_code}", "details": response.text}
        return response.json()

    
    def _call_send_slack_message(self, message: str, channel: str = "#general", user: str = None) -> Dict[str, Any]:
        """Sends a message to a Slack channel or user."""
        
        # DEBUG: Print what we're receiving
        print(f"DEBUG - Message: '{message}'")
        print(f"DEBUG - Channel: '{channel}'")
        print(f"DEBUG - User: '{user}'")
        
        headers = {
            "Authorization": f"Bearer {self.slack_token}",
            "Content-Type": "application/json"
        }
        
        try:
            with httpx.Client(timeout=10.0) as client:
                if user:
                    # Send DM to user
                    users_response = client.get("https://slack.com/api/users.list", headers=headers)
                    
                    if users_response.status_code != 200:
                        return {"ok": False, "error": f"HTTP error {users_response.status_code} when listing users"}
                    
                    users_data = users_response.json()
                    
                    if not users_data.get("ok"):
                        error_msg = users_data.get("error", "Unknown error")
                        if error_msg == "invalid_auth":
                            return {"ok": False, "error": "Invalid Slack token"}
                        return {"ok": False, "error": f"Could not list users: {error_msg}"}
                    
                    # Find user ID
                    user_id = None
                    for member in users_data.get("members", []):
                        if (member.get("name") == user or 
                            member.get("profile", {}).get("display_name") == user or
                            member.get("real_name") == user):
                            user_id = member.get("id")
                            break
                    
                    if not user_id:
                        return {"ok": False, "error": f"User '{user}' not found"}
                    
                    # Open DM conversation
                    dm_response = client.post(
                        "https://slack.com/api/conversations.open",
                        json={"users": user_id},
                        headers=headers
                    )
                    
                    if dm_response.status_code != 200:
                        return {"ok": False, "error": f"HTTP error {dm_response.status_code} when opening DM"}
                    
                    dm_result = dm_response.json()
                    
                    if not dm_result.get("ok"):
                        error_msg = dm_result.get("error", "Unknown error")
                        return {"ok": False, "error": f"Could not open DM: {error_msg}"}
                    
                    channel_id = dm_result.get("channel", {}).get("id")
                    
                else:
                    # Send to channel - get channel ID
                    channel_name = channel.lstrip("#")
                    print(f"DEBUG - Processed channel name: '{channel_name}'")
                    
                    # Try public channels first
                    channels_response = client.get("https://slack.com/api/conversations.list", headers=headers)
                    
                    if channels_response.status_code != 200:
                        return {"ok": False, "error": f"HTTP error {channels_response.status_code} when listing channels"}
                    
                    channels_data = channels_response.json()
                    
                    if not channels_data.get("ok"):
                        error_msg = channels_data.get("error", "Unknown error")
                        if error_msg == "invalid_auth":
                            return {"ok": False, "error": "Invalid Slack token"}
                        return {"ok": False, "error": f"Could not list channels: {error_msg}"}
                    
                    # Find channel ID in public channels
                    channel_id = None
                    for ch in channels_data.get("channels", []):
                        if ch.get("name") == channel_name:
                            channel_id = ch.get("id")
                            break
                    
                    # If not found in public channels, try private channels
                    if not channel_id:
                        private_channels_response = client.get(
                            "https://slack.com/api/conversations.list",
                            headers=headers,
                            params={"types": "private_channel"}
                        )
                        
                        if private_channels_response.status_code == 200:
                            private_data = private_channels_response.json()
                            if private_data.get("ok"):
                                for ch in private_data.get("channels", []):
                                    if ch.get("name") == channel_name:
                                        channel_id = ch.get("id")
                                        break
                    
                    if not channel_id:
                        return {"ok": False, "error": f"Channel '{channel_name}' not found. Bot may not be added to this channel."}
                
                # Send message
                print(f"DEBUG - Final channel_id: '{channel_id}'")
                print(f"DEBUG - Final message: '{message}'")
                
                message_data = {
                    "channel": channel_id,
                    "text": message
                }
                
                message_response = client.post(
                    "https://slack.com/api/chat.postMessage",
                    json=message_data,
                    headers=headers
                )
                
                if message_response.status_code != 200:
                    return {"ok": False, "error": f"HTTP error {message_response.status_code} when sending message"}
                
                result = message_response.json()
                
                if not result.get("ok"):
                    error_msg = result.get("error", "Unknown error")
                    if error_msg == "invalid_auth":
                        return {"ok": False, "error": "Invalid Slack token"}
                    elif error_msg == "channel_not_found":
                        return {"ok": False, "error": f"Channel not found or bot not added to channel"}
                    elif error_msg == "not_in_channel":
                        return {"ok": False, "error": f"Bot is not a member of the channel"}
                    return {"ok": False, "error": f"Could not send message: {error_msg}"}
                
                return result
                
        except httpx.TimeoutException:
            return {"ok": False, "error": "Slack API timeout"}
        except httpx.RequestError as e:
            return {"ok": False, "error": f"Slack API connection error: {str(e)}"}
        except Exception as e:
            return {"ok": False, "error": f"Unexpected error: {str(e)}"}


    def _call_list_github_issues(self, repo_name: str) -> Dict[str, Any]:
        """Lists issues for a given GitHub repository."""
        if not repo_name:
            return {"error": "Repository name not provided"}
        url = f"https://api.github.com/repos/{self.github_owner}/{repo_name}/issues"
        headers = {"Authorization": f"token {self.github_token}"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": f"GitHub API Error: {response.status_code}", "details": response.text}
        return response.json()

    def _call_get_github_issue(self, repo_name: str, issue_number: int) -> Dict[str, Any]:
        """Gets details for a specific GitHub issue."""
        if not repo_name or not issue_number:
            return {"error": "Repository name or issue number not provided"}
        url = f"https://api.github.com/repos/{self.github_owner}/{repo_name}/issues/{issue_number}"
        headers = {"Authorization": f"token {self.github_token}"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": f"GitHub API Error: {response.status_code}", "details": response.text}
        return response.json()

    def _call_comment_on_github_issue(self, repo_name: str, issue_number: int, comment_body: str) -> Dict[str, Any]:
        """Adds a comment to a specific GitHub issue."""
        if not repo_name or not issue_number or not comment_body:
            return {"error": "Repository name, issue number, or comment body not provided"}
        url = f"https://api.github.com/repos/{self.github_owner}/{repo_name}/issues/{issue_number}/comments"
        headers = {"Authorization": f"token {self.github_token}"}
        data = {"body": comment_body}
        response = requests.post(url, json=data, headers=headers)
        if response.status_code not in [200, 201]:
            return {"error": f"GitHub API Error: {response.status_code}", "details": response.text}
        return response.json()

    # --- LangGraph Node Functions ---
    def _classify_and_extract_parameters_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Uses Gemini API to classify the query and extract parameters with improved NLP."""
        print("--- Classifying Query and Extracting Parameters ---")
        user_query = state["user_query"]

        # Enhanced prompt with better natural language understanding
        prompt = f"""
        You are DevCascade, a smart assistant that understands user requests for DevOps automation.

        User said: "{user_query}"

IMPORTANT: When users want to create an issue, they might describe:
1. The PROBLEM/BUG they want to report (extract this as the issue content)
2. WHERE to create it (repository name)

Examples:
- "raise an issue in repo gc-adi about login bug" → Issue about login bug in gc-adi repo
- "create issue in backend: API is returning 500 errors" → Issue about API errors in backend repo
- "report bug in frontend that buttons don't work" → Issue about button bug in frontend repo

BRANCH OPERATIONS:
- "list branches in repo X" → List all branches in repository X
- "show branch feature-login in repo X" → Get details for specific branch
- "create branch hotfix-123 from main in repo X" → Create new branch from source
- "what branches exist in repo X" → List all branches

For CREATE ISSUE requests, identify:
- WHAT is the actual problem/issue to report (not the command itself)
- WHERE to create it (repository)

If the user just says "raise an issue in repo X" without specifying WHAT issue, ask them what problem they want to report.

Respond in this exact format:
ACTION: [github_create_issue, github_list_issues, github_get_issue, github_comment_issue, github_list_branches, github_get_branch, github_create_branch, slack_send_message, general_response, unhandled]
REPO: [repository name or null]
ISSUE_NUMBER: [issue number or null]
ISSUE_TITLE: [short title describing the actual problem, not the command]
ISSUE_BODY: [detailed description of the problem, not the user's command]
COMMENT: [comment text if adding comment, or null]
MESSAGE: [message text for slack, or null]
BRANCH_NAME: [branch name for branch operations, or null]
SOURCE_BRANCH: [source branch for creating new branch, or null]
CLARIFICATION_NEEDED: [yes if user needs to specify what issue to create, or no]
"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            print(f"Gemini Classification Response: {response_text}")

            # Parse the structured response
            parsed_data = self._parse_structured_response(response_text)

            # Add some fallback logic for common cases
            if parsed_data["action_type"] == "unhandled":
                parsed_data = self._fallback_classification(user_query)

            return parsed_data

        except Exception as e:
            print(f"Error during classification/extraction: {e}")
            # Fallback to simple pattern matching
            return self._fallback_classification(user_query)

    def _needs_clarification_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Handle cases where user intent needs clarification"""
        print("--- Requesting Clarification ---")
        repo_name = state.get("repo_name", "the repository")

        return {
            "api_response": {
                "message": f"I understand you want to create an issue in {repo_name}. What specific problem or feature would you like to report?",
                "type": "clarification_request",
                "context": "issue_creation",
            }
        }

    def _general_response_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Handle general conversation using Gemini"""
        print("--- Executing General Response Node ---")
        user_query = state["user_query"]

        prompt = f"""
        You are DevCascade, a friendly DevOps assistant. The user said: "{user_query}"
    
        Respond naturally and helpfully. If it's a greeting, be warm. If it's a question, answer it well.
        If relevant, you can mention your automation capabilities, but don't force it.
    
        Keep your response conversational and engaging.
        """

        try:
            response = self.model.generate_content(prompt)
            return {"api_response": {"message": response.text.strip(), "type": "general_conversation"}}
        except Exception as e:
            return {
                "api_response": {
                    "message": "Hello! I'm DevCascade, your DevOps automation assistant. How can I help you today?",
                    "type": "general_conversation",
                }
            }

    def _parse_structured_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the structured response from Gemini"""
        lines = response_text.split("\n")
        parsed = {
            "action_type": "unhandled",
            "repo_name": None,
            "issue_number": None,
            "comment_body": None,
            "issue_title": None,
            "issue_body": None,
            "error_message": None,
            "needs_clarification": False,
        }

        for line in lines:
            line = line.strip()
            if line.startswith("ACTION:"):
                action = line.split(":", 1)[1].strip()
                parsed["action_type"] = action
            elif line.startswith("REPO:"):
                repo = line.split(":", 1)[1].strip()
                parsed["repo_name"] = repo if repo.lower() != "null" else None
            elif line.startswith("ISSUE_NUMBER:"):
                issue_num = line.split(":", 1)[1].strip()
                if issue_num.lower() != "null":
                    try:
                        parsed["issue_number"] = int(issue_num)
                    except ValueError:
                        pass
            elif line.startswith("ISSUE_TITLE:"):
                title = line.split(":", 1)[1].strip()
                parsed["issue_title"] = title if title.lower() != "null" else None
            elif line.startswith("ISSUE_BODY:"):
                body = line.split(":", 1)[1].strip()
                parsed["issue_body"] = body if body.lower() != "null" else None
            elif line.startswith("BRANCH_NAME:"):
                branch = line.split(":", 1)[1].strip()
                parsed["branch_name"] = branch if branch.lower() != "null" else None
            elif line.startswith("SOURCE_BRANCH:"):
                source = line.split(":", 1)[1].strip()
                parsed["source_branch"] = source if source.lower() != "null" else None

            elif line.startswith("COMMENT:"):
                comment = line.split(":", 1)[1].strip()
                parsed["comment_body"] = comment if comment.lower() != "null" else None

        return parsed

    def _fallback_classification(self, user_query: str) -> Dict[str, Any]:
        """Fallback classification using simple pattern matching"""
        query_lower = user_query.lower().strip()

        # Check for conversational/greeting patterns first
        greeting_patterns = [
            "hello",
            "hi",
            "hey",
            "howdy",
            "greetings",
            "good morning",
            "good afternoon",
            "good evening",
        ]
        question_patterns = ["how are you", "what can you do", "help", "what is", "tell me about", "explain"]

        # Check if it's a greeting or general conversation
        if any(greeting in query_lower for greeting in greeting_patterns):
            return {
                "action_type": "general_response",
                "repo_name": None,
                "issue_number": None,
                "comment_body": None,
                "issue_title": None,
                "issue_body": None,
                "error_message": None,
            }

        # Check if it's a general question
        if any(question in query_lower for question in question_patterns):
            return {
                "action_type": "general_response",
                "repo_name": None,
                "issue_number": None,
                "comment_body": None,
                "issue_title": None,
                "issue_body": None,
                "error_message": None,
            }
        create_patterns = ["create", "raise", "open", "make", "new", "add"]
        issue_patterns = ["issue", "bug", "ticket", "problem", "feature"]
        list_patterns = ["list", "show", "see", "view", "display", "get all", "what are"]
        slack_patterns = ["send", "message", "notify", "tell", "slack", "inform"]
        branch_patterns = ["branch", "branches"]
        list_branch_patterns = ["list", "show", "see", "view", "display", "get all", "what"]
        create_branch_patterns = ["create", "make", "new", "add"]
        repo_name = self._extract_repo_name(user_query)
        issue_number = self._extract_issue_number(user_query)
        if any(create in query_lower for create in create_patterns) and any(
            issue in query_lower for issue in issue_patterns
        ):
            # Try to extract the actual issue content
            issue_content = self._extract_issue_content(user_query)

            if not issue_content:
                # User didn't specify what issue to create - need clarification
                return {
                    "action_type": "needs_clarification",
                    "repo_name": repo_name,
                    "issue_number": None,
                    "comment_body": None,
                    "issue_title": None,
                    "issue_body": None,
                    "error_message": None,
                    "needs_clarification": True,
                }

            # User specified what issue to create
            return {
                "action_type": "github_create_issue",
                "repo_name": repo_name,
                "issue_number": None,
                "comment_body": None,
                "issue_title": issue_content["title"],
                "issue_body": issue_content["body"],
                "error_message": None,
            }
        elif any(list_word in query_lower for list_word in list_patterns) and any(
            issue in query_lower for issue in issue_patterns
        ):
            return {
                "action_type": "github_list_issues",
                "repo_name": repo_name,
                "issue_number": None,
                "comment_body": None,
                "issue_title": None,
                "issue_body": None,
                "error_message": None,
            }
        elif issue_number and ("show" in query_lower or "get" in query_lower or "details" in query_lower):
            return {
                "action_type": "github_get_issue",
                "repo_name": repo_name,
                "issue_number": issue_number,
                "comment_body": None,
                "issue_title": None,
                "issue_body": None,
                "error_message": None,
            }
        elif issue_number and ("comment" in query_lower or "reply" in query_lower):
            return {
                "action_type": "github_comment_issue",
                "repo_name": repo_name,
                "issue_number": issue_number,
                "comment_body": user_query,
                "issue_title": None,
                "issue_body": None,
                "error_message": None,
            }
        elif any(slack in query_lower for slack in slack_patterns):
            return {
                "action_type": "slack_send_message",
                "repo_name": None,
                "issue_number": None,
                "comment_body": None,
                "issue_title": None,
                "issue_body": None,
                "error_message": None,
            }
        elif any(branch in query_lower for branch in branch_patterns):
            branch_name = self._extract_branch_name(user_query)

            if any(create in query_lower for create in create_branch_patterns):
                source_branch = self._extract_source_branch(user_query)
                return {
                    "action_type": "github_create_branch",
                    "repo_name": repo_name,
                    "branch_name": branch_name,
                    "source_branch": source_branch or "main",
                    "issue_number": None,
                    "comment_body": None,
                    "issue_title": None,
                    "issue_body": None,
                    "error_message": None,
                }
            elif any(list_word in query_lower for list_word in list_branch_patterns):
                return {
                    "action_type": "github_list_branches",
                    "repo_name": repo_name,
                    "branch_name": None,
                    "source_branch": None,
                    "issue_number": None,
                    "comment_body": None,
                    "issue_title": None,
                    "issue_body": None,
                    "error_message": None,
                }
            elif branch_name:
                return {
                    "action_type": "github_get_branch",
                    "repo_name": repo_name,
                    "branch_name": branch_name,
                    "source_branch": None,
                    "issue_number": None,
                    "comment_body": None,
                    "issue_title": None,
                    "issue_body": None,
                    "error_message": None,
                }
        # If nothing matches, it's probably a general conversation
        return {
            "action_type": "general_response",
            "repo_name": repo_name,
            "issue_number": issue_number,
            "comment_body": None,
            "issue_title": None,
            "issue_body": None,
            "error_message": None,
        }

    def _extract_issue_content(self, query: str) -> Dict[str, str]:
        """Extract actual issue content from user query"""
        # Patterns to identify issue content
        content_patterns = [
            r"about\s+(.+?)(?:\s+in\s+|\s*$)",  # "about login bug"
            r":\s*(.+?)(?:\s+in\s+|\s*$)",  # ": API is broken"
            r"that\s+(.+?)(?:\s+in\s+|\s*$)",  # "that buttons don't work"
            r"with\s+(.+?)(?:\s+in\s+|\s*$)",  # "with connection issues"
        ]

        for pattern in content_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                # Create title and body from extracted content
                title = content[:50] + "..." if len(content) > 50 else content
                body = f"Issue details: {content}\n\nReported via DevCascade automation."
                return {"title": title, "body": body}

        return None  # No content found

    def _extract_repo_name(self, query: str) -> str:
        """Extract repository name from query using patterns"""
        import re

        # Pattern 1: "repo xyz", "repository abc", "project def"
        patterns = [
            r"(?:repo|repository|project)\s+([a-zA-Z0-9_-]+)",
            r"(?:in|to|for)\s+(?:the\s+)?([a-zA-Z0-9_-]+)(?:\s+repo|\s+repository|\s+project)?",
            r"([a-zA-Z0-9_-]+)(?:\s+repo|\s+repository|\s+project)",
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_issue_number(self, query: str) -> int:
        """Extract issue number from query"""
        import re

        # Pattern for issue numbers: "issue 123", "#45", "bug 67"
        patterns = [
            r"(?:issue|bug|ticket)\s+#?(\d+)",
            r"#(\d+)",
            r"(?:number|num)\s+(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue

        return None

    def _extract_branch_name(self, query: str) -> str:
        """Extract branch name from query using patterns"""
        import re

        patterns = [
            r"branch\s+([a-zA-Z0-9_/-]+)",
            r"on\s+([a-zA-Z0-9_/-]+)\s+branch",
            r"switch\s+to\s+([a-zA-Z0-9_/-]+)",
            r"checkout\s+([a-zA-Z0-9_/-]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_source_branch(self, query: str) -> str:
        """Extract source branch name from query"""
        import re

        patterns = [
            r"from\s+([a-zA-Z0-9_/-]+)",
            r"based\s+on\s+([a-zA-Z0-9_/-]+)",
            r"off\s+([a-zA-Z0-9_/-]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_branch_name(self, query: str) -> str:
        """Extract branch name from query"""
        patterns = [r"branch\s+([a-zA-Z0-9_/-]+)", r"on\s+([a-zA-Z0-9_/-]+)\s+branch", r"from\s+([a-zA-Z0-9_/-]+)"]

    # ...pattern matching logic
    def _create_issue_node(self, state: WorkflowState) -> Dict[str, Any]:
        print("--- Executing GitHub Create Issue Node ---")
        repo_name = state.get("repo_name")
        title = state.get("issue_title") or f"Issue from query: {state['user_query'][:50]}..."
        body = state.get("issue_body") or f"Details based on user query: {state['user_query']}"

        if not repo_name:
            return {
                "api_response": {"error": "Repository name not extracted for creating issue."},
                "error_message": "Repo name missing",
            }

        response = self._call_create_github_issue(repo_name, title, body)
        print(f"GitHub API Response: {response}")
        return {"api_response": response}

    def _list_issues_node(self, state: WorkflowState) -> Dict[str, Any]:
        print("--- Executing GitHub List Issues Node ---")
        repo_name = state.get("repo_name")
        if not repo_name:
            return {
                "api_response": {"error": "Repository name not extracted for listing issues."},
                "error_message": "Repo name missing",
            }
        response = self._call_list_github_issues(repo_name)
        print(f"GitHub API Response: {response}")
        return {"api_response": response}

    def _get_issue_node(self, state: WorkflowState) -> Dict[str, Any]:
        print("--- Executing GitHub Get Issue Node ---")
        repo_name = state.get("repo_name")
        issue_number = state.get("issue_number")
        if not repo_name or not issue_number:
            return {
                "api_response": {"error": "Repo name or issue number not extracted."},
                "error_message": "Repo/Issue num missing",
            }
        response = self._call_get_github_issue(repo_name, issue_number)
        print(f"GitHub API Response: {response}")
        return {"api_response": response}

    def _comment_issue_node(self, state: WorkflowState) -> Dict[str, Any]:
        print("--- Executing GitHub Comment on Issue Node ---")
        repo_name = state.get("repo_name")
        issue_number = state.get("issue_number")
        comment_body = state.get("comment_body")
        if not repo_name or not issue_number or not comment_body:
            return {
                "api_response": {"error": "Repo, issue num, or comment not extracted."},
                "error_message": "Params missing for comment",
            }
        response = self._call_comment_on_github_issue(repo_name, issue_number, comment_body)
        print(f"GitHub API Response: {response}")
        return {"api_response": response}

    def _slack_message_node(self, state: WorkflowState) -> Dict[str, Any]:
        print("--- Executing Slack Message Node ---")
        user_query = state["user_query"]

        # Extract Slack target and message
        slack_target = self._extract_slack_target(user_query)
        message = slack_target["message"]
        user = slack_target["user"]
        channel = slack_target["channel"] if not user else None

        response = self._call_send_slack_message(message, channel=channel, user=user)
        print(f"Slack API Response: {response}")
        return {"api_response": response}

    def _list_branches_node(self, state: WorkflowState) -> Dict[str, Any]:
        print("--- Executing GitHub List Branches Node ---")
        repo_name = state.get("repo_name")
        if not repo_name:
            return {
                "api_response": {"error": "Repository name not extracted for listing branches."},
                "error_message": "Repo name missing",
            }
        response = self._call_list_github_branches(repo_name)
        print(f"GitHub API Response: {response}")
        return {"api_response": response}

    def _get_branch_node(self, state: WorkflowState) -> Dict[str, Any]:
        print("--- Executing GitHub Get Branch Node ---")
        repo_name = state.get("repo_name")
        branch_name = state.get("branch_name")
        if not repo_name or not branch_name:
            return {
                "api_response": {"error": "Repository name or branch name not extracted."},
                "error_message": "Repo/Branch name missing",
            }
        response = self._call_get_github_branch(repo_name, branch_name)
        print(f"GitHub API Response: {response}")
        return {"api_response": response}

    def _create_branch_node(self, state: WorkflowState) -> Dict[str, Any]:
        print("--- Executing GitHub Create Branch Node ---")
        repo_name = state.get("repo_name")
        branch_name = state.get("branch_name")
        source_branch = state.get("source_branch", "main")

        if not repo_name or not branch_name:
            return {
                "api_response": {"error": "Repository name or branch name not extracted."},
                "error_message": "Repo/Branch name missing",
            }

        response = self._call_create_github_branch(repo_name, branch_name, source_branch)
        print(f"GitHub API Response: {response}")
        return {"api_response": response}

    def _unhandled_action_node(self, state: WorkflowState) -> Dict[str, Any]:
        print("--- Executing Unhandled Action Node ---")
        error_msg = state.get("error_message", "The user query could not be handled by available actions.")

        # Provide helpful suggestions
        suggestions = [
            "Try: 'create an issue in repo my-project'",
            "Try: 'list issues in repository backend'",
            "Try: 'show issue #123 in repo frontend'",
            "Try: 'send a message to the team'",
        ]

        return {
            "api_response": {
                "message": "I didn't understand your request. Here are some things you can try:",
                "suggestions": suggestions,
                "your_request": state["user_query"],
            }
        }

    def _build_graph(self) -> StateGraph:
        workflow_builder = StateGraph(WorkflowState)

        workflow_builder.add_node("classify_and_extract", self._classify_and_extract_parameters_node)
        workflow_builder.add_node("github_create_issue_node", self._create_issue_node)
        workflow_builder.add_node("github_list_issues_node", self._list_issues_node)
        workflow_builder.add_node("github_get_issue_node", self._get_issue_node)
        workflow_builder.add_node("github_comment_issue_node", self._comment_issue_node)
        workflow_builder.add_node("slack_message_node", self._slack_message_node)
        workflow_builder.add_node("unhandled_action_node", self._unhandled_action_node)
        workflow_builder.add_node("general_response_node", self._general_response_node)
        workflow_builder.add_node("needs_clarification_node", self._needs_clarification_node)
        workflow_builder.add_node("github_list_branches_node", self._list_branches_node)
        workflow_builder.add_node("github_get_branch_node", self._get_branch_node)
        workflow_builder.add_node("github_create_branch_node", self._create_branch_node)
        workflow_builder.set_entry_point("classify_and_extract")

        workflow_builder.add_conditional_edges(
            "classify_and_extract",
            lambda state: state.get("action_type", "unhandled"),
            {
                "github_create_issue": "github_create_issue_node",
                "github_list_issues": "github_list_issues_node",
                "github_get_issue": "github_get_issue_node",
                "github_comment_issue": "github_comment_issue_node",
                "slack_send_message": "slack_message_node",
                "unhandled": "unhandled_action_node",
                "general_response": "general_response_node",
                "needs_clarification": "needs_clarification_node",
                "github_list_branches": "github_list_branches_node",
                "github_get_branch": "github_get_branch_node",
                "github_create_branch": "github_create_branch_node",
            },
        )

        workflow_builder.add_edge("github_create_issue_node", END)
        workflow_builder.add_edge("github_list_issues_node", END)
        workflow_builder.add_edge("github_get_issue_node", END)
        workflow_builder.add_edge("github_comment_issue_node", END)
        workflow_builder.add_edge("slack_message_node", END)
        workflow_builder.add_edge("unhandled_action_node", END)
        workflow_builder.add_edge("general_response_node", END)
        workflow_builder.add_edge("needs_clarification_node", END)
        workflow_builder.add_edge("github_list_branches_node", END)
        workflow_builder.add_edge("github_get_branch_node", END)
        workflow_builder.add_edge("github_create_branch_node", END)
        return workflow_builder.compile()

    def _format_response(self, final_state: WorkflowState) -> str:
        action_type = final_state.get("action_type")
        api_response = final_state.get("api_response")
        error_message = final_state.get("error_message")

        if error_message:  # Prioritize pre-API call errors
            return f"Error processing your request: {error_message}"

        if not api_response:
            return "No API response was received."

        if isinstance(api_response, dict) and api_response.get("error"):
            return f"API Error ({action_type}): {api_response.get('error')}. Details: {api_response.get('details', 'N/A')}"

        if action_type == "github_create_issue":
            if api_response.get("html_url"):
                return f"✅ Successfully created GitHub issue: {api_response['html_url']}"
            return "❌ GitHub issue creation seems to have failed or returned an unexpected response."

        elif action_type == "github_list_issues":
            if isinstance(api_response, list):
                issues_summary = [
                    f"#{issue['number']} - {issue['title']}" for issue in api_response[:3]
                ]  # Show first 3
                summary_str = "\n".join(issues_summary)
                if len(api_response) > 3:
                    summary_str += f"\n... and {len(api_response) - 3} more."
                return f"📋 Found {len(api_response)} issues in repo '{final_state.get('repo_name')}':\n{summary_str}"
            return "❌ Could not retrieve or parse the list of GitHub issues."

        elif action_type == "github_get_issue":
            if api_response.get("html_url") and api_response.get("title"):
                return f"🔍 Details for issue #{api_response.get('number')} in repo '{final_state.get('repo_name')}':\nTitle: {api_response['title']}\nURL: {api_response['html_url']}"
            return "❌ Could not retrieve details for the GitHub issue."

        elif action_type == "github_comment_issue":
            if api_response.get("html_url"):
                return f"💬 Successfully commented on GitHub issue: {api_response['html_url']}"
            return "❌ GitHub issue comment seems to have failed or returned an unexpected response."

        elif action_type == "slack_send_message":
            if api_response.get("ok"):
                return f"💬 Successfully sent Slack message to channel {api_response.get('channel')} (Timestamp: {api_response.get('ts')})."
            else:
                return f"❌ Failed to send Slack message. Error: {api_response.get('error', 'Unknown Slack error')}"

        elif action_type == "unhandled":
            if api_response.get("suggestions"):
                suggestions_text = "\n".join(f"• {s}" for s in api_response["suggestions"])
                return f"🤔 {api_response.get('message', 'I couldn\'t understand your request.')}\n\n{suggestions_text}\n\nYour request was: '{api_response.get('your_request')}'"
            return f"🤔 I couldn't understand or handle your request. Please try being more specific."
        # Add this case in _format_response:
        elif action_type == "general_response":
            if api_response and api_response.get("message"):
                return api_response["message"]
            return "Hello! How can I help you today?"
        elif action_type == "github_list_branches":
            if isinstance(api_response, list):
                branches_summary = [
                    f"• {branch['name']}" + (f" (default)" if branch.get("protected") else "")
                    for branch in api_response[:10]  # Show first 10
                ]
                summary_str = "\n".join(branches_summary)
                if len(api_response) > 10:
                    summary_str += f"\n... and {len(api_response) - 10} more."
                return (
                    f"🌿 Found {len(api_response)} branches in repo '{final_state.get('repo_name')}':\n{summary_str}"
                )
            return "❌ Could not retrieve or parse the list of GitHub branches."

        elif action_type == "github_get_branch":
            if api_response.get("name"):
                commit_sha = api_response.get("commit", {}).get("sha", "Unknown")[:8]
                return f"🌿 Details for branch '{api_response['name']}' in repo '{final_state.get('repo_name')}':\nLatest commit: {commit_sha}\nProtected: {api_response.get('protected', False)}"
            return "❌ Could not retrieve details for the GitHub branch."

        elif action_type == "github_create_branch":
            if api_response.get("ref"):
                branch_name = api_response["ref"].replace("refs/heads/", "")
                return f"✅ Successfully created branch '{branch_name}' in repo '{final_state.get('repo_name')}' from '{final_state.get('source_branch', 'main')}'"
            return "❌ GitHub branch creation seems to have failed or returned an unexpected response."

        return f"Action '{action_type}' completed. Raw response: {json.dumps(api_response, indent=2)}"

    def process_query(self, user_query: str) -> str:
        print(f"\n--- Processing Query: {user_query} ---")
        initial_state: WorkflowState = {
            "user_query": user_query,
            "action_type": None,
            "repo_name": None,
            "issue_number": None,
            "comment_body": None,
            "issue_title": None,
            "issue_body": None,
            "api_response": None,
            "error_message": None,
        }
        final_state = self.app.invoke(initial_state)
        # print(f"--- Internal Final Workflow State --- \n{json.dumps(final_state, indent=2)}") # For debugging
        return self._format_response(final_state)

    def _extract_slack_target(self, query: str) -> Dict[str, str]:
        """
        Extracts Slack message target (user or channel) and message text from the query.
        Returns a dict with keys: 'user', 'channel', 'message'
        """
        
        print(f"DEBUG: Processing query: '{query}'")
        
        result = {'user': None, 'channel': None, 'message': None}
        
        # Extract user mention
        user_match = re.search(r"(?:to|@)\s*@?([a-zA-Z0-9._-]+)", query, re.IGNORECASE)
        if user_match:
            result['user'] = user_match.group(1)
        
        # Extract channel
        channel_match = re.search(r"(?:channel|in)\s+#?([a-zA-Z0-9_-]+)", query, re.IGNORECASE)
        if channel_match:
            result['channel'] = channel_match.group(1)
        
        # Extract message - try quotes first
        quote_match = re.search(r'["\']([^"\']+)["\']', query)
        if quote_match:
            result['message'] = quote_match.group(1).strip()
        else:
            # Try content after colon
            colon_match = re.search(r":\s*(.+?)(?:\s+(?:to|@|in|channel)|$)", query, re.IGNORECASE)
            if colon_match:
                result['message'] = colon_match.group(1).strip()
            else:
                # Remove command and extract remaining content before target
                cleaned = re.sub(r'^(?:send|message|notify|tell|inform)\s+(?:a\s+)?(?:slack\s+)?(?:message\s*)?:?\s*', '', query, flags=re.IGNORECASE)
                cleaned = re.sub(r'\s+(?:to|@|in|channel)\s+.+$', '', cleaned, flags=re.IGNORECASE)
                if cleaned.strip():
                    result['message'] = cleaned.strip()
        
        print(f"DEBUG: Final result: {result}")
        return result

if __name__ == "__main__":
    # TODO: Replace with your actual API keys and configuration from a secure source
    GEMINI_API_KEY = "<gemini api key>"  # Replace with your Gemini API Key
    GITHUB_TOKEN = "<your_github_token>"  # Replace with your GitHub token
    SLACK_TOKEN = "<slack token>"  # Replace with your Slack Bot Token
    GITHUB_OWNER = "<github username>"  # TODO: Make this dynamic or configurable

    if "your_slack_bot_token" in SLACK_TOKEN or "AIzaSy" not in GEMINI_API_KEY or "ghp_" not in GITHUB_TOKEN:
        print("WARNING: Please replace placeholder API keys and tokens in the __main__ block.")
        # You might want to exit or skip execution if keys are not set

    try:
        processor = WorkflowProcessor(
            gemini_api_key=GEMINI_API_KEY,
            github_token=GITHUB_TOKEN,
            slack_token=SLACK_TOKEN,
            github_owner=GITHUB_OWNER,
        )

        queries = [
            "Create an issue in repo cicdrelease about a login bug with details: The login page is broken after the last update.",
            "List issues for repository my-test-app",
            "Show me details for issue 1 in repo cicdrelease",
            "Comment on issue #1 in repo cicdrelease saying 'I am looking into this now.'",
            "Send a slack message: Hello team, the new build is ready for testing.",
            "List branches in repo cicdrelease",  # NEW
            "Show branch main in repo cicdrelease",  # NEW
            "Create branch feature-auth from main in repo cicdrelease",  # NEW
            "What branches exist in my-test-app repository",  # NEW
            "What is the weather today?",  # Unhandled
        ]

        for query in queries:
            friendly_response = processor.process_query(query)
            print(f"\nUser Query: {query}\nResponse: {friendly_response}\n" + "-" * 50)

    except ValueError as e:
        print(f"Initialization Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
