import requests
import json
import os

def call_openrouter(model: str, messages: list, tools: list = None, response_format: dict = None, parallel_tool_calls: bool = True) -> dict:
    """Shared API call logic for OpenRouter.
    
    Args:
        model: Model name (e.g., "gpt-4o", "google/gemini-2.0-flash-001")
        messages: List of message dicts
        tools: Optional list of tool definitions
        response_format: Optional response format dict (for structured output)
        parallel_tool_calls: If False, restricts to one tool call at a time
    
    Returns:
        API response dict (or error dict on failure)
    """
    payload = {
        "model": model,
        "messages": messages,
    }
    
    if tools:
        payload["tools"] = tools
        if not parallel_tool_calls:
            payload["parallel_tool_calls"] = False
    
    if response_format:
        payload["response_format"] = response_format
    
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
            data=json.dumps(payload),
            timeout=60  # 60 second timeout
        )
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": "Request timeout after 60 seconds"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {e}"}
