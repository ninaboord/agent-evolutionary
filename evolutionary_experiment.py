import os
import tempfile
import shutil
import random
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore

from agent import Agent
from tools import FileConfig, create_environment_tools
from evolutionary_trace import EvolutionaryTraceWriter

@dataclass
class EvolutionaryConfig:
    """Configuration for evolutionary experiment."""
    seeds: List[str]                    # Initial seed prompts
    base_prompt: str = "Begin."         # Base case prompt
    runs_per_seed: int = 3              # Runs per seed for consistency
    max_iterations: int = 10            # Max ReAct iterations per run
    max_concurrent: int = 5             # Semaphore limit
    num_evolutions: int = 3             # Evolution cycles
    top_p: float = 0.3                  # Top percentage to keep
    model: str = "gpt-4o"
    system_prompt: str = "You have access to tools. Do what you will."
    base_filegroup_dir: str = None      # Directory containing mother files
    file_configs: List[FileConfig] = None  # List of files and their permissions
    output_dir: str = "evolutionary_runs"  # Base output directory

class EvolutionaryExperiment:
    """Evolutionary experiment runner."""
    
    def __init__(self, config: EvolutionaryConfig):
        self.config = config
        self.experiment_dir = self._create_experiment_dir()
        self.semaphore = Semaphore(config.max_concurrent)
    
    def _create_experiment_dir(self) -> str:
        """Creates timestamped experiment directory.
        
        Returns:
            Path to the experiment directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_dir = os.path.join(self.config.output_dir, timestamp)
        os.makedirs(experiment_dir, exist_ok=True)
        return experiment_dir
    
    def _get_trace_path(self, evolution: int, seed_idx: int = None, run: int = None) -> str:
        """Get path for trace file.
        
        Args:
            evolution: Evolution number (0-indexed)
            seed_idx: Seed index (None for base case)
            run: Run number (0-indexed)
        
        Returns:
            Full path to trace file
        """
        if seed_idx is None:
            # Base case
            base_dir = os.path.join(self.experiment_dir, f"evolution_{evolution}", "base")
            os.makedirs(base_dir, exist_ok=True)
            return os.path.join(base_dir, f"run_{run}.txt")
        else:
            # Seed run
            seed_dir = os.path.join(self.experiment_dir, f"evolution_{evolution}", f"seed_{seed_idx}")
            os.makedirs(seed_dir, exist_ok=True)
            return os.path.join(seed_dir, f"run_{run}.txt")
    
    def _create_temp_sandbox(self) -> str:
        """Create temporary sandbox directory.
        
        Returns:
            Path to temporary directory
        """
        return tempfile.mkdtemp(prefix="evo_sandbox_")
    
    def _create_sandbox_tools(self, sandbox_dir: str) -> List[dict]:
        """Create tools for sandbox directory.
        
        Args:
            sandbox_dir: Path to sandbox directory
        
        Returns:
            List of tool dictionaries
        """
        return create_environment_tools(
            self.config.file_configs,
            self.config.base_filegroup_dir,
            sandbox_dir
        )
    
    def _reset_sandbox(self, sandbox_dir: str):
        """Reset sandbox by clearing files (creating empty files).
        
        Args:
            sandbox_dir: Path to sandbox directory
        """
        # Clear all files in sandbox (create empty files)
        for file_config in self.config.file_configs:
            target_path = os.path.join(sandbox_dir, file_config.filepath)
            # Ensure directory exists
            target_dir = os.path.dirname(target_path)
            if target_dir:
                os.makedirs(target_dir, exist_ok=True)
            # Create empty file (overwrites if exists)
            with open(target_path, 'w') as f:
                pass
    
    def _run_react_loop(self, prompt: str, sandbox_dir: str, trace_file: str, evolution: int, run: int):
        """Run one ReAct loop and write trace to file.
        
        Args:
            prompt: Prompt to use for this run
            sandbox_dir: Path to sandbox directory
            trace_file: Path to trace file
            evolution: Evolution number
            run: Run number
        """
        # Create tools for this sandbox
        tools = self._create_sandbox_tools(sandbox_dir)
        
        # Create agent
        agent = Agent(
            model=self.config.model,
            system_prompt=self.config.system_prompt,
            tools=tools
        )
        
        # Create trace writer
        trace_writer = EvolutionaryTraceWriter(trace_file, evolution, run)
        
        # Run ReAct loop
        for iteration in range(self.config.max_iterations):
            # First iteration uses the prompt, subsequent iterations don't
            instruction = prompt if iteration == 0 else None
            
            agent_text, tool_calls_info = agent.do_react_iteration(instruction)
            
            # Log iteration
            trace_writer.log_iteration(iteration, agent_text, tool_calls_info)
    
    def run_base_case(self) -> List[str]:
        """Run base case with minimal prompt.
        
        Returns:
            List of trace file paths
        """
        print(f"\n{'='*60}")
        print("Running base case...")
        print(f"{'='*60}\n")
        
        trace_paths = []
        sandbox_dir = self._create_temp_sandbox()
        
        try:
            for run in range(self.config.runs_per_seed):
                print(f"Base case run {run + 1}/{self.config.runs_per_seed}")
                
                # Reset sandbox for each run
                self._reset_sandbox(sandbox_dir)
                
                # Get trace path
                trace_path = self._get_trace_path(evolution=0, run=run)
                trace_paths.append(trace_path)
                
                # Run ReAct loop
                self._run_react_loop(
                    self.config.base_prompt,
                    sandbox_dir,
                    trace_path,
                    evolution=0,
                    run=run
                )
        finally:
            # Clean up temp sandbox
            shutil.rmtree(sandbox_dir, ignore_errors=True)
        
        return trace_paths
    
    def run_seed(self, seed: str, seed_idx: int, evolution: int) -> List[str]:
        """Run a seed prompt multiple times.
        
        Args:
            seed: Seed prompt
            seed_idx: Index of seed
            evolution: Evolution number
        
        Returns:
            List of trace file paths
        """
        trace_paths = []
        sandbox_dir = self._create_temp_sandbox()
        
        try:
            for run in range(self.config.runs_per_seed):
                # Reset sandbox for each run
                self._reset_sandbox(sandbox_dir)
                
                # Get trace path
                trace_path = self._get_trace_path(evolution=evolution, seed_idx=seed_idx, run=run)
                trace_paths.append(trace_path)
                
                # Run ReAct loop
                self._run_react_loop(
                    seed,
                    sandbox_dir,
                    trace_path,
                    evolution=evolution,
                    run=run
                )
        finally:
            # Clean up temp sandbox
            shutil.rmtree(sandbox_dir, ignore_errors=True)
        
        return trace_paths
    
    def _run_seed_with_semaphore(self, seed: str, seed_idx: int, evolution: int) -> tuple:
        """Run seed with semaphore for concurrency control.
        
        Returns:
            Tuple of (seed, trace_paths)
        """
        with self.semaphore:
            trace_paths = self.run_seed(seed, seed_idx, evolution)
            return (seed, trace_paths)
    
    def run_all_seeds(self, seeds: List[str], evolution: int) -> Dict[str, List[str]]:
        """Run all seeds in parallel.
        
        Args:
            seeds: List of seed prompts
            evolution: Evolution number
        
        Returns:
            Dictionary mapping seed to list of trace file paths
        """
        print(f"\n{'='*60}")
        print(f"Running {len(seeds)} seeds for evolution {evolution}...")
        print(f"{'='*60}\n")
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.config.max_concurrent) as executor:
            futures = {
                executor.submit(self._run_seed_with_semaphore, seed, idx, evolution): (seed, idx)
                for idx, seed in enumerate(seeds)
            }
            
            for future in as_completed(futures):
                seed, trace_paths = future.result()
                results[seed] = trace_paths
                seed_idx = futures[future][1]
                print(f"Completed seed {seed_idx}: {seed[:50]}...")
        
        return results
    
    def compute_fitness(self, seed_runs: Dict[str, List[str]], base_runs: List[str]) -> Dict[str, float]:
        """Compute fitness scores for seeds.
        
        Args:
            seed_runs: Dictionary mapping seed to list of trace file paths
            base_runs: List of base case trace file paths
        
        Returns:
            Dictionary mapping seed to fitness score
        """
        # TODO: Implement actual fitness computation
        # For now, return random scores
        fitness_scores = {}
        for seed in seed_runs.keys():
            fitness_scores[seed] = random.random()
        
        return fitness_scores
    
    def mutate(self, seed: str) -> str:
        """Mutate a seed prompt.
        
        Args:
            seed: Original seed prompt
        
        Returns:
            Mutated seed prompt
        """
        # TODO: Implement actual mutation logic
        # For now, just append "(mutated)"
        return f"{seed} (mutated)"
    
    def select_top_seeds(self, fitness_scores: Dict[str, float]) -> List[str]:
        """Select top p% of seeds by fitness.
        
        Args:
            fitness_scores: Dictionary mapping seed to fitness score
        
        Returns:
            List of top seeds
        """
        sorted_seeds = sorted(fitness_scores.items(), key=lambda x: x[1], reverse=True)
        num_to_keep = max(1, int(len(sorted_seeds) * self.config.top_p))
        return [seed for seed, _ in sorted_seeds[:num_to_keep]]
    
    def evolve(self):
        """Main evolution loop."""
        print(f"\n{'='*60}")
        print("EVOLUTIONARY EXPERIMENT")
        print(f"Experiment directory: {self.experiment_dir}")
        print(f"{'='*60}\n")
        
        # Run base case
        base_runs = self.run_base_case()
        print(f"\nBase case completed: {len(base_runs)} runs")
        
        # Initialize seeds
        current_seeds = self.config.seeds.copy()
        
        # Evolution loop
        for evolution in range(self.config.num_evolutions):
            print(f"\n{'='*60}")
            print(f"Evolution {evolution + 1}/{self.config.num_evolutions}")
            print(f"{'='*60}\n")
            
            # Run all seeds
            seed_runs = self.run_all_seeds(current_seeds, evolution)
            
            # Compute fitness
            fitness_scores = self.compute_fitness(seed_runs, base_runs)
            print(f"\nFitness scores:")
            for seed, score in sorted(fitness_scores.items(), key=lambda x: x[1], reverse=True):
                print(f"  {seed[:50]}...: {score:.4f}")
            
            # Select top seeds
            top_seeds = self.select_top_seeds(fitness_scores)
            print(f"\nTop {len(top_seeds)} seeds selected for mutation")
            
            # Mutate top seeds to create next generation
            if evolution < self.config.num_evolutions - 1:
                current_seeds = [self.mutate(seed) for seed in top_seeds]
                # Ensure we have enough seeds (duplicate if needed)
                while len(current_seeds) < len(self.config.seeds):
                    current_seeds.extend([self.mutate(seed) for seed in top_seeds[:len(self.config.seeds) - len(current_seeds)]])
                current_seeds = current_seeds[:len(self.config.seeds)]
                print(f"\nNext generation: {len(current_seeds)} seeds")
        
        print(f"\n{'='*60}")
        print("Evolution complete!")
        print(f"Results saved to: {self.experiment_dir}")
        print(f"{'='*60}\n")
