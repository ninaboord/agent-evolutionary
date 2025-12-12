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
        API response dict
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
    
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
        data=json.dumps(payload)
    )
    return response.json()
