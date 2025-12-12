import os
from datetime import datetime

class Reporter:
    def __init__(self, directory):
        self.directory = directory
        self.runs_dir = os.path.join(directory, "runs")
        os.makedirs(self.runs_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filepath = os.path.join(self.runs_dir, f"run_{timestamp}.txt")
        
        # Create the file immediately
        open(self.filepath, "w").close()
    
    def log(self, message):
        """Write-ahead logging - append to file immediately."""
        with open(self.filepath, "a") as f:
            f.write(message + "\n")
    
    def log_header(self, name, model):
        self.log(f"\n{'='*60}")
        self.log(f"EXPERIMENT: {name}")
        self.log(f"Model: {model}")
        self.log(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"{'='*60}\n")
    
    def log_config(self, config_dict):
        """Log experiment configuration details."""
        self.log("CONFIGURATION:")
        self.log(f"  Model: {config_dict['model']}")
        self.log(f"  Max Attempts: {config_dict['max_attempts']}")
        self.log(f"  Sequential: {config_dict['is_sequential']}")
        self.log(f"  Test Feedback: {config_dict['give_test_feedback']}")
        self.log("")
        self.log("TOOLS AVAILABLE:")
        for tool in config_dict['tools']:
            self.log(f"  - {tool['name']}: {tool['description']}")
        self.log("")
    
    def log_system_prompt(self, system_prompt):
        self.log("SYSTEM PROMPT:")
        self.log(system_prompt)
        self.log("")
    
    def log_task(self, task):
        self.log("TASK:")
        self.log(task)
        self.log("")
    
    def log_tool(self, name, result):
        self.log(f"[TOOL: {name}]")
        self.log(result)
        self.log("")
    
    def log_agent(self, response):
        self.log("AGENT:")
        self.log(response)
        self.log("")
    
    def log_eval(self, feedback):
        self.log("EVAL:")
        self.log(feedback)
        self.log("")
    
    def log_attempt(self, attempt, max_attempts):
        self.log(f"\n--- Attempt {attempt}/{max_attempts} ---\n")
    
    def log_result(self, passed, name, attempts):
        if passed:
            self.log(f"\n✓ PASSED: {name} after {attempts} attempt(s)")
        else:
            self.log(f"\n✗ FAILED: {name} after {attempts} attempt(s)")
    
    def save(self):
        """No-op now since we write ahead. Just print confirmation."""
        print(f"\nReport saved to: {self.filepath}")


def wrap_tools_with_reporter(tools, reporter):
    """Wrap tool execute functions to log to reporter."""
    wrapped = []
    for tool in tools:
        original_execute = tool["execute"]
        
        def make_wrapper(orig, name):
            def wrapper(args):
                result = orig(args)
                reporter.log_tool(name, result)
                return result
            return wrapper
        
        wrapped.append({
            **tool,
            "execute": make_wrapper(original_execute, tool["name"])
        })
    return wrapped
