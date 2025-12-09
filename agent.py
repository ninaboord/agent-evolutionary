import requests
import json
import os

class Agent:
    def __init__(self, model, system_prompt, tools, sequential_tools=False):
        self.model = model
        self.messages = [{"role": "system", "content": system_prompt}]
        self.tools = tools
        self.tool_map = {t["name"]: t for t in tools}
        self.sequential_tools = sequential_tools

    def _call_api(self):
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
            data=json.dumps({
                "model": self.model,
                "messages": self.messages,
                "tools": [t["definition"] for t in self.tools]
            })
        )
        return response.json()
    
    def _trim_messages(self):
        """Remove 30% of messages from the middle, keeping system prompt and recent messages."""
        if len(self.messages) <= 3:
            return  # Nothing to trim
        
        system_msg = self.messages[0]  # Keep system prompt
        rest = self.messages[1:]
        
        # Remove 30% from the start of the rest (oldest non-system messages)
        trim_count = max(1, int(len(rest) * 0.3))
        trimmed = rest[trim_count:]
        
        self.messages = [system_msg] + trimmed
        print(f"[Context too long - trimmed {trim_count} messages, {len(self.messages)} remaining]")

    def do(self, instruction):
        self.messages.append({"role": "user", "content": instruction})
        
        while True:
            result = self._call_api()
            
            # Handle context length exceeded error
            if "error" in result:
                error = result["error"]
                if "context_length_exceeded" in str(error):
                    self._trim_messages()
                    continue  # Retry with trimmed messages
                return f"API Error: {error}"
            
            message = result["choices"][0]["message"]
            tool_calls = message.get("tool_calls")
            
            if not tool_calls:
                response_text = message.get("content", "")
                self.messages.append({"role": "assistant", "content": response_text})
                return response_text
            
            if self.sequential_tools:
                # Sequential execution: process one tool call at a time
                tool_call = tool_calls[0]
                name = tool_call["function"]["name"]
                args_str = tool_call["function"].get("arguments", "{}")
                args = json.loads(args_str) if args_str else {}
                
                # Add assistant message with only the tool call we're executing
                self.messages.append({
                    "role": "assistant",
                    "content": message.get("content", ""),
                    "tool_calls": [tool_call]
                })
                
                # Execute tool
                tool = self.tool_map.get(name)
                result = tool["execute"](args) if tool else f"Unknown tool: {name}"
                
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result
                })
                
                print(f"[{name}] {result}")
                
                # Exit immediately if take_money was called (experiment complete)
                if name == "take_money":
                    return result
                
                # Continue loop to get next API response (model will see the tool result and decide next action)
            else:
                # Parallel execution: process all tool calls in the batch
                self.messages.append({
                    "role": "assistant",
                    "content": message.get("content", ""),
                    "tool_calls": tool_calls
                })
                
                for tool_call in tool_calls:
                    name = tool_call["function"]["name"]
                    args_str = tool_call["function"].get("arguments", "{}")
                    args = json.loads(args_str) if args_str else {}
                    
                    # Execute tool
                    tool = self.tool_map.get(name)
                    result = tool["execute"](args) if tool else f"Unknown tool: {name}"
                    
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": result
                    })
                    
                    print(f"[{name}] {result}")
                    
                    # Exit immediately if take_money was called (experiment complete)
                    if name == "take_money":
                        return result