import os
import textwrap
import experiments.marshmellow_test_tool.env as env_stubs
import experiments.marshmellow_test_tool.environment as env_impl
from tools import tools_from_env
from evals import completion_check
from experiment_config import ExperimentConfig

# Dataclass-based configuration (recommended)
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
    tools=tools_from_env(env_stubs, env_impl),
    evals=[completion_check("marshmallow_test", env_impl.is_complete)],
    max_attempts=100,
    is_sequential=True,
    is_complete_fn=env_impl.is_complete
)

