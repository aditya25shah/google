import requests
import json

def test_slack_message(slack_token: str) -> None:
    """
    Simple test: Send a message to #social channel
    Only prints if there's an error
    """
    
    headers = {
        "Authorization": f"Bearer {slack_token}",
        "Content-Type": "application/json"
    }
    
    # Get channel ID for #social
    try:
        channels_url = "https://slack.com/api/conversations.list"
        channels_response = requests.get(channels_url, headers=headers)
        channels_data = channels_response.json()
        
        if not channels_data.get("ok"):
            print(f"FAIL: Could not list channels - {channels_data.get('error')}")
            return
        
        # Find #social channel
        social_channel_id = None
        for channel in channels_data.get("channels", []):
            if channel.get("name") == "social":
                social_channel_id = channel.get("id")
                break
        
        if not social_channel_id:
            print("FAIL: #social channel not found")
            return
        
        # Send test message
        message_url = "https://slack.com/api/chat.postMessage"
        message_data = {
            "channel": social_channel_id,
            "text": "Test message from bot 🤖"
        }
        
        message_response = requests.post(message_url, json=message_data, headers=headers)
        message_result = message_response.json()
        
        if not message_result.get("ok"):
            print(f"FAIL: Could not send message - {message_result.get('error')}")
        
    except Exception as e:
        print(f"FAIL: {e}")

# Usage:
if __name__ == "__main__":
    SLACK_TOKEN = "xoxb-9069193143991-9084440906021-HTCqUwqh0k5vSyGarrbsC54y"  # Replace with your actual token
    test_slack_message(SLACK_TOKEN)