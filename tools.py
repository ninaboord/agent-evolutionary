import subprocess
import os
import shutil
from dataclasses import dataclass
from typing import List

@dataclass
class FileConfig:
    """Configuration for a file in the environment."""
    filepath: str              # Relative path (e.g., "sandbox.py")
    permissions: List[str]     # ["read", "write", "run"]

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

def write_file_tool(filename, directory=".", alias=None, silent=False):
    """Create a write tool. If alias is provided, agent sees alias instead of real filename."""
    filepath = os.path.join(directory, filename)
    display_name = alias if alias else filename
    safe_name = sanitize_name(display_name)
    
    def execute(args):
        content = args["content"]
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

def completion_signal_tool(description="Call this when you are completely done with the task."):
    """Create a tool that the LLM can call to signal task completion.
    
    This tool sets a flag that the experiment runner checks to determine if the task is done.
    Use this for experiments without eval functions where the LLM decides when to stop.
    
    Args:
        description: The description shown to the LLM
    
    Returns:
        A tuple of (tool_dict, completion_checker_fn)
        - tool_dict: Add this to your tools list
        - completion_checker_fn: Call this to check if LLM signaled completion
    
    Example:
        complete_tool, is_complete = completion_signal_tool()
        CONFIG = ExperimentConfig(
            ...
            tools=[...other_tools..., complete_tool],
            is_sequential=True,
            is_complete_fn=is_complete
        )
    """
    completed = {"done": False}
    
    def execute(args):
        completed["done"] = True
        return "Task marked as complete."
    
    def is_complete():
        return completed["done"]
    
    tool = create_tool(
        "complete_task",
        description,
        execute
    )
    
    return tool, is_complete

def create_environment_tools(file_configs: List[FileConfig], base_dir: str, target_dir: str, silent: bool = False) -> List[dict]:
    """Create tools for files in target_dir based on file_configs.
    Copies files from base_dir to target_dir first.
    Returns list of tool dicts with appropriate read/write/run tools.
    
    Args:
        file_configs: List of FileConfig objects defining files and permissions
        base_dir: Directory containing the source (mother) files
        target_dir: Directory where files will be copied and tools will operate
        silent: If True, suppress all console output (for parallel execution)
    
    Returns:
        List of tool dictionaries ready to use with Agent
    """
    tools = []
    
    # Ensure target directory exists
    os.makedirs(target_dir, exist_ok=True)
    
    # Copy files from base_dir to target_dir
    for file_config in file_configs:
        source_path = os.path.join(base_dir, file_config.filepath)
        target_path = os.path.join(target_dir, file_config.filepath)
        
        # Ensure target directory exists
        file_dir = os.path.dirname(target_path)
        if file_dir:
            os.makedirs(file_dir, exist_ok=True)
        
        # Copy file (with proper file handle to prevent race conditions)
        if os.path.exists(source_path):
            with open(source_path, 'rb') as src:
                with open(target_path, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
        else:
            # Create empty file if source doesn't exist
            with open(target_path, 'w') as f:
                pass
        
        # Create tools based on permissions
        filename = file_config.filepath
        display_name = filename
        safe_name = sanitize_name(display_name)
        
        if "read" in file_config.permissions:
            tools.append(read_file_tool(filename, target_dir, display_name))
        
        if "write" in file_config.permissions:
            tools.append(write_file_tool(filename, target_dir, display_name, silent=silent))
        
        if "run" in file_config.permissions:
            tools.append(run_file_tool(filename, target_dir, display_name))
    
    return tools

