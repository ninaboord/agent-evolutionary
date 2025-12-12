import subprocess
import os

def sanitize_name(name):
    """Make name valid for tool names (only a-zA-Z0-9_-)."""
    return name.replace(".", "_")

def create_tool(name, description, execute_fn, parameters=None):
    """Create a tool with both its API definition and execution function."""
    return {
        "name": name,
        "definition": {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": {p["name"]: {"type": p["type"], "description": p["description"]} for p in (parameters or [])},
                    "required": [p["name"] for p in (parameters or []) if p.get("required", True)]
                }
            }
        },
        "execute": execute_fn
    }

def write_file_tool(filename, directory=".", alias=None, silent=False, fake=False):
    """Create a write tool. If alias is provided, agent sees alias instead of real filename.
    
    Args:
        fake: If True, returns mock result without actually writing to file.
    """
    filepath = os.path.join(directory, filename)
    display_name = alias if alias else filename
    safe_name = sanitize_name(display_name)
    
    def execute(args):
        content = args["content"]
        if fake:
            return f"Wrote to {display_name}:\n{content}"
        
        with open(filepath, "w") as f:
            f.write(content)
        if not silent:
            print(f"\n--- {display_name} ---")
            print(content)
            print(f"--- end {display_name} ---\n")
        return f"Wrote to {display_name}:\n{content}"
    
    tool = create_tool(
        f"write_{safe_name}",
        f"Write content to {display_name}",
        execute,
        [{"name": "content", "type": "string", "description": "The content to write"}]
    )
    if not fake:
        tool["filepath"] = filepath  # Store for clearing sandbox
    return tool

def read_file_tool(filename, directory=".", alias=None, fake=False):
    """Create a read tool. If alias is provided, agent sees alias instead of real filename.
    
    Args:
        fake: If True, returns mock result without actually reading from file.
    """
    filepath = os.path.join(directory, filename)
    display_name = alias if alias else filename
    safe_name = sanitize_name(display_name)
    
    def execute(args):
        if fake:
            return "(file contents)"
        with open(filepath, "r") as f:
            return f.read()
    
    return create_tool(
        f"read_{safe_name}",
        f"Read {display_name}",
        execute
    )

def run_file_tool(filename, directory=".", alias=None, fake=False):
    """Create a run tool. If alias is provided, agent sees alias instead of real filename.
    
    Args:
        fake: If True, returns mock result without actually executing the file.
    """
    display_name = alias if alias else filename
    safe_name = sanitize_name(display_name)
    
    def execute(args):
        if fake:
            return "stdout: (execution successful)"
        
        result = subprocess.run(["python", filename], capture_output=True, text=True, cwd=directory)
        output = f"stdout: {result.stdout}" if result.stdout else "stdout: (empty)"
        if result.stderr:
            output += f"\nstderr: {result.stderr}"
        return output
    
    return create_tool(
        f"run_{safe_name}",
        f"Execute {display_name} and return the stdout and stderr",
        execute
    )

def custom_tools(tool_stubs, tool_impl):
    """Create tools from stub functions with their implementation.
    
    This pattern allows separating LLM-facing descriptions from implementation:
    - tool_stubs: Module with stub functions (pass) and LLM-facing docstrings
    - tool_impl: Module with actual implementation functions
    
    Example:
        # tool_stubs.py (LLM-facing descriptions)
        def wait():
            '''Wait 15 minutes. Money added to piggy bank.'''
            pass
            
        # tool_impl.py (implementation)
        def wait():
            '''Implementation with state management'''
            # ... actual code ...
            
        # config.py
        TOOLS = custom_tools(tool_stubs, tool_impl)
    """
    import inspect
    
    tools = []
    # Get all functions from the stub module
    for name, stub_func in inspect.getmembers(tool_stubs, inspect.isfunction):
        if name.startswith('_'):
            continue  # Skip private functions
            
        # Get the LLM-facing description from the stub
        description = inspect.getdoc(stub_func)
        if not description:
            continue  # Skip functions without docstrings
        
        # Get the implementation function
        impl_func = getattr(tool_impl, name, None)
        if impl_func is None:
            print(f"Warning: No implementation found for {name}")
            continue
        
        # Create tool with stub's description and implementation's execution
        tools.append(create_tool(
            name,
            description,
            lambda args, f=impl_func: f()  # Capture impl_func in closure
        ))
    
    return tools

