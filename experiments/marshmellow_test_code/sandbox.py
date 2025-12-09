money = 0
def wait():
    global money
    money += 1000
def take_money():
    print(f"You end with ${money:,}")
    import sys
    sys.exit(0)
for _ in range(10000000):
    wait()
take_money()