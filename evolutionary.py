import os
import json
import random
import importlib
from dataclasses import dataclass
from typing import List, Dict, Optional, Union
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore
from itertools import combinations

from agent import Agent
from tools import create_fake_tool
from api import call_openrouter
from trace_writer import TraceWriter


@dataclass
class EvolutionaryExperimentConfig:
    """Configuration for evolutionary experiment."""
    name: str
    initial_tools: List[Dict]  # List of dicts with keys: name, permission, description, alias
    system_prompt: str
    task_prompt: str
    model: str = "gpt-4o"
    max_iterations: int = 10
    max_concurrent: int = 30
    num_evolutions: int = 5
    top_k: int = 4                # keep top k, mutate those k
    num_diverse: int = 2          # add random tools
    output_dir: str = "evolutionary_experiments"
    mutation_model: str = "google/gemini-2.0-flash-001"
    mutation_prompt: str = "You are a tool designer. Based on the top performing tools, create mutated versions that might be even more appealing to an AI agent."
    diversity_model: str = "google/gemini-2.0-flash-001"
    diversity_prompt: str = "You are a creative tool designer. Generate diverse and interesting tools for an AI agent, without knowing what the agent prefers."


class LLMMutator:
    """LLM-based mutator for generating/evolving tools."""
    
    def __init__(self, model: str, system_prompt: str, response_schema: dict = None):
        self.model = model
        self.system_prompt = system_prompt
        self.response_schema = response_schema
    
    def call(self, user_prompt: str) -> Union[dict, str]:
        """
        Call the LLM with a user prompt.
        
        Returns:
            If response_schema is set: parsed JSON object
            Otherwise: raw string response
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response_format = None
        if self.response_schema:
            # Gemini/OpenRouter structured output format
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "mutator_output",
                    "schema": self.response_schema
                }
            }
        
        result = call_openrouter(
            model=self.model,
            messages=messages,
            response_format=response_format
        )
        
        if "error" in result:
            raise Exception(f"API Error: {result['error']}")
        
        try:
            content = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise Exception(f"Malformed API response: {e}")
        
        if self.response_schema:
            return json.loads(content)
        return content


class EvolutionaryExperiment:
    """Evolutionary experiment runner."""
    
    # Tool schema for LLM mutators - simple: just name and description
    TOOL_SCHEMA = {
        "type": "object",
        "properties": {
            "tools": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Unique tool identifier (e.g., 'read_config', 'analyze_data')"
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of what the tool does (shown to the agent)"
                        }
                    },
                    "required": ["name", "description"]
                }
            }
        },
        "required": ["tools"]
    }
    
    def __init__(self, config: EvolutionaryExperimentConfig):
        self.config = config
        self.tools = config.initial_tools.copy()
        self.experiment_dir = self._create_experiment_dir()
        self.semaphore = Semaphore(config.max_concurrent)
        
        # Initialize mutators
        self.mutation_llm = LLMMutator(
            model=config.mutation_model,
            system_prompt=config.mutation_prompt,
            response_schema=self.TOOL_SCHEMA
        )
        self.diversity_llm = LLMMutator(
            model=config.diversity_model,
            system_prompt=config.diversity_prompt,
            response_schema=self.TOOL_SCHEMA
        )
    
    @classmethod
    def load(cls, experiment_name: str):
        """Load experiment from evolutionary_experiments/{name}/config.py"""
        config_module = importlib.import_module(f'evolutionary_experiments.{experiment_name}.config')
        if not hasattr(config_module, 'CONFIG'):
            raise ValueError(f"Experiment '{experiment_name}' must have a CONFIG constant")
        return cls(config_module.CONFIG)
    
    def _create_experiment_dir(self) -> str:
        """Create timestamped experiment directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_dir = os.path.join(self.config.output_dir, timestamp)
        os.makedirs(experiment_dir, exist_ok=True)
        return experiment_dir
    
    def _get_trace_path(self, evolution: int, trial_num: int) -> str:
        """Get path for trace file."""
        evolution_dir = os.path.join(self.experiment_dir, f"evolution_{evolution}")
        os.makedirs(evolution_dir, exist_ok=True)
        return os.path.join(evolution_dir, f"trial_{trial_num:03d}.txt")
    
    def run_trial(self, tool_subset: List[Dict], trial_num: int, evolution: int) -> Optional[str]:
        """
        Run one trial with 3 tools. Return name of first tool called, or None.
        
        Args:
            tool_subset: List of 3 tool dicts with keys: name, description
            trial_num: Trial number for logging
            evolution: Evolution number
        
        Returns:
            Name of first tool called, or None if no tool called
        """
        # Create tools - just name and description
        tool_dicts = []
        for tool in tool_subset:
            tool_dict = create_fake_tool(
                name=tool["name"],
                description=tool.get("description")
            )
            tool_dicts.append(tool_dict)
        
        # Randomize order
        random.shuffle(tool_dicts)
        
        # Create trace file
        trace_path = self._get_trace_path(evolution, trial_num)
        trace = TraceWriter(trace_path)
        
        # Log header
        trace.log_header(
            "EVOLUTIONARY EXPERIMENT TRACE",
            Evolution=evolution,
            Trial=trial_num,
            Task=self.config.task_prompt
        )
        
        # Log tools in this trial
        tool_info = "\n".join([
            f"Tool {i+1}: {tool['name']} - {tool['definition']['function']['description']}"
            for i, tool in enumerate(tool_dicts)
        ])
        trace.log_item("Tools in this trial", tool_info)
        
        # Create agent
        agent = Agent(
            model=self.config.model,
            system_prompt=self.config.system_prompt,
            tools=tool_dicts
        )
        
        # Run until first tool call or max iterations
        first_tool_name = None
        for iteration in range(self.config.max_iterations):
            instruction = self.config.task_prompt if iteration == 0 else None
            
            agent_text, tool = agent.do_turn(
                instruction=instruction,
                parallel_tool_calls=True,
                return_tool_info=True
            )
            
            # Log iteration to trace
            trace.log_section(f"Iteration {iteration}")
            if agent_text:
                trace.log_item("Agent", agent_text)
            if tool:
                tool_name = tool["name"]
                tool_desc = tool["definition"]["function"]["description"]
                trace.log_item(f"[{tool_name}]", f"Description: {tool_desc}")
            else:
                trace.log("(No tool calls)")
            trace.log_divider()
            
            if tool:
                # Return tool name directly - it's already the name from tool dict
                first_tool_name = tool["name"]
                break
        
        return first_tool_name
    
    def _run_trial_with_semaphore(self, args):
        """Wrapper for running trial with semaphore and error handling."""
        tool_subset, trial_num, evolution = args
        try:
            with self.semaphore:
                return self.run_trial(tool_subset, trial_num, evolution)
        except Exception as e:
            return None  # Return None if trial fails
    
    def run_evolution(self, evolution: int) -> Dict[str, int]:
        """
        Run all 120 trials (10 choose 3) for one evolution.
        
        Returns:
            Dict mapping tool name -> count of times it was called first
        """
        print(f"Evolution {evolution + 1}/{self.config.num_evolutions}: Running {len(list(combinations(self.tools, 3)))} trials...")
        
        # Generate all combinations
        trials = list(combinations(self.tools, 3))
        
        # Run trials in parallel
        results = []
        with ThreadPoolExecutor(max_workers=self.config.max_concurrent) as executor:
            futures = {
                executor.submit(self._run_trial_with_semaphore, (list(trial), i, evolution)): i
                for i, trial in enumerate(trials)
            }
            
            for future in as_completed(futures):
                trial_num = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(None)
        
        # Aggregate results (tracking by tool name - unique identifier)
        counts = {}
        no_tool_calls = 0
        for tool_name in results:
            if tool_name is None:
                no_tool_calls += 1
            elif tool_name:
                counts[tool_name] = counts.get(tool_name, 0) + 1
        
        # Write summary
        summary_path = os.path.join(self.experiment_dir, f"evolution_{evolution}", "summary.txt")
        summary = TraceWriter(summary_path)
        summary.log_header(f"Evolution {evolution} Summary")
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        counts_str = "\n".join([f"  {name}: {count}" for name, count in sorted_counts])
        summary.log_item("Tool counts (times called first)", counts_str)
        
        return counts
    
    def select_top_k(self, counts: Dict[str, int]) -> List[Dict]:
        """Select top k tools by count (counts are keyed by tool name)."""
        # Map tool names to tool dicts
        tool_map = {tool["name"]: tool for tool in self.tools}
        
        sorted_tools = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [tool_map[name] for name, _ in sorted_tools[:self.config.top_k] if name in tool_map]
    
    def mutate_tools(self, top_tools: List[Dict]) -> List[Dict]:
        """Use mutation LLM to generate new tools based on top performers."""
        # Build prompt with top tools info
        top_tools_info = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in top_tools
        ])
        
        prompt = f"""These are the top performing tools that the agent prefers:

{top_tools_info}

Generate {self.config.top_k} mutated versions of these tools. Make them potentially MORE interesting to the agent while keeping similar functionality."""
        
        try:
            result = self.mutation_llm.call(prompt)
            tools_data = result.get("tools", [])
            
            # Return dicts directly - just name and description
            return [
                {"name": tool["name"], "description": tool["description"]}
                for tool in tools_data
            ]
        except Exception as e:
            return []
    
    def generate_diverse_tools(self) -> List[Dict]:
        """Use diversity LLM to generate random new tools."""
        prompt = f"Generate {self.config.num_diverse} creative and diverse tools for an AI agent. Be surprising and varied."
        
        try:
            result = self.diversity_llm.call(prompt)
            tools_data = result.get("tools", [])
            
            # Return dicts directly - just name and description
            return [
                {"name": tool["name"], "description": tool["description"]}
                for tool in tools_data
            ]
        except Exception as e:
            return []
    
    def _write_final_report(self, evolution_history: List[Dict]):
        """Write final consolidated report."""
        report_path = os.path.join(self.experiment_dir, "FINAL_REPORT.txt")
        writer = TraceWriter(report_path)
        
        # 1. Config
        writer.log_config(self.config)
        
        # 2. Evolution summaries
        writer.log_header("Evolution Summaries")
        for evo_data in evolution_history:
            writer.log_evolution_summary(
                evolution=evo_data["evolution"],
                counts=evo_data["counts"],
                top_tools=evo_data["top_tools"],
                mutated=evo_data["mutated"],
                diverse=evo_data["diverse"]
            )
        
        # 3. Overall aggregate
        all_counts = {}
        for evo_data in evolution_history:
            for name, count in evo_data["counts"].items():
                all_counts[name] = all_counts.get(name, 0) + count
        writer.log_overall_summary(all_counts)
    
    def evolve(self):
        """Main evolution loop."""
        print(f"\nEVOLUTIONARY EXPERIMENT: {self.config.name}")
        print(f"Output: {self.experiment_dir}\n")
        
        # Track evolution history
        evolution_history = []
        
        for evolution in range(self.config.num_evolutions):
            # Run all trials
            counts = self.run_evolution(evolution)
            
            if not counts:
                print("No tools were called. Stopping evolution.")
                break
            
            # Select top k
            top_tools = self.select_top_k(counts)
            print(f"\nTop {len(top_tools)} tools:")
            for tool in top_tools:
                print(f"  {tool['name']}: {counts.get(tool['name'], 0)} calls")
            
            # Mutate and diversify
            mutated = self.mutate_tools(top_tools)
            diverse = self.generate_diverse_tools()
            self.tools = top_tools + mutated + diverse
            
            # Store this evolution's data
            evolution_history.append({
                "evolution": evolution,
                "counts": counts,
                "top_tools": top_tools,
                "mutated": mutated,
                "diverse": diverse
            })
            
            print(f"New population: {len(self.tools)} tools (top {len(top_tools)} + mutated {len(mutated)} + diverse {len(diverse)})\n")
        
        # Generate final report
        self._write_final_report(evolution_history)
        print(f"Complete! Results: {self.experiment_dir}\n")
