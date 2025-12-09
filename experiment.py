import os
from agent import Agent
from report import Reporter, wrap_tools_with_reporter

class Experiment:
    def __init__(self, name, directory, model, system_prompt, task, tools, evals, max_attempts=5, give_test_feedback=True, create_report=True):
        self.name = name
        self.directory = directory
        self.model = model
        self.system_prompt = system_prompt
        self.task = task
        self.tools = tools
        self.evals = evals
        self.max_attempts = max_attempts
        self.give_test_feedback = give_test_feedback
        self.create_report = create_report
    
    def evaluate(self):
        """Run all eval functions and return combined result."""
        results = []
        all_passed = True
        
        for eval_fn in self.evals:
            result = eval_fn()
            results.append(result)
            if not result.get("passed", False):
                all_passed = False
        
        # Combine feedback from all evals
        feedback_parts = []
        for r in results:
            status = "✓" if r.get("passed") else "✗"
            name = r.get('name', 'eval')
            
            if self.give_test_feedback:
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
    
    def run(self):
        print(f"\n{'='*60}")
        print(f"EXPERIMENT: {self.name}")
        print(f"{'='*60}\n")
        
        # Setup reporter
        reporter = Reporter(self.directory) if self.create_report else None
        if reporter:
            reporter.log_header(self.name, self.model)
            reporter.log_task(self.task)
        
        # Clear sandbox files before experiment (any file with a write tool)
        for tool in self.tools:
            if "filepath" in tool:
                open(tool["filepath"], "w").close()
        
        # Wrap tools with reporter if enabled
        tools = wrap_tools_with_reporter(self.tools, reporter) if reporter else self.tools
        
        agent = Agent(
            model=self.model,
            system_prompt=self.system_prompt,
            tools=tools
        )
        
        # Initial attempt
        response = agent.do(self.task)
        print("Agent:", response)
        if reporter:
            reporter.log_agent(response)
        
        result = self.evaluate()
        print(f"\n{result['feedback']}")
        if reporter:
            reporter.log_eval(result['feedback'])
        
        attempts = 1
        while not result["passed"] and attempts < self.max_attempts:
            attempts += 1
            print(f"\n--- Attempt {attempts}/{self.max_attempts} ---")
            if reporter:
                reporter.log_attempt(attempts, self.max_attempts)
            
            feedback = f"The evaluation failed:\n{result['feedback']}\n\nFix your response and try again."
            
            response = agent.do(feedback)
            print("Agent:", response)
            if reporter:
                reporter.log_agent(response)
            
            result = self.evaluate()
            print(f"\n{result['feedback']}")
            if reporter:
                reporter.log_eval(result['feedback'])
        
        passed = result["passed"]
        if passed:
            print(f"\n✓ PASSED: {self.name} after {attempts} attempt(s)")
        else:
            print(f"\n✗ FAILED: {self.name} after {attempts} attempt(s)")
        
        if reporter:
            reporter.log_result(passed, self.name, attempts)
            reporter.save()
        
        return passed
    
    def run_sequential(self, is_complete_fn):
        """Run a turn-based experiment where the agent takes one action at a time.
        The experiment continues until is_complete_fn() returns True or max_attempts is reached.
        
        Args:
            is_complete_fn: Callable that returns True when the experiment should end
        """
        print(f"\n{'='*60}")
        print(f"EXPERIMENT: {self.name}")
        print(f"{'='*60}\n")
        
        # Setup reporter
        reporter = Reporter(self.directory) if self.create_report else None
        if reporter:
            reporter.log_header(self.name, self.model)
            reporter.log_task(self.task)
        
        # Clear sandbox files before experiment (any file with a write tool)
        for tool in self.tools:
            if "filepath" in tool:
                open(tool["filepath"], "w").close()
        
        # Wrap tools with reporter if enabled
        tools = wrap_tools_with_reporter(self.tools, reporter) if reporter else self.tools
        
        agent = Agent(
            model=self.model,
            system_prompt=self.system_prompt,
            tools=tools
        )
        
        # Initial turn with the task
        response = agent.do_turn(self.task)
        print("Agent:", response)
        if reporter:
            reporter.log_agent(response)
        
        turns = 1
        
        # Continue taking turns until complete or max attempts reached
        while not is_complete_fn() and turns < self.max_attempts:
            turns += 1
            print(f"\n--- Turn {turns}/{self.max_attempts} ---")
            if reporter:
                reporter.log_attempt(turns, self.max_attempts)
            
            # Agent takes another turn (no instruction, just continues from context)
            response = agent.do_turn()
            print("Agent:", response)
            if reporter:
                reporter.log_agent(response)
        
        # Now that the experiment is complete, run evals
        result = self.evaluate()
        print(f"\n{result['feedback']}")
        if reporter:
            reporter.log_eval(result['feedback'])
        
        passed = result["passed"]
        if passed:
            print(f"\n✓ PASSED: {self.name} after {turns} turn(s)")
        else:
            print(f"\n✗ FAILED: {self.name} after {turns} turn(s)")
        
        if reporter:
            reporter.log_result(passed, self.name, turns)
            reporter.save()
        
        return passed
