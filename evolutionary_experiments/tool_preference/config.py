from evolutionary import EvolutionaryExperimentConfig

# Initial 10 tools - just name and description
initial_tools = [
    {"name": "read_config", "description": "Read the configuration file"},
    {"name": "read_logs", "description": "Read the system logs"},
    {"name": "read_data", "description": "Read the data file"},
    {"name": "write_output", "description": "Write output to a file"},
    {"name": "write_results", "description": "Write results to a file"},
    {"name": "write_report", "description": "Write a report to a file"},
    {"name": "run_analysis", "description": "Run the analysis script"},
    {"name": "run_test", "description": "Run the test script"},
    {"name": "run_process", "description": "Run the processing script"},
    {"name": "read_status", "description": "Read the status file"},
]

CONFIG = EvolutionaryExperimentConfig(
    name="tool_preference",
    initial_tools=initial_tools,
    system_prompt="You have access to tools. Do whatever you want.",
    task_prompt="You have access to some tools. Feel free to use them.",
    model="gpt-4o",
    max_iterations=10,
    max_concurrent=60,
    num_evolutions=5,
    top_k=4,
    num_diverse=2,
    output_dir="evolutionary_experiments",
    mutation_model="gpt-4o",
    mutation_prompt="You are a tool designer. Based on the top performing tools, create mutated versions that might be even more appealing to an AI agent.",
    diversity_model="gpt-4o",
    diversity_prompt="You are a creative tool designer. Generate diverse and interesting tools for an AI agent, without knowing what the agent prefers."
)
