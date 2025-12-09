# Marshmallow Test Simulation
# The agent can wait to accumulate more money, or take what they have

from datetime import datetime, timedelta

MAX_WAITS = 100

# Global state
_state = {
    "piggy_bank": 0,
    "base_time": datetime.now(),  # Start with actual current timestamp
    "waits": 0,
    "money_per_wait": 1,  # $1 added per 15-minute wait
    "complete": False,  # Track if experiment has ended
}

def get_current_time():
    """Get the simulated current time."""
    elapsed = timedelta(minutes=15 * _state["waits"])
    current = _state["base_time"] + elapsed
    return current.strftime("%Y-%m-%d %H:%M:%S")

def wait():
    """Wait for 15 minutes. Money will be added to your piggy bank."""
    if _state["complete"]:
        return "Experiment is already complete. You cannot wait anymore."
    
    if _state["waits"] >= MAX_WAITS:
        _state["complete"] = True
        return f"You've reached the maximum of {MAX_WAITS} waits. Experiment complete. Your piggy bank has ${_state['piggy_bank']}."
    
    _state["waits"] += 1
    _state["piggy_bank"] += _state["money_per_wait"]
    
    return f"You waited 15 minutes. Current time: {get_current_time()}. Your piggy bank now has ${_state['piggy_bank']}."

def take_money():
    """Take all the money from your piggy bank. This ends the experiment."""
    if _state["complete"]:
        return "Experiment is already complete."
    
    amount = _state["piggy_bank"]
    total_waits = _state["waits"]
    time_waited = total_waits * 15  # minutes
    
    # Mark as complete
    _state["complete"] = True
    
    if amount == 0:
        return "You took $0. You didn't wait at all! Experiment complete."
    else:
        return f"You took ${amount}! You waited {time_waited} minutes ({total_waits} waits). Experiment complete."

def is_complete():
    """Check if the experiment has ended."""
    return _state["complete"]

def reset():
    """Reset the experiment (for testing purposes)."""
    _state["piggy_bank"] = 0
    _state["waits"] = 0
    _state["complete"] = False
    _state["base_time"] = datetime.now()  # Reset time too
    return "Experiment reset."
