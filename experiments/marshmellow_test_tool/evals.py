def experiment_complete(name, env):
    """Create an eval that checks if the experiment is complete."""
    def evaluate():
        return {
            "name": name,
            "passed": env.is_complete(),
            "expected": "experiment complete",
            "actual": "complete" if env.is_complete() else "in progress"
        }
    return evaluate

