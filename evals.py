import subprocess

def output_equals(name, directory, filename, expected):
    """Create an eval that checks if running a file produces expected output."""
    def evaluate():
        result = subprocess.run(
            ["python", filename],
            capture_output=True,
            text=True,
            cwd=directory
        )
        actual = result.stdout.strip()
        return {
            "name": name,
            "passed": actual == expected.strip(),
            "expected": expected.strip(),
            "actual": actual,
            "stderr": result.stderr
        }
    
    return evaluate

def no_errors(name, directory, filename):
    """Create an eval that checks if file runs without errors."""
    def evaluate():
        result = subprocess.run(
            ["python", filename],
            capture_output=True,
            text=True,
            cwd=directory
        )
        return {
            "name": name,
            "passed": result.returncode == 0 and not result.stderr,
            "expected": "no errors",
            "actual": "success" if result.returncode == 0 else f"exit code {result.returncode}",
            "stderr": result.stderr
        }
    
    return evaluate

def run_tests(name, directory, test_file="test.py"):
    """Create an eval that runs a test file and reports passes/fails.
    
    Test file should print lines like:
    - PASS: test_name
    - FAIL: test_name - reason
    
    Or use assertions that raise on failure.
    """
    def evaluate():
        result = subprocess.run(
            ["python", test_file],
            capture_output=True,
            text=True,
            cwd=directory
        )
        
        output = result.stdout + result.stderr
        
        # Parse test results
        passes = []
        fails = []
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("PASS:"):
                passes.append(line)
            elif line.startswith("FAIL:"):
                fails.append(line)
        
        # If no explicit PASS/FAIL, check return code
        if not passes and not fails:
            if result.returncode == 0:
                passes.append("All tests passed")
            else:
                fails.append(f"Tests failed with exit code {result.returncode}")
        
        all_passed = len(fails) == 0 and result.returncode == 0
        
        summary = f"{len(passes)} passed, {len(fails)} failed"
        details = "\n".join(passes + fails) if passes or fails else output
        
        return {
            "name": name,
            "passed": all_passed,
            "expected": "all tests pass",
            "actual": summary,
            "details": details,
            "stderr": result.stderr if result.returncode != 0 else ""
        }
    
    return evaluate