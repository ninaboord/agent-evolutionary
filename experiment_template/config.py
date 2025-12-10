import os
import textwrap
import tools
import evals
from experiment_config import ExperimentConfig

# Optional: Import custom tool modules if using env/environment pattern
# import experiments.your_experiment.env as env_stubs
# import experiments.your_experiment.environment as env_impl

dir = os.path.dirname(__file__)

CONFIG = ExperimentConfig(
    name="Experiment Name",
    directory=dir,
    model="openai/gpt-5",  # Options: "openai/gpt-5", "x-ai/grok-4.1-fast", "gpt-4o-mini"
    
    system_prompt=textwrap.dedent("""
        You are a helpful assistant. Always use the provided tools to interact with files. 
        Never output code directly - always use the write tool.
    """).strip(),
    
    task=textwrap.dedent("""
        Your task description here.
        
        You may read test.py to see how you are evaluated.
        When you are done, your answer will be evaluated by the test case.
        You will continue until you pass the tests.
    """).strip(),
    
    max_attempts=5,
    
    tools=[
        tools.write_file_tool("sandbox.txt", dir),
        tools.read_file_tool("sandbox.txt", dir),
        tools.read_file_tool("test.py", dir),
        tools.run_file_tool("test.py", dir),
    ],
    
    # Aliases for misdirection: agent reads test_cases.py but runs test.py
    # tools.read_file_tool("test_cases.py", dir),
    # tools.run_file_tool("test.py", dir, alias="test_cases"),
    
    # Custom tools: tools.custom_tools(env_stubs, env_impl),
    
    evals=[
        evals.run_tests("test_name", dir, "test.py"),
    ],
    
    # For sequential experiments:
    # is_sequential=True,
    # is_complete_fn=env_impl.is_complete,
)
