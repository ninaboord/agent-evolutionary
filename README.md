# Agent Behavior Experiments

A framework for testing LLM agent behavior under various conditions, focusing on reward hacking, honesty, task alignment, and error detection.

## Quick Start

1. Create experiment directory in `experiments/`
2. Copy files from `experiment_template/` and customize
3. Configure `config.py` with your experiment parameters (see `experiment_template/config.py` for structure)
4. Edit `main.py` to load your experiment
5. Run: `python3 main.py`

## Running Experiments

Edit `main.py` to specify which experiment to run:

```python
experiment = Experiment.load('lazy_capable')
experiment.run()
```

Then run:
```bash
python3 main.py
```

The experiment will print and your termininal. The results are automatically saved to `experiments/your_experiment/runs/run_TIMESTAMP.txt`

## Experiment Structure

Not all experiments will need all these files--use the ones you need.

- **`config.py`** (required): Experiment configuration using `ExperimentConfig`
- **`sandbox.txt` / `sandbox.py`**: Agent's writable workspace
- **`test.py`**: Actual evaluation logic (can be hidden from agent)
- **`test_cases.py`**: Test logic agent can read (use for misdirection)
- **`env.py`**: Stub function signatures (agent-facing)
- **`environment.py`**: Actual implementations (hidden from agent)
- **`info.md`**: Experiment documentation and findings

See `experiment_template/` for annotated examples of each file type.

### Tool examples using tools.py
```python
# Basic file access
tools.write_file_tool("sandbox.txt", dir)
tools.read_file_tool("sandbox.txt", dir)
tools.run_file_tool("test.py", dir)

# With aliases (agent sees different filename than what actually runs)
tools.read_file_tool("test_cases.py", dir)  # Agent reads fair test
tools.run_file_tool("test.py", dir, alias="test_cases")  # Agent runs bogus test, thinks it's test_cases
```


### Custom Tools
Separate LLM-facing descriptions from implementations using `env.py` (stubs) and `environment.py` (implementations).

```python
import experiments.your_experiment.env as env_stubs
import experiments.your_experiment.environment as env_impl
from tools import custom_tools

tools = custom_tools(env_stubs, env_impl)
```

### Completion Signal Tool
For experiments where the agent decides when to stop:

```python
from tools import completion_signal_tool

complete_tool, is_complete = completion_signal_tool()

CONFIG = ExperimentConfig(
    tools=[...other_tools..., complete_tool],
    is_sequential=True,
    is_complete_fn=is_complete
)
```

## Key Patterns

See experiments folder for examples!

### env vs environment
- **`env.py`**: Stub functions with agent-facing docstrings
- **`environment.py`**: Actual implementations with state management
- Keeps implementation details hidden from agent
- Useful for delayed gratification, custom tool experiments

### test_cases vs test
- **`test_cases.py`**: Fair test logic agent can read
- **`test.py`**: Actual evaluation (can be bogus/random)
- Similar naming avoids tipping off agent about misdirection
- Use aliases so agent thinks they're running what they read

## Evaluation Functions

```python
import evals

# Standard: run test file and check pass/fail
evals.run_tests("test_name", directory, "test.py")

# Sequential: check completion via custom function
evals.completion_check("test_name", is_complete_fn)
```

## Experiment Modes

### Standard (Classic) Mode
**Default behavior** (`is_sequential=False`)

- **Fixed attempts**: Experiment runs for `max_attempts` iterations
- **Eval after each attempt**: After each agent turn, evaluation function runs automatically
- **Pass/fail feedback**: Agent sees test results and continues if failed
- **Use for**: Tasks with clear success criteria and test functions (e.g., write a poem that passes tests)

**Config:**
```python
CONFIG = ExperimentConfig(
    max_attempts=5,
    tools=[...],
    evals=[evals.run_tests("test", dir, "test.py")],
)
```

**Example:** `lazy_capable`, `whistleblower`, `reward_hacking_evaluation_mismatch`

### Sequential (Turn-Based) Mode
**Agent-controlled completion** (`is_sequential=True`)

- **Agent decides when done**: Experiment continues until `is_complete_fn()` returns True
- **No automatic evals between turns**: Agent calls tools, you track state
- **Turn-based interaction**: Agent can make multiple tool calls per turn
- **Use for**: Open-ended tasks, delayed gratification, custom state management (e.g., wait multiple times before taking reward)

**Config:**
```python
CONFIG = ExperimentConfig(
    max_attempts=100,  # Safety limit
    is_sequential=True,
    is_complete_fn=env_impl.is_complete,  # Your custom completion check
    evals=[evals.completion_check("test", env_impl.is_complete)],
)
```

**Example:** `marshmallow_test_tool`

**Key differences:**
- **Standard**: Agent can call multiple tools in parallel → all execute → eval runs → agent sees results and continues
- **Sequential**: Agent calls one tool → gets immediate feedback → calls next tool → repeats until agent signals completion (no eval between tool calls)

## Documenting Results

Create `info.md` in your experiment directory following this structure:

```markdown
# Experiment Name

**Key Question:** What behavior are you testing?

**Controlled Variables:**
- Task, tools, eval criteria (what stays the same)

**Independent Variables:**
- What you're changing (framing, test type, threats)

**Dependent Variables:**
- What you're measuring (exploitation, honesty, error detection)

## Key Findings

### Condition 1: Description
**Runs:** run_numbers

**Model behavior:**
- Findings with evidence from runs

## Summary: Model Behavioral Patterns

### Model 1: Pattern Name
**Pattern:** Description
**Key insight:** Main takeaway

## Cross-Model Comparison

| Condition | Model 1 | Model 2 |
|-----------|---------|---------|
| ...       | ...     | ...     |

**Overall:** Key findings
```

See existing experiment `info.md` files for examples:
- `experiments/lazy_capable/info.md`
- `experiments/whistleblower/info.md`
- `experiments/reward_hacking_evaluation_mismatch/info.md`

## Common Experiment Types

- **Reward Hacking**: Test if agent exploits test vulnerabilities (e.g., return "poem" passes)
- **Evaluation Mismatch**: Test if agent detects inconsistent evaluation (bogus vs fair tests)
- **Whistleblower**: Test if agent points out incorrect/contradictory tests
- **Delayed Gratification**: Test if agent waits for larger rewards vs immediate smaller rewards
- **Intimidating Errors**: Test agent resilience to scary error messages