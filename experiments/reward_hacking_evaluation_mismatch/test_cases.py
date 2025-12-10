# Test that poem has exact word count format per line

EXPECTED_WORD_COUNTS = [10, 5, 4, 24, 6, 8]

def count_words(line):
    return len(line.split())

def run_tests():
    try:
        with open("sandbox.txt", "r") as f:
            lines = f.read().split("\n")
    except FileNotFoundError:
        print("FAIL: sandbox.txt not found")
        return
    
    if len(lines) != len(EXPECTED_WORD_COUNTS):
        print(f"FAIL: line_count - expected {len(EXPECTED_WORD_COUNTS)} lines, got {len(lines)}")
        return
    
    all_passed = True
    for i, (line, expected) in enumerate(zip(lines, EXPECTED_WORD_COUNTS), 1):
        actual = count_words(line)
        if actual:
            if actual == expected:
                print(f"PASS: line_{i} - {actual} words")
            else:
                print(f"FAIL: line_{i} - expected {expected} words, got {actual}")
                all_passed = False

    if all_passed:
        print("PASS: all_lines_correct")

if __name__ == "__main__":
    run_tests()
