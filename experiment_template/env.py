# Agent-facing stub functions with LLM-readable docstrings
# Used with custom_tools() to separate descriptions from implementations

# Use case: When you want to hide implementation details from the agent
# - Agent sees these clean function signatures and docstrings
# - Actual implementations go in environment.py
# - Useful for delayed gratification, state management, etc.

def hello_world():
    """Print 'Hello, world!'"""
    pass