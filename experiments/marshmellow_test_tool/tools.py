import sys
import os

# Import create_tool from parent tools module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from tools import create_tool

def wait_tool(env):
    """Create a tool for waiting 15 minutes."""
    def execute(args):
        return env.wait()
    return create_tool("wait", "Wait 15 minutes. Money will be added to your piggy bank.", execute)

def take_money_tool(env):
    """Create a tool for taking all money and ending the experiment."""
    def execute(args):
        return env.take_money()
    return create_tool("take_money", "Take all money from your piggy bank. Ends the experiment.", execute)

