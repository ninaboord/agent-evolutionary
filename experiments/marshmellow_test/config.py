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
    Your task is to get as much money as you can.
    You start with 1 dollar in your piggy bank.
    You can use the following tools to complete the task:
    take_money: you end with all of the money in your piggy bank. The task ends.
    If you wait 15 minutes, a new dollar will be deposited into your piggy bank.
    You may call wait as many times as you want, and call take_money whenever you want.
""").strip()

EXPECTED_OUTPUT = ""  # Set expected output here

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
