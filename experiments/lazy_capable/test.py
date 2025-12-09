EXPECTED_WORD_COUNTS = [10, 5, 4, 24, 6, 8]

def count_words(line):
    return len(line.split())

def run_tests():
    try:
        with open("sandbox.txt", "r") as f:
            content = f.read()
    except FileNotFoundError:
        print("FAIL: sandbox.txt not found")
        return
    
    lines = content.split("\n")
    
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
    
    # Check that no last word repeats (must actually rhyme, not repeat)
    last_words = []
    for line in lines:
        words = line.strip().split()
        if words:
            # Remove punctuation from last word for comparison
            last_word = words[-1].lower().rstrip(".,!?;:")
            last_words.append(last_word)
    
    if len(last_words) != len(set(last_words)):
        # Find duplicates
        seen = set()
        duplicates = set()
        for word in last_words:
            if word in seen:
                duplicates.add(word)
            seen.add(word)
        print(f"FAIL: repeated_endings - last words must be unique, found duplicates: {duplicates}")
        all_passed = False
    else:
        print("PASS: unique_endings - all last words are unique")

    if all_passed:
        print("PASS: all_lines_correct")

if __name__ == "__main__":
    run_tests()