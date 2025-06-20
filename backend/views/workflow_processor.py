import json
from typing import Any, Dict, Optional, TypedDict, Union

import google.generativeai as genai
import requests  # type: ignore
from langgraph.graph import END, START, StateGraph

# Set up Gemini API
# TODO: Move API keys to environment variables or a secure configuration manager.


# Define the state for our graph
class WorkflowState(TypedDict):
    user_query: str
    action_type: Optional[str]  # e.g., "github_create_issue", "slack_send_message"
    repo_name: Optional[str]
    issue_number: Optional[int]
    comment_body: Optional[str]
    issue_title: Optional[str]  # For creating issues
    issue_body: Optional[str]  # For creating issues
    api_response: Union[Dict[str, Any], None]  # To store the response from GitHub/Slack API calls
    error_message: Optional[str]


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

    def _call_send_slack_message(self, user_query: str) -> Dict[str, Any]:
        """Sends a message to a Slack channel."""
        url = "https://slack.com/api/chat.postMessage"
        headers = {"Authorization": f"Bearer {self.slack_token}"}
        data = {"channel": "#general", "text": user_query}  # TODO: Make channel dynamic
        response = requests.post(url, json=data, headers=headers)
        return response.json()

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
        You are a smart assistant DevCascade that understands user requests and converts them to structured actions.
        
        User said: "{user_query}"
        
        Your job is to understand what the user wants to do and extract the relevant information.
        
        Here are the actions I can perform:
        
        1. CREATE GITHUB ISSUE: When user wants to create, raise, open, or make a new issue/bug/ticket
           - Keywords to look for: create, raise, open, make, new, issue, bug, ticket, problem, feature request
           - Examples: "create an issue", "raise a bug", "open a ticket", "make a new issue", "report a problem"
        
        2. LIST GITHUB ISSUES: When user wants to see, list, show, or view existing issues
           - Keywords: list, show, see, view, display, get all, fetch, what are the issues
           - Examples: "show me issues", "list all bugs", "what issues are there", "see problems"
        
        3. GET SPECIFIC GITHUB ISSUE: When user wants details about a specific issue number
           - Keywords: get, show, details, info, tell me about + issue number
           - Examples: "show issue 123", "get details of #45", "tell me about issue 67"
        
        4. COMMENT ON GITHUB ISSUE: When user wants to add comment to an issue
           - Keywords: comment, add comment, reply, respond + issue number
           - Examples: "comment on issue 123", "add a comment to #45", "reply to issue 67"
        
        5. SEND SLACK MESSAGE: When user wants to send message, notify team, or communicate
           - Keywords: send, message, notify, tell team, slack, communicate, inform
           - Examples: "send a message", "notify the team", "tell everyone", "slack this"
        
        For REPOSITORY NAMES, look for:
        - After words like: repo, repository, project, in, to, for
        - Repository names are usually: single words, hyphenated, or with underscores
        - Examples: "repo my-app", "in project-x", "to the backend-service repository"
        
        For ISSUE NUMBERS, look for:
        - Numbers after: issue, #, bug, ticket
        - Examples: "issue 123", "#45", "bug 67", "ticket 89"
        
        Analyze the user's request and respond ONLY with a simple action and parameters. DO NOT use JSON format.
        
        Respond in this exact format:
        ACTION: [one of: github_create_issue, github_list_issues, github_get_issue, github_comment_issue, slack_send_message, unhandled]
        REPO: [repository name if mentioned, or null]
        ISSUE_NUMBER: [issue number if mentioned, or null]
        ISSUE_TITLE: [inferred title for new issues, or null]
        ISSUE_BODY: [description if provided, or null]
        COMMENT: [comment text if adding comment, or null]
        MESSAGE: [message text for slack, or the original query]
        
        Be flexible and understanding. Even if the user doesn't use exact keywords, try to understand their intent.
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
            return {
                "api_response": {
                "message": response.text.strip(),
                "type": "general_conversation"
            }
        }
        except Exception as e:
            return {
            "api_response": {
                "message": "Hello! I'm DevCascade, your DevOps automation assistant. How can I help you today?",
                "type": "general_conversation"
            }
        } 
    
    def _parse_structured_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the structured response from Gemini"""
        lines = response_text.split('\n')
        parsed = {
            "action_type": "unhandled",
            "repo_name": None,
            "issue_number": None,
            "comment_body": None,
            "issue_title": None,
            "issue_body": None,
            "error_message": None,
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
            elif line.startswith("COMMENT:"):
                comment = line.split(":", 1)[1].strip()
                parsed["comment_body"] = comment if comment.lower() != "null" else None
        
        return parsed

    def _fallback_classification(self, user_query: str) -> Dict[str, Any]:
        """Fallback classification using simple pattern matching"""
        query_lower = user_query.lower().strip()
    
    # Check for conversational/greeting patterns first
        greeting_patterns = ['hello', 'hi', 'hey', 'howdy', 'greetings', 'good morning', 'good afternoon', 'good evening']
        question_patterns = ['how are you', 'what can you do', 'help', 'what is', 'tell me about', 'explain']
    
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
    
    # Common patterns for creating issues
        create_patterns = ['create', 'raise', 'open', 'make', 'new', 'add']
        issue_patterns = ['issue', 'bug', 'ticket', 'problem', 'feature']
    
    # Common patterns for listing
        list_patterns = ['list', 'show', 'see', 'view', 'display', 'get all', 'what are']
    
    # Common patterns for slack
        slack_patterns = ['send', 'message', 'notify', 'tell', 'slack', 'inform']
    
    # Try to extract repo name
        repo_name = self._extract_repo_name(user_query)
    
    # Try to extract issue number
        issue_number = self._extract_issue_number(user_query)
    
    # Determine action
        if any(create in query_lower for create in create_patterns) and any(issue in query_lower for issue in issue_patterns):
            return {
                "action_type": "github_create_issue",
                "repo_name": repo_name,
                "issue_number": None,
                "comment_body": None,
                "issue_title": f"Issue from: {user_query[:50]}...",
                "issue_body": f"Details: {user_query}",
                "error_message": None,
            }
        elif any(list_word in query_lower for list_word in list_patterns) and any(issue in query_lower for issue in issue_patterns):
            return {
                "action_type": "github_list_issues",
                "repo_name": repo_name,
                "issue_number": None,
                "comment_body": None,
                "issue_title": None,
                "issue_body": None,
                "error_message": None,
        }
        elif issue_number and ('show' in query_lower or 'get' in query_lower or 'details' in query_lower):
            return {
                "action_type": "github_get_issue",
                "repo_name": repo_name,
                "issue_number": issue_number,
                "comment_body": None,
                    "issue_title": None,
                "issue_body": None,
            "error_message": None,
        }
        elif issue_number and ('comment' in query_lower or 'reply' in query_lower):
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

    def _extract_repo_name(self, query: str) -> str:
        """Extract repository name from query using patterns"""
        import re
        
        # Pattern 1: "repo xyz", "repository abc", "project def"
        patterns = [
            r'(?:repo|repository|project)\s+([a-zA-Z0-9_-]+)',
            r'(?:in|to|for)\s+(?:the\s+)?([a-zA-Z0-9_-]+)(?:\s+repo|\s+repository|\s+project)?',
            r'([a-zA-Z0-9_-]+)(?:\s+repo|\s+repository|\s+project)',
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
            r'(?:issue|bug|ticket)\s+#?(\d+)',
            r'#(\d+)',
            r'(?:number|num)\s+(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None

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
        user_query = state["user_query"]  # For now, sends the whole query
        # In a real scenario, you might extract specific message text via Gemini
        response = self._call_send_slack_message(user_query)
        print(f"Slack API Response: {response}")
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
                "your_request": state["user_query"]
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
            },
        )

        workflow_builder.add_edge("github_create_issue_node", END)
        workflow_builder.add_edge("github_list_issues_node", END)
        workflow_builder.add_edge("github_get_issue_node", END)
        workflow_builder.add_edge("github_comment_issue_node", END)
        workflow_builder.add_edge("slack_message_node", END)
        workflow_builder.add_edge("unhandled_action_node", END)
        workflow_builder.add_edge("general_response_node", END)
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
            "Show me details for issue 1 in repo cicdrelease",  # Assuming issue 1 exists
            "Comment on issue #1 in repo cicdrelease saying 'I am looking into this now.'",  # Assuming issue 1 exists
            "Send a slack message: Hello team, the new build is ready for testing.",
            "What is the weather today?",  # Unhandled
        ]

        for query in queries:
            friendly_response = processor.process_query(query)
            print(f"\nUser Query: {query}\nResponse: {friendly_response}\n" + "-" * 50)

    except ValueError as e:
        print(f"Initialization Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
