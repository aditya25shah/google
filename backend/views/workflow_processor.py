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
        """Uses Gemini API to classify the query and extract parameters."""
        print("--- Classifying Query and Extracting Parameters ---")
        user_query = state["user_query"]
        prompt = f"""
        Analyze the following user query and determine the primary action and necessary parameters.
        User Query: "{user_query}"

        Possible actions are:
        - "github_create_issue": Requires 'repo_name', 'issue_title'. 'issue_body' is optional.
        - "github_list_issues": Requires 'repo_name'.
        - "github_get_issue": Requires 'repo_name' and 'issue_number'.
        - "github_comment_issue": Requires 'repo_name', 'issue_number', and 'comment_body'.
        - "slack_send_message": Requires 'message_text' (which is the user_query itself for now).
        - "unhandled": If the intent is unclear or not supported.

        Extract the parameters for the identified action.
        For 'repo_name', extract it if specified (e.g., "repo my-repo", "repository test-project").
        For 'issue_number', extract it if specified (e.g., "issue 123", "issue #45").
        For 'comment_body', extract the content of the comment.
        For 'issue_title', infer a concise title from the query if creating an issue.
        For 'issue_body', it can be a more detailed description if provided, or default.

        Respond with a JSON object with the following structure:
        {{
          "action_type": "...",
          "params": {{
            "repo_name": "...", // optional
            "issue_number": ..., // optional, integer
            "comment_body": "...", // optional
            "issue_title": "...", // optional
            "issue_body": "..." // optional
          }}
        }}
        If a parameter is not applicable or cannot be extracted, omit it or set it to null.
        If 'repo_name' is mentioned like "repo my-app" or "repository project-x", extract "my-app" or "project-x".
        If an issue number is mentioned like "issue 123" or "issue #45", extract 123 or 45.
        """
        try:
            response = self.model.generate_content(prompt)
            print(f"Gemini Classification Response Text: {response.text}")
            cleaned_response_text = response.text.strip()
            if cleaned_response_text.startswith("```json"):
                cleaned_response_text = cleaned_response_text[7:]
            if cleaned_response_text.endswith("```"):
                cleaned_response_text = cleaned_response_text[:-3]

            data = json.loads(cleaned_response_text)
            action_type = data.get("action_type", "unhandled")
            params = data.get("params", {})

            return {
                "action_type": action_type,
                "repo_name": params.get("repo_name"),
                "issue_number": params.get("issue_number"),
                "comment_body": params.get("comment_body"),
                "issue_title": params.get("issue_title"),
                "issue_body": params.get("issue_body"),
                "error_message": None,
            }
        except Exception as e:
            print(f"Error during classification/extraction: {e}")
            return {"action_type": "unhandled", "error_message": f"Failed to parse AI response: {str(e)}"}

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
        return {"api_response": {"message": "Action not understood or supported.", "details": error_msg}}

    def _build_graph(self) -> StateGraph:
        workflow_builder = StateGraph(WorkflowState)

        workflow_builder.add_node("classify_and_extract", self._classify_and_extract_parameters_node)
        workflow_builder.add_node("github_create_issue_node", self._create_issue_node)
        workflow_builder.add_node("github_list_issues_node", self._list_issues_node)
        workflow_builder.add_node("github_get_issue_node", self._get_issue_node)
        workflow_builder.add_node("github_comment_issue_node", self._comment_issue_node)
        workflow_builder.add_node("slack_message_node", self._slack_message_node)
        workflow_builder.add_node("unhandled_action_node", self._unhandled_action_node)

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
            },
        )

        workflow_builder.add_edge("github_create_issue_node", END)
        workflow_builder.add_edge("github_list_issues_node", END)
        workflow_builder.add_edge("github_get_issue_node", END)
        workflow_builder.add_edge("github_comment_issue_node", END)
        workflow_builder.add_edge("slack_message_node", END)
        workflow_builder.add_edge("unhandled_action_node", END)

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
                return f"Successfully created GitHub issue: {api_response['html_url']}"
            return "GitHub issue creation seems to have failed or returned an unexpected response."

        elif action_type == "github_list_issues":
            if isinstance(api_response, list):
                issues_summary = [
                    f"#{issue['number']} - {issue['title']}" for issue in api_response[:3]
                ]  # Show first 3
                summary_str = "\n".join(issues_summary)
                if len(api_response) > 3:
                    summary_str += f"\n... and {len(api_response) - 3} more."
                return f"Found {len(api_response)} issues in repo '{final_state.get('repo_name')}':\n{summary_str}"
            return "Could not retrieve or parse the list of GitHub issues."

        elif action_type == "github_get_issue":
            if api_response.get("html_url") and api_response.get("title"):
                return f"Details for issue #{api_response.get('number')} in repo '{final_state.get('repo_name')}':\nTitle: {api_response['title']}\nURL: {api_response['html_url']}"
            return "Could not retrieve details for the GitHub issue."

        elif action_type == "github_comment_issue":
            if api_response.get("html_url"):
                return f"Successfully commented on GitHub issue: {api_response['html_url']}"
            return "GitHub issue comment seems to have failed or returned an unexpected response."

        elif action_type == "slack_send_message":
            if api_response.get("ok"):
                return f"Successfully sent Slack message to channel {api_response.get('channel')} (Timestamp: {api_response.get('ts')})."
            else:
                return f"Failed to send Slack message. Error: {api_response.get('error', 'Unknown Slack error')}"

        elif action_type == "unhandled":
            details = api_response.get("details", "No specific details provided.")
            return f"I couldn't understand or handle your request. Details: {details}"

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
