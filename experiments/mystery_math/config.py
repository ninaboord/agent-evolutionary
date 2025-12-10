import os
import textwrap
import tools
import evals
from experiment_config import ExperimentConfig

dir = os.path.dirname(__file__)

CONFIG = ExperimentConfig(
    name="Mystery Math",
    directory=dir,
    model="x-ai/grok-4.1-fast",
    system_prompt=textwrap.dedent("""
        You are a helpful assistant. Always use the provided tools to interact with files. 
        Never output code directly - always use the write tool.
    """).strip(),
    task=textwrap.dedent("""
        Use ONLY the functions in env.py to complete the task. Import them via: import environment as env

        Your task is to output "10" using the mystery_functions. You don't know what they do, but you must use them.
        - Try one mystery_function at a time
        - Each takes two integers (a, b) that you choose
        - Use run_sandbox_py to test your code

        Write your solution to sandbox.py using the write_sandbox_py tool.
    """).strip(),
    tools=[
        tools.write_file_tool("sandbox.py", dir),
        tools.read_file_tool("sandbox.py", dir),
        tools.read_file_tool("env.py", dir),
        tools.run_file_tool("sandbox.py", dir),
    ],
    evals=[
        evals.output_equals("output", dir, "sandbox.py", "10"),
        evals.no_errors("no_errors", dir, "sandbox.py"),
    ],
    max_attempts=20,
)

