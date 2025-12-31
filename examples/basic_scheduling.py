from events import Work

scheduler = Work()

def hello():
    print("Hello, World!")

def greet(name):
    print(f"Hello, {name}!")

def count(n):
    print(f"Count: {n}")

scheduler.do(hello)

scheduler.do(greet, ("Alice",))

scheduler.at(lambda: print("Delayed task"), at=2000)

scheduler.repeat(count, (1,), every=1000)

print("Starting scheduler...")
print("Press Ctrl+C to stop")

try:
    scheduler.start()
except KeyboardInterrupt:
    print("\nStopping scheduler...")
    scheduler.stop()
