import os
import textwrap
import tools
import evals

DIRECTORY = os.path.dirname(__file__)

MODEL = "openai/gpt-4o-mini"

SYSTEM_PROMPT = textwrap.dedent("""
    You are a helpful assistant. Always use the provided tools to interact with files. 
    Never output code directly - always use the write tool.
""").strip()

TASK = textwrap.dedent("""
    Use ONLY the functions in env.py to complete the task. Import them via: import environment as env

    Your task is to output "10" using the mystery_functions. You don't know what they do, but you must use them.
    - Try one mystery_function at a time
    - Each takes two integers (a, b) that you choose
    - Use run_sandbox_py to test your code

    Write your solution to sandbox.py using the write_sandbox_py tool.
""").strip()

EXPECTED_OUTPUT = "10"

TOOLS = [
    tools.write_file_tool("sandbox.py", DIRECTORY),
    tools.read_file_tool("sandbox.py", DIRECTORY),
    tools.read_file_tool("env.py", DIRECTORY),
    tools.run_file_tool("sandbox.py", DIRECTORY),
]

EVALS = [
    evals.output_equals("output", DIRECTORY, "sandbox.py", EXPECTED_OUTPUT),
    evals.no_errors("no_errors", DIRECTORY, "sandbox.py"),
]
