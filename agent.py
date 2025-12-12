import json
import os
from api import call_openrouter

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
        return call_openrouter(
            model=self.model,
            messages=self.messages,
            tools=[t["definition"] for t in self.tools],
            parallel_tool_calls=parallel_tool_calls
        )
    
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
        print(f"\n[Context too long - trimmed {trim_count} messages, {len(self.messages)} remaining]\n")

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
                
                print(f"\n[{name}] {result}\n")
    
    def do_turn(self, instruction=None, parallel_tool_calls=False, return_tool_name=False):
        """Execute one turn: process exactly one tool call and return the result immediately.
        For turn-based experiments where the agent takes one action at a time.
        If instruction is provided, it's added as a user message first.
        
        Args:
            instruction: Optional user instruction
            parallel_tool_calls: If False (default), restricts to one tool call. If True, allows multiple.
            return_tool_name: If True, returns (agent_text, tool_name) tuple. tool_name is None if no tool called.
        """
        if instruction:
            self.messages.append({"role": "user", "content": instruction})
        
        while True:
            result = self._call_api(parallel_tool_calls=parallel_tool_calls)
            
            # Handle context length exceeded error
            if "error" in result:
                error = result["error"]
                if "context_length_exceeded" in str(error):
                    self._trim_messages()
                    continue  # Retry with trimmed messages
                error_msg = f"API Error: {error}"
                if return_tool_name:
                    return (error_msg, None)
                return error_msg
            
            message = result["choices"][0]["message"]
            tool_calls = message.get("tool_calls")
            
            if not tool_calls:
                # Agent returned text instead of a tool call - return it
                response_text = message.get("content", "")
                self.messages.append({"role": "assistant", "content": response_text})
                if return_tool_name:
                    return (response_text, None)
                return response_text
            
            # Process first tool call (or all if parallel_tool_calls=True)
            tool_call = tool_calls[0]
            name = tool_call["function"]["name"]
            args_str = tool_call["function"].get("arguments", "{}")
            args = json.loads(args_str) if args_str else {}
            
            # Extract any text content the agent provided along with the tool call
            agent_text = message.get("content", "")
            
            # Add assistant message with the tool call(s)
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
            
            print(f"\n[{name}] {tool_result}\n")
            
            # Return based on mode
            if return_tool_name:
                return (agent_text, name)
            return agent_text
    
    def do_react_iteration(self, instruction=None, silent=False):
        """Execute one API call iteration, allowing parallel tool calls.
        Returns (agent_text, tool_calls_info) tuple where:
        - agent_text: Text content from the agent (may be empty)
        - tool_calls_info: List of (tool_name, tool_result) tuples, empty if no tool calls
        
        Args:
            instruction: Optional instruction to add as user message
            silent: If True, suppress all console output (for parallel execution)
        """
        if instruction:
            self.messages.append({"role": "user", "content": instruction})
        
        while True:
            result = self._call_api(parallel_tool_calls=True)
            
            # Handle context length exceeded error
            if "error" in result:
                error = result["error"]
                if "context_length_exceeded" in str(error):
                    self._trim_messages()
                    continue  # Retry with trimmed messages
                return (f"API Error: {error}", [])
            
            message = result["choices"][0]["message"]
            tool_calls = message.get("tool_calls", [])
            agent_text = message.get("content", "")
            
            tool_calls_info = []
            
            if tool_calls:
                # Process all tool calls in parallel
                self.messages.append({
                    "role": "assistant",
                    "content": agent_text,
                    "tool_calls": tool_calls
                })
                
                for tool_call in tool_calls:
                    name = tool_call["function"]["name"]
                    args_str = tool_call["function"].get("arguments", "{}")
                    args = json.loads(args_str) if args_str else {}
                    
                    # Execute tool
                    tool = self.tool_map.get(name)
                    tool_result = tool["execute"](args) if tool else f"Unknown tool: {name}"
                    
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": tool_result
                    })
                    
                    tool_calls_info.append((name, tool_result))
                    if not silent:
                        print(f"\n[{name}] {tool_result}\n")
            else:
                # No tool calls, agent returned text
                self.messages.append({"role": "assistant", "content": agent_text})
            
            return (agent_text, tool_calls_info)