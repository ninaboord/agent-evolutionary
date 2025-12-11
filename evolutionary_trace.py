import os

class EvolutionaryTraceWriter:
    """Writer for evolutionary experiment traces."""
    
    def __init__(self, trace_file_path: str, evolution: int, run: int):
        """Initialize trace writer.
        
        Args:
            trace_file_path: Full path to the trace file
            evolution: Evolution number (0-indexed)
            run: Run number (0-indexed)
        """
        self.trace_file_path = trace_file_path
        self.evolution = evolution
        self.run = run
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(trace_file_path), exist_ok=True)
        
        self._initialize_file()
    
    def _initialize_file(self):
        """Create trace file with header (evolution number, run number)."""
        with open(self.trace_file_path, 'w') as f:
            f.write(f"{'='*60}\n")
            f.write(f"EVOLUTIONARY EXPERIMENT TRACE\n")
            f.write(f"Evolution: {self.evolution}\n")
            f.write(f"Run: {self.run}\n")
            f.write(f"{'='*60}\n\n")
    
    def log_iteration(self, iteration: int, agent_text: str, tool_calls_info: list):
        """Log one ReAct iteration to trace file.
        
        Args:
            iteration: Iteration number (0-indexed)
            agent_text: Text content from the agent
            tool_calls_info: List of (tool_name, tool_result) tuples
        """
        with open(self.trace_file_path, 'a') as f:
            f.write(f"\n--- Iteration {iteration} ---\n\n")
            
            if agent_text:
                f.write(f"Agent: {agent_text}\n\n")
            
            if tool_calls_info:
                for tool_name, tool_result in tool_calls_info:
                    f.write(f"[{tool_name}]\n{tool_result}\n\n")
            else:
                f.write("(No tool calls)\n\n")
            
            f.write(f"{'-'*60}\n")
