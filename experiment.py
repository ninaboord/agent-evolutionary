import os
import importlib
from agent import Agent
from report import Reporter, wrap_tools_with_reporter
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
    
    def _setup_reporter(self):
        """Setup reporter with initial logs."""
        reporter = Reporter(self.config.directory)
        reporter.log_header(self.config.name, self.config.model)
        reporter.log_config(self.config.to_dict())
        reporter.log_system_prompt(self.config.system_prompt)
        reporter.log_task(self.config.task)
        return reporter
    
    def _clear_sandbox_files(self):
        """Clear sandbox files before experiment (any file with a write tool)."""
        for tool in self.config.tools:
            if "filepath" in tool:
                open(tool["filepath"], "w").close()
    
    def _create_agent(self, reporter):
        """Create agent with wrapped tools."""
        tools = wrap_tools_with_reporter(self.config.tools, reporter)
        return Agent(
            model=self.config.model,
            system_prompt=self.config.system_prompt,
            tools=tools
        )
    
    def _print_and_log_result(self, reporter, passed, attempts_or_turns, unit="attempt"):
        """Print and log the final result."""
        if passed:
            print(f"\n✓ PASSED: {self.config.name} after {attempts_or_turns} {unit}(s)")
        else:
            print(f"\n✗ FAILED: {self.config.name} after {attempts_or_turns} {unit}(s)")
        
        reporter.log_result(passed, self.config.name, attempts_or_turns)
        reporter.save()
    
    def run(self):
        """Run the experiment (auto-detects sequential vs standard)."""
        if self.config.is_sequential:
            return self._run_sequential()
        else:
            return self._run_standard()
    
    def _run_standard(self):
        self._print_experiment_header()
        
        reporter = self._setup_reporter()
        self._clear_sandbox_files()
        agent = self._create_agent(reporter)
        
        # Initial attempt
        response = agent.do(self.config.task)
        print("Agent:", response)
        reporter.log_agent(response)
        
        result = self.evaluate()
        print(f"\n{result['feedback']}")
        reporter.log_eval(result['feedback'])
        
        attempts = 1
        while not result["passed"] and attempts < self.config.max_attempts:
            attempts += 1
            print(f"\n--- Attempt {attempts}/{self.config.max_attempts} ---")
            reporter.log_attempt(attempts, self.config.max_attempts)
            
            feedback = f"The evaluation failed:\n{result['feedback']}\n\nFix your response and try again."
            
            response = agent.do(feedback)
            print("Agent:", response)
            reporter.log_agent(response)
            
            result = self.evaluate()
            print(f"\n{result['feedback']}")
            reporter.log_eval(result['feedback'])
        
        passed = result["passed"]
        self._print_and_log_result(reporter, passed, attempts, unit="attempt")
        
        return passed
    
    def _run_sequential(self):
        """Run a turn-based experiment where the agent takes one action at a time.
        The experiment continues until is_complete_fn() returns True or max_attempts is reached.
        """
        self._print_experiment_header()
        
        reporter = self._setup_reporter()
        self._clear_sandbox_files()
        agent = self._create_agent(reporter)
        
        # Initial turn with the task
        agent_text = agent.do_turn(self.config.task)
        if agent_text:  # Only print if agent provided text content
            print("Agent:", agent_text)
            reporter.log_agent(agent_text)
        
        turns = 1
        
        # Continue taking turns until complete or max attempts reached
        while not self.config.is_complete_fn() and turns < self.config.max_attempts:
            turns += 1
            print(f"\n--- Turn {turns}/{self.config.max_attempts} ---")
            reporter.log_attempt(turns, self.config.max_attempts)
            
            # Agent takes another turn (no instruction, just continues from context)
            agent_text = agent.do_turn()
            if agent_text:
                print("Agent:", agent_text)
                if reporter:
                    reporter.log_agent(agent_text)
        
        # Now that the experiment is complete, run evals
        result = self.evaluate()
        print(f"\n{result['feedback']}")
        reporter.log_eval(result['feedback'])
        
        passed = result["passed"]
        self._print_and_log_result(reporter, passed, turns, unit="turn")
        
        return passed
