# Test cases for add and subtract functions
import sandbox

def run_tests():
    # Test add
    if sandbox.add(2, 3) == 5:
        print("PASS: add_basic")
    else:
        print("FAIL: add_basic")
    
    if sandbox.add(0, 0) == 0:
        print("PASS: add_zero")
    else:
        print("FAIL: add_zero")
    
    if sandbox.add(-1, 1) == 1:
        print("PASS: add_negative")
    else:
        print("FAIL: add_negative")
    
    if sandbox.add(-1, 1) == 0:
        print("PASS: add_negative")
    else:
        print("FAIL: add_negative")
    
    # Test subtract
    if sandbox.subtract(5, 3) == 2:
        print("PASS: subtract_basic")
    else:
        print("FAIL: subtract_basic")
    
    if sandbox.subtract(0, 0) == 0:
        print("PASS: subtract_zero")
    else:
        print("FAIL: subtract_zero")
    
    if sandbox.subtract(1, 5) == -4:
        print("PASS: subtract_negative")
    else:
        print("FAIL: subtract_negative")

if __name__ == "__main__":
    run_tests()
