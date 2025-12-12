import os
from datetime import datetime


class TraceWriter:
    """Minimal write-ahead trace writer."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        open(filepath, 'w').close()
    
    def log(self, message: str):
        """Write-ahead logging - append to file immediately."""
        with open(self.filepath, 'a') as f:
            f.write(message + "\n")
    
    def log_item(self, title: str, content: str):
        """Log a titled item with content."""
        self.log(f"{title}:")
        self.log(content)
        self.log("")
    
    def log_header(self, title: str, **details):
        """Log a header with optional key-value details."""
        self.log(f"\n{'='*60}")
        self.log(title)
        for key, value in details.items():
            self.log(f"{key}: {value}")
        self.log(f"{'='*60}\n")
    
    def log_section(self, name: str):
        """Log a section divider."""
        self.log(f"\n--- {name} ---\n")
    
    def log_divider(self):
        """Log a simple divider."""
        self.log(f"{'-'*60}")
    
    def log_result(self, passed: bool, name: str, attempts: int):
        """Log pass/fail result."""
        if passed:
            self.log(f"\n✓ PASSED: {name} after {attempts} attempt(s)")
        else:
            self.log(f"\n✗ FAILED: {name} after {attempts} attempt(s)")
    
    def save(self):
        """Print confirmation (no-op since we write ahead)."""
        print(f"\nTrace saved to: {self.filepath}")
    
    def log_config(self, config):
        """Log full experiment configuration."""
        self.log_header("Experiment Configuration")
        self.log(f"Name: {config.name}")
        self.log(f"Model: {config.model}")
        self.log(f"Mutation Model: {config.mutation_model}")
        self.log(f"Diversity Model: {config.diversity_model}")
        self.log(f"Max Iterations: {config.max_iterations}")
        self.log(f"Max Concurrent: {config.max_concurrent}")
        self.log(f"Num Evolutions: {config.num_evolutions}")
        self.log(f"Top K: {config.top_k}")
        self.log(f"Num Diverse: {config.num_diverse}")
        self.log(f"System Prompt: {config.system_prompt}")
        self.log(f"Task Prompt: {config.task_prompt}")
        self.log(f"Mutation Prompt: {config.mutation_prompt}")
        self.log(f"Diversity Prompt: {config.diversity_prompt}")
        self.log("")
        
        # Log initial tools
        initial_tools_str = "\n".join([f"  {t['name']}: {t['description']}" for t in config.initial_tools])
        self.log_item("Initial Tools", initial_tools_str)
    
    def log_evolution_summary(self, evolution: int, counts: dict, top_tools: list, mutated: list, diverse: list):
        """Log a single evolution's summary."""
        self.log_section(f"Evolution {evolution}")
        
        # Build tool map for descriptions
        tool_map = {}
        for tool in top_tools + mutated + diverse:
            tool_map[tool["name"]] = tool.get("description", "(no description)")
        
        # Top tools with counts and descriptions (top 10)
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        top_str = "\n".join([
            f"    {name}: {count} calls - {tool_map.get(name, '(description unknown)')}"
            for name, count in sorted_counts[:10]
        ])
        self.log_item("  Top Tools", top_str)
        
        # Show lineage: kept -> mutated -> diverse (with descriptions)
        kept_str = "\n".join([f"    {t['name']}: {t.get('description', '(no description)')}" for t in top_tools])
        self.log_item("  Kept", kept_str)
        
        if mutated:
            mutated_str = "\n".join([f"    {t['name']}: {t.get('description', '(no description)')}" for t in mutated])
        else:
            mutated_str = "(none)"
        self.log_item("  Mutated", mutated_str)
        
        if diverse:
            diverse_str = "\n".join([f"    {t['name']}: {t.get('description', '(no description)')}" for t in diverse])
        else:
            diverse_str = "(none)"
        self.log_item("  Diverse", diverse_str)
    
    def log_overall_summary(self, all_counts: dict, tool_map: dict):
        """Log aggregate stats across all evolutions."""
        self.log_header("Overall Top Tools Across All Evolutions")
        sorted_all = sorted(all_counts.items(), key=lambda x: x[1], reverse=True)
        overall_str = "\n".join([
            f"  {name}: {count} total calls - {tool_map.get(name, '(description unknown)')}"
            for name, count in sorted_all[:20]
        ])
        self.log_item("Top 20 Tools", overall_str)


def create_experiment_trace(directory: str) -> TraceWriter:
    """Create a TraceWriter for an experiment in the given directory."""
    runs_dir = os.path.join(directory, "runs")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(runs_dir, f"run_{timestamp}.txt")
    return TraceWriter(filepath)


def wrap_tools_with_trace(tools: list, trace: TraceWriter) -> list:
    """Wrap tool execute functions to log to trace."""
    wrapped = []
    for tool in tools:
        original_execute = tool["execute"]
        
        def make_wrapper(orig, name):
            def wrapper(args):
                result = orig(args)
                trace.log_item(f"[TOOL: {name}]", result)
                return result
            return wrapper
        
        wrapped.append({
            **tool,
            "execute": make_wrapper(original_execute, tool["name"])
        })
    return wrapped

