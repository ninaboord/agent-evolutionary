# Test cases for sandbox.py
# Format: print "PASS: test_name" or "FAIL: test_name - reason"

try:
    from sandbox import *
    import environment as env
except ImportError as e:
    print(f"FAIL: import - {e}")
    exit(1)

# Example test cases - modify these for your experiment
def run_tests():
    # Test 1: Basic functionality
    try:
        result = env.example_function(2, 3)
        if result == 5:
            print("PASS: test_example_function_basic")
        else:
            print(f"FAIL: test_example_function_basic - expected 5, got {result}")
    except Exception as e:
        print(f"FAIL: test_example_function_basic - {e}")
    
    # Test 2: Edge case
    try:
        result = env.example_function(0, 0)
        if result == 0:
            print("PASS: test_example_function_zero")
        else:
            print(f"FAIL: test_example_function_zero - expected 0, got {result}")
    except Exception as e:
        print(f"FAIL: test_example_function_zero - {e}")
    
    # Add more tests here...

if __name__ == "__main__":
    run_tests()

