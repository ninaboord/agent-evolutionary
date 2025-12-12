from dataclasses import dataclass, field, asdict
from typing import List, Callable, Optional, Dict

@dataclass
class ExperimentConfig:
    """Structured configuration for an experiment."""
    
    # Required fields
    name: str
    directory: str
    model: str
    system_prompt: str
    task: str
    tools: List[dict]
    evals: List[Callable]
    
    # Optional fields with defaults
    max_attempts: int = 5
    give_test_feedback: bool = True
    
    # Sequential experiment fields
    is_sequential: bool = False
    is_complete_fn: Optional[Callable] = None
    
    def __post_init__(self):
        """Validate config after initialization."""
        if self.is_sequential and self.is_complete_fn is None:
            raise ValueError(f"Sequential experiment '{self.name}' requires is_complete_fn")
    
    def to_dict(self):
        """Convert config to dictionary for logging (excludes callables)."""
        config_dict = {
            'name': self.name,
            'model': self.model,
            'max_attempts': self.max_attempts,
            'give_test_feedback': self.give_test_feedback,
            'is_sequential': self.is_sequential,
            'system_prompt': self.system_prompt,
            'task': self.task,
            'tools': [
                {
                    'name': tool['name'],
                    'description': tool['definition']['function']['description']
                }
                for tool in self.tools
            ],
            'has_completion_fn': self.is_complete_fn is None
        }
        return config_dict


@dataclass
class EvolutionaryExperimentConfig:
    """Configuration for evolutionary experiment."""
    name: str
    initial_tools: List[Dict]  # List of dicts with keys: name, description
    system_prompt: str
    task_prompt: str
    model: str
    max_iterations: int
    max_concurrent: int
    num_evolutions: int
    top_k: int                # keep top k, mutate those k
    num_diverse: int          # add random tools
    tools_per_trial: int      # number of tools to include in each trial (e.g., 3 means N choose 3)
    trials_per_combination: int  # number of times to run each tool combination
    output_dir: str
    mutation_model: str
    mutation_prompt: str
    diversity_model: str
    diversity_prompt: str
