import requests
import json
import os

class Agent:
    def __init__(self, model, system_prompt, tools):
        self.model = model
        self.messages = [{"role": "system", "content": system_prompt}]
        self.tools = tools
        self.tool_map = {t["name"]: t for t in tools}

    def _call_api(self, parallel_tool_calls=True):
        """Call the API with optional parallel_tool_calls parameter.
        
        Args:
            parallel_tool_calls: If False, restricts the model to one tool call at a time
        """
        payload = {
            "model": self.model,
            "messages": self.messages,
            "tools": [t["definition"] for t in self.tools]
        }
        
        # Add parallel_tool_calls parameter if explicitly set to False
        if not parallel_tool_calls:
            payload["parallel_tool_calls"] = False
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
            data=json.dumps(payload)
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
        """Execute instruction and process all tool calls in batch until agent returns text."""
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
            
            # Process all tool calls in the batch
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
    
    def do_turn(self, instruction=None):
        """Execute one turn: process exactly one tool call and return the result immediately.
        For turn-based experiments where the agent takes one action at a time.
        If instruction is provided, it's added as a user message first."""
        if instruction:
            self.messages.append({"role": "user", "content": instruction})
        
        while True:
            result = self._call_api(parallel_tool_calls=False)  # Restrict to one tool call
            
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
                # Agent returned text instead of a tool call - return it
                response_text = message.get("content", "")
                self.messages.append({"role": "assistant", "content": response_text})
                return response_text
            
            # API guarantees only one tool call due to parallel_tool_calls=False
            tool_call = tool_calls[0]
            name = tool_call["function"]["name"]
            args_str = tool_call["function"].get("arguments", "{}")
            args = json.loads(args_str) if args_str else {}
            
            # Extract any text content the agent provided along with the tool call
            agent_text = message.get("content", "")
            
            # Add assistant message with the single tool call
            self.messages.append({
                "role": "assistant",
                "content": agent_text,
                "tool_calls": [tool_call]
            })
            
            # Execute tool
            tool = self.tool_map.get(name)
            tool_result = tool["execute"](args) if tool else f"Unknown tool: {name}"
            
            self.messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": tool_result
            })
            
            print(f"[{name}] {tool_result}")
            
            # Return the agent's text content (if any), not the tool result
            # The tool result is already printed above
            return agent_text