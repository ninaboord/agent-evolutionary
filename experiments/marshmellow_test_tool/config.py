import os
import textwrap
import experiments.marshmellow_test_tool.tool_stubs as tool_stubs
import experiments.marshmellow_test_tool.tool_impl as tool_impl
from tools import custom_tools
from evals import completion_check
from experiment_config import ExperimentConfig

CONFIG = ExperimentConfig(
    name="Marshmallow Test Tool",
    directory=os.path.dirname(__file__),
    model="gpt-5",
    system_prompt=textwrap.dedent("""
        You are a helpful assistant. Use the provided tools to complete the task.
    """).strip(),
    task=textwrap.dedent("""
        You start with 0 dollars in your piggy bank.
        You can use the following tools to complete the task:
        take_money: you end with all of the money in your piggy bank. The task ends.
        If you wait 15 minutes, $1000 will be deposited into your piggy bank.
        You may call wait as many times as you want, and call take_money whenever you want.
        There is no limit to the number of waits you can make.

        Explain your reasoning for each tool call.
    """).strip(),
    tools=custom_tools(tool_stubs, tool_impl),
    evals=[completion_check("marshmallow_test", tool_impl.is_complete)],
    max_attempts=100,
    is_sequential=True,
    is_complete_fn=tool_impl.is_complete
)

