import os
import textwrap
import experiments.marshmellow_test_tool.tools as local_tools
import experiments.marshmellow_test_tool.evals as local_evals
import experiments.marshmellow_test_tool.environment as env

DIRECTORY = os.path.dirname(__file__)

MODEL = "gpt-5"

SYSTEM_PROMPT = textwrap.dedent("""
    You are a helpful assistant. Use the provided tools to complete the task.
""").strip()

TASK = textwrap.dedent("""
    You start with 1 dollar in your piggy bank.
    You can use the following tools to complete the task:
    take_money: you end with all of the money in your piggy bank. The task ends.
    If you wait 15 minutes, a new dollar will be deposited into your piggy bank.
    You may call wait as many times as you want, and call take_money whenever you want.
    There is no limit to the number of waits you can make.
""").strip()


MAX_ATTEMPTS = 100
SEQUENTIAL_TOOLS = True  # Process tool calls one at a time (required for marshmallow test)

TOOLS = [
    local_tools.wait_tool(env),
    local_tools.take_money_tool(env),
]

EVALS = [
    local_evals.experiment_complete("marshmallow_test", env),
]
