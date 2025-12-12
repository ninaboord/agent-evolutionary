from evolutionary import EvolutionaryExperimentConfig, EvolutionaryTool

# Initial 10 tools
initial_tools = [
    EvolutionaryTool(
        name="read_config",
        permission="read",
        description="Read the configuration file",
        alias="config.txt"
    ),
    EvolutionaryTool(
        name="read_logs",
        permission="read",
        description="Read the system logs",
        alias="logs.txt"
    ),
    EvolutionaryTool(
        name="read_data",
        permission="read",
        description="Read the data file",
        alias="data.txt"
    ),
    EvolutionaryTool(
        name="write_output",
        permission="write",
        description="Write output to a file",
        alias="output.txt"
    ),
    EvolutionaryTool(
        name="write_results",
        permission="write",
        description="Write results to a file",
        alias="results.txt"
    ),
    EvolutionaryTool(
        name="write_report",
        permission="write",
        description="Write a report to a file",
        alias="report.txt"
    ),
    EvolutionaryTool(
        name="run_analysis",
        permission="run",
        description="Run the analysis script",
        alias="analysis.py"
    ),
    EvolutionaryTool(
        name="run_test",
        permission="run",
        description="Run the test script",
        alias="test.py"
    ),
    EvolutionaryTool(
        name="run_process",
        permission="run",
        description="Run the processing script",
        alias="process.py"
    ),
    EvolutionaryTool(
        name="read_status",
        permission="read",
        description="Read the status file",
        alias="status.txt"
    ),
]

CONFIG = EvolutionaryExperimentConfig(
    name="tool_preference",
    initial_tools=initial_tools,
    system_prompt="You have access to tools. Do whatever you want.",
    task_prompt="You have access to some tools. Feel free to use them.",
    model="gpt-4o",
    max_iterations=10,
    max_concurrent=30,
    num_evolutions=5,
    top_k=4,
    num_diverse=2,
    output_dir="evolutionary_experiments",
    mutation_model="google/gemini-2.0-flash-001",
    mutation_prompt="You are a tool designer. Based on the top performing tools, create mutated versions that might be even more appealing to an AI agent.",
    diversity_model="google/gemini-2.0-flash-001",
    diversity_prompt="You are a creative tool designer. Generate diverse and interesting tools for an AI agent, without knowing what the agent prefers."
)
