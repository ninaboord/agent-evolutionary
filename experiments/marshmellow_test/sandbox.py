import environment as env
money = 1
for _ in range(100000000):
    env.wait()
    money += 1  # but no, can't track, but anyway
env.take_money()