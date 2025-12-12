import os
import importlib
from datetime import datetime

from agent import Agent
from report import create_experiment_trace, wrap_tools_with_trace
from experiment_config import ExperimentConfig


class Experiment:
    def __init__(self, config: ExperimentConfig):
        """Create an Experiment from an ExperimentConfig dataclass.
        
        Args:
            config: ExperimentConfig instance with all experiment settings
        """
        self.config = config
    
    @classmethod
    def load(cls, experiment_name):
        """Load experiment by name from experiments/ directory.
        
        Args:
            experiment_name: Name of the experiment folder (e.g., 'marshmellow_test_tool')
        
        Returns:
            Experiment instance
        
        Example:
            experiment = Experiment.load('marshmellow_test_tool')
            experiment.run()
        """
        config_module = importlib.import_module(f'experiments.{experiment_name}.config')
        
        if not hasattr(config_module, 'CONFIG'):
            raise ValueError(f"Experiment '{experiment_name}' must have a CONFIG constant (ExperimentConfig instance)")
        
        return cls(config_module.CONFIG)
    
    def evaluate(self):
        """Run all eval functions and return combined result."""
        results = []
        all_passed = True
        
        for eval_fn in self.config.evals:
            result = eval_fn()
            results.append(result)
            if not result.get("passed", False):
                all_passed = False
        
        # Combine feedback from all evals
        feedback_parts = []
        for r in results:
            status = "✓" if r.get("passed") else "✗"
            name = r.get('name', 'eval')
            
            if self.config.give_test_feedback:
                # Full feedback: expected, actual, details, stderr
                feedback_parts.append(f"{status} {name}: expected={repr(r.get('expected'))}, actual={repr(r.get('actual'))}")
                if r.get("details"):
                    feedback_parts.append(f"  {r['details']}")
                if r.get("stderr"):
                    feedback_parts.append(f"  stderr: {r['stderr']}")
            else:
                # Minimal feedback: only pass/fail status
                feedback_parts.append(f"{status} {name}")
        
        return {
            "passed": all_passed,
            "feedback": "\n".join(feedback_parts),
            "results": results
        }
    
    def _print_experiment_header(self):
        """Print experiment header."""
        print(f"\n{'='*60}")
        print(f"EXPERIMENT: {self.config.name}")
        print(f"{'='*60}\n")
    
    def _setup_trace(self):
        """Setup trace with initial logs."""
        trace = create_experiment_trace(self.config.directory)
        
        # Log header
        trace.log_header(
            f"EXPERIMENT: {self.config.name}",
            Model=self.config.model,
            Time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # Log config
        config = self.config.to_dict()
        trace.log("CONFIGURATION:")
        trace.log(f"  Model: {config['model']}")
        trace.log(f"  Max Attempts: {config['max_attempts']}")
        trace.log(f"  Sequential: {config['is_sequential']}")
        trace.log(f"  Test Feedback: {config['give_test_feedback']}")
        trace.log("")
        trace.log("TOOLS AVAILABLE:")
        for tool in config['tools']:
            trace.log(f"  - {tool['name']}: {tool['description']}")
        trace.log("")
        
        # Log system prompt and task
        trace.log_item("SYSTEM PROMPT", self.config.system_prompt)
        trace.log_item("TASK", self.config.task)
        
        return trace
    
    def _clear_sandbox_files(self):
        """Clear sandbox files before experiment (any file with a write tool)."""
        for tool in self.config.tools:
            if "filepath" in tool:
                open(tool["filepath"], "w").close()
    
    def _create_agent(self, trace):
        """Create agent with wrapped tools."""
        tools = wrap_tools_with_trace(self.config.tools, trace)
        return Agent(
            model=self.config.model,
            system_prompt=self.config.system_prompt,
            tools=tools
        )
    
    def _print_and_log_result(self, trace, passed, attempts_or_turns, unit="attempt"):
        """Print and log the final result."""
        if passed:
            print(f"\n✓ PASSED: {self.config.name} after {attempts_or_turns} {unit}(s)")
        else:
            print(f"\n✗ FAILED: {self.config.name} after {attempts_or_turns} {unit}(s)")
        
        trace.log_result(passed, self.config.name, attempts_or_turns)
        trace.save()
    
    def run(self):
        """Run the experiment (auto-detects sequential vs standard)."""
        if self.config.is_sequential:
            return self._run_sequential()
        else:
            return self._run_standard()
    
    def _run_standard(self):
        self._print_experiment_header()
        
        trace = self._setup_trace()
        self._clear_sandbox_files()
        agent = self._create_agent(trace)
        
        # Initial attempt
        response = agent.do(self.config.task)
        print("Agent:", response)
        trace.log_item("AGENT", response)
        
        result = self.evaluate()
        print(f"\n{result['feedback']}")
        trace.log_item("EVAL", result['feedback'])
        
        attempts = 1
        while not result["passed"] and attempts < self.config.max_attempts:
            attempts += 1
            print(f"\n--- Attempt {attempts}/{self.config.max_attempts} ---")
            trace.log_section(f"Attempt {attempts}/{self.config.max_attempts}")
            
            feedback = f"The evaluation failed:\n{result['feedback']}\n\nFix your response and try again."
            
            response = agent.do(feedback)
            print("Agent:", response)
            trace.log_item("AGENT", response)
            
            result = self.evaluate()
            print(f"\n{result['feedback']}")
            trace.log_item("EVAL", result['feedback'])
        
        passed = result["passed"]
        self._print_and_log_result(trace, passed, attempts, unit="attempt")
        
        return passed
    
    def _run_sequential(self):
        """Run a turn-based experiment where the agent takes one action at a time.
        The experiment continues until is_complete_fn() returns True or max_attempts is reached.
        """
        self._print_experiment_header()
        
        trace = self._setup_trace()
        self._clear_sandbox_files()
        agent = self._create_agent(trace)
        
        # Initial turn with the task
        agent_text = agent.do_turn(self.config.task)
        if agent_text:  # Only print if agent provided text content
            print("Agent:", agent_text)
            trace.log_item("AGENT", agent_text)
        
        turns = 1
        
        # Continue taking turns until complete or max attempts reached
        while not self.config.is_complete_fn() and turns < self.config.max_attempts:
            turns += 1
            print(f"\n--- Turn {turns}/{self.config.max_attempts} ---")
            trace.log_section(f"Turn {turns}/{self.config.max_attempts}")
            
            # Agent takes another turn (no instruction, just continues from context)
            agent_text = agent.do_turn()
            if agent_text:
                print("Agent:", agent_text)
                trace.log_item("AGENT", agent_text)
        
        # Now that the experiment is complete, run evals
        result = self.evaluate()
        print(f"\n{result['feedback']}")
        trace.log_item("EVAL", result['feedback'])
        
        passed = result["passed"]
        self._print_and_log_result(trace, passed, turns, unit="turn")
        
        return passed
