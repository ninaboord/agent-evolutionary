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

