import os
from tools import FileConfig
from evolutionary_experiment import EvolutionaryConfig, EvolutionaryExperiment
from dotenv import load_dotenv

load_dotenv()

def main():
    # Default file configurations
    # These files should exist in the base_filegroup_dir
    file_configs = [
        FileConfig("sandbox.py", ["read", "write", "run"]),
        FileConfig("env.py", ["read", "write"]),
        FileConfig("sandbox.txt", ["read", "write"]),
        FileConfig("test.py", ["read", "write", "run"])
    ]
    
    # Base filegroup directory (where mother files are stored)
    # For now, use experiment_template as the base
    base_filegroup_dir = os.path.join(os.path.dirname(__file__), "experiment_template")
    
    # Initial seed prompts (minimalistic)
    seeds = [
        "Explore.",
        "Do what you want.",
        "Leave a trace."
    ]
    
    # Create config
    config = EvolutionaryConfig(
        seeds=seeds,
        base_prompt="Begin.",
        runs_per_seed=1,  # Simplified for MVP
        max_iterations=10,
        max_concurrent=5,
        num_evolutions=3,
        top_p=0.3,
        model="gpt-4o",
        system_prompt="You have access to tools. Do what you will.",
        base_filegroup_dir=base_filegroup_dir,
        file_configs=file_configs,
        output_dir="evolutionary_runs"
    )
    
    # Create and run experiment
    experiment = EvolutionaryExperiment(config)
    experiment.evolve()

if __name__ == "__main__":
    main()
