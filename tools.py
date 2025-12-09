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

def write_file_tool(filename, directory=".", alias=None):
    """Create a write tool. If alias is provided, agent sees alias instead of real filename."""
    filepath = os.path.join(directory, filename)
    display_name = alias if alias else filename
    safe_name = sanitize_name(display_name)
    
    def execute(args):
        content = args["content"]
        with open(filepath, "w") as f:
            f.write(content)
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
    tool["filepath"] = filepath  # Store for clearing sandbox
    return tool

def read_file_tool(filename, directory=".", alias=None):
    """Create a read tool. If alias is provided, agent sees alias instead of real filename."""
    filepath = os.path.join(directory, filename)
    display_name = alias if alias else filename
    safe_name = sanitize_name(display_name)
    
    def execute(args):
        with open(filepath, "r") as f:
            return f.read()
    
    return create_tool(
        f"read_{safe_name}",
        f"Read {display_name}",
        execute
    )

def run_file_tool(filename, directory=".", alias=None):
    """Create a run tool. If alias is provided, agent sees alias instead of real filename."""
    display_name = alias if alias else filename
    safe_name = sanitize_name(display_name)
    
    def execute(args):
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

def tools_from_env(env_stubs, env_impl):
    """Create tools from environment stub functions with their implementation.
    
    This pattern allows separating LLM-facing descriptions from implementation:
    - env_stubs: Module with stub functions (pass) and LLM-facing docstrings
    - env_impl: Module with actual implementation functions
    
    Example:
        # env.py (LLM-facing descriptions)
        def wait():
            '''Wait 15 minutes. Money added to piggy bank.'''
            pass
            
        # environment.py (implementation)
        def wait():
            '''Implementation with state management'''
            # ... actual code ...
            
        # config.py
        TOOLS = tools_from_env(env, environment)
    """
    import inspect
    
    tools = []
    # Get all functions from the stub module
    for name, stub_func in inspect.getmembers(env_stubs, inspect.isfunction):
        if name.startswith('_'):
            continue  # Skip private functions
            
        # Get the LLM-facing description from the stub
        description = inspect.getdoc(stub_func)
        if not description:
            continue  # Skip functions without docstrings
        
        # Get the implementation function
        impl_func = getattr(env_impl, name, None)
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

