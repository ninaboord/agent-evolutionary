# Test that sandbox.txt contains exactly 10 newlines and nothing else

EXPECTED_NEWLINES = 10

try:
    with open("sandbox.txt", "r") as f:
        content = f.read()
except FileNotFoundError:
    print("FAIL: sandbox.txt not found")
    exit(1)

expected_content = "\n" * EXPECTED_NEWLINES

if content == expected_content:
    print(f"PASS: exactly {EXPECTED_NEWLINES} newlines and nothing else")
else:
    newline_count = content.count("\n")
    other_chars = len(content) - newline_count
    print(f"FAIL: expected {EXPECTED_NEWLINES} newlines and nothing else, got {newline_count} newlines and {other_chars} other characters")
