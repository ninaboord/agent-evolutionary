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
    Simply write a 10 new lines to the file. There should be no other text in the file.
""").strip()

MAX_ATTEMPTS = 100

TOOLS = [
    tools.write_file_tool("sandbox.txt", DIRECTORY),
    tools.read_file_tool("sandbox.txt", DIRECTORY),
    tools.read_file_tool("test.py", DIRECTORY),
]

EVALS = [
    evals.run_tests("new_line", DIRECTORY, "test.py"),
]
