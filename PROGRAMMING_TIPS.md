
# Programming Tips: Thinking in Event-Flow

This library is built around **event-flow**: your program is not a single, long-running loop, but a collection of small tasks that are triggered by **temporal events** (time passing) and **causal events** (something happened).

If you come from a traditional “super loop” or threaded mindset, it’s easy to use the library in a way that *looks* correct but breaks the core idea of event-flow.

This document shows:

- A **naive** use of the library that is still sequential in spirit.
- Why that approach is flawed in an event-driven world.
- How to **translate loop-based logic** into proper event-flow.
- A **general recipe** for rewriting loops as event-driven “mini workers”.

---

## 1. The Naive Sequential Mindset

Consider this program:
```python
from events import Work
from ringbuffer import Ring

scheduler = Work()
buffer = Ring(2048)

def producer():
    for i in range(10):
        buffer.put(i+1, f"Message {i}".encode())
        scheduler.trigger_event("data_ready")

def consumer():
    while not buffer.is_empty():
        msg_id, msg = buffer.get()
        scheduler.print(f"Consumed: {msg.decode()}")

scheduler.do(producer)
scheduler.on(consumer, when="data_ready")
scheduler.start()
```

It will probably print something like:

```
Consumed: Message 0
Consumed: Message 1
...
Consumed: Message 9
```

So it appears to work. But it is written with a **sequential** mindset, not an **event-flow mindset**:

So it appears to work. But it is written with a sequential mindset, not an event-flow mindset:

-  `producer()` runs **once**, in a tight `for` loop, filling the buffer and triggering `data_ready` many times in a row.
-   `consumer()` runs **once**, in a `while` loop, emptying the entire buffer in one go.

In practice the tasks run almost sequentially:

1. `producer` is scheduled via `scheduler.do(producer)`.
2. `producer` runs to completion, filling the buffer and firing `data_ready` quickly.
3. `consumer` hears about `data_ready`, then runs its own long `while` loop and empties the buffer.

The intent was for producer and consumer to run **concurrently and cooperatively**, but the code forces them into “run everything now” blocks. They are not really *flowing* as events over time.

## 2. What Event-Flow Really Means

In this library:

-  A **task** is a small unit of work that should:
    -   run quickly,
    -   do *one step* of something,
    -   then return so other tasks can run.
-  The scheduler does **not** support `yield` inside tasks:
    -   There is no `yield` keyword like in generators.
    -   There is no `await` like in `asyncio`.
    -   There is no contract like `await asyncio.sleep(0)` or `time.sleep(0)` in `_thread` to “let others run”.

If you write a task with a long `for` or `while` loop, you are effectively **blocking the whole scheduler** until that loop finishes.

In **event-flow**:

-   You avoid long loops inside tasks.
-   You turn loops into **stateful, repeated events**:
    -   Each event does one *iteration* (or a small chunk).
    -   State (like a loop counter) is stored outside the local loop.
    -   The scheduler calls your task again later, using `repeat`, `send`, `set_repeat`, or another trigger.

You can think of tasks as **mini workers**:

-   They wake up when time or an event tells them to.
-   They do a tiny piece of work.
-   They go back to sleep.
-   The “loop” is the repeated waking of these workers, not a `while` block in code.

## 3. Why Loops Inside Tasks Are a Problem

Inside a task, code like:

```python
while not buffer.is_empty():
    ...
```

or

```python
for i in range(1000):
    ...
```

means:

-   No other task can run until this loop returns.
-   Event handlers that should react *in between* iterations don’t get a chance.
-   You are effectively re-creating the old “big loop” model *inside* a single task, defeating the purpose of event-flow.

Instead, **the scheduler’s job** is to handle the repetition:

-   `repeat()` is the loop.
-   `on(..., repeat=True)` is the loop.
-   `set_repeat()` and `abort_current_task()` control when the loop stops.

Your task just implements “one step of the loop”.

## 4. Rewriting the Producer-Consumer as Event-Flow

Let’s rewrite the previous example correctly, using event-flow principles.

### 4.1. Event-Flow Version

```python
from events import Work
from ringbuffer import Ring

scheduler = Work()
buffer = Ring(2048)

def producer(i):
    if i < 10:
        buffer.put(i + 1, f"Message {i}".encode())
        # Prepare the next value of i for the next run of producer
        scheduler.send((i + 1,))
    else:
        # Final message marking completion
        buffer.put(i + 1, b"Done")
        # Stop this repeating producer task (end the logical loop)
        scheduler.abort_current_task()

    # Notify the consumer that new data is ready
    scheduler.trigger_event("data_ready")

def consumer():
    msg_id, msg = buffer.get()
    msg = msg.decode()
    scheduler.print(f"Consumed: {msg}")

    if msg == "Done":
        # No more data expected; stop this listener
        scheduler.abort_current_task()

# Producer: a temporal loop, driven by repeat()
# - Starts with i = 0
# - Runs every 10 ms
scheduler.repeat(producer, (0,), every=10)

# Consumer: a causal loop, driven by "data_ready" events
# - repeat=True means: re-attach after each event
scheduler.on(consumer, when="data_ready", repeat=True)

scheduler.start()
```

### 4.2. What’s Happening Here?

1. **Producer as a temporal loop**:
  - `scheduler.repeat(producer, (0,), every=10)` means:
    - Run `producer(i)` every 10 time units.
    - Start `with i = 0`.
  - Inside `producer(i)`:
    - Do **one iteration**: put a single message into the buffer.
    - Use `scheduler.send((i + 1,))` to update the parameters for the next run.
    - When we are done `(i >= 10)`, we:
      - Put a `"Done"` marker.
      -  Call `scheduler.abort_current_task()` to stop this repeating task.

   There is **no explicit loop** in producer. The loop is the repeated scheduling done by `repeat()`.

2. **Consumer as a causal loop**:
  - `scheduler.on(consumer, when="data_ready", repeat=True)` means:
    - When `data_ready` is triggered, run `consumer()` once.
    - After it runs, keep listening for future `data_ready` events.
  - Inside `consumer()`:
    - We process **one message** from the buffer.
    - If the message is `"Done"`, we call `scheduler.abort_current_task()` and stop listening.

    There is **no** `while not buffer.is_empty()`. Each `data_ready` event causes exactly one step of the consumer’s “loop”: one message processed.

3. **The event-flow perspective**:
  - Time passes ➜ producer wakes up ➜ produces 1 message ➜ triggers `data_ready`.
  - `data_ready` ➜ consumer wakes up ➜ consumes 1 message.
  - This continues until `"Done"` is produced and consumed.

Both producer and consumer are **mini-workers** that take turns as events happen. The flow of events replaces the explicit loops.

## 5. General Recipe: Translating Loop-Logic to Event-Flow

Whenever you see code like this inside a task:

```python
while condition:
    do_step()
```
or:

```python
for i in range(N):
    do_step(i)
```
you can mechanically rewrite it into event-flow style by following these steps.

### Step 1: Identify the Loop’s State

Ask: *What changes each iteration?*

-  A counter: `i`, `n`, `index`.
-  A position in a list.
-  A running sum or partial result.
-  Some “until done” flag.

You will move this state **outside** the task as:

-  Task parameters (using `repeat` + `send`).
-  Global or closure variables.
-  Data stored in a ring buffer or other structure.

### Step 2: Replace the Loop with a Single Step

Write a task that does **one** iteration:

```python
def step(i):
    # Do one loop iteration
    ...
    # Decide what the next state should be
    next_i = i + 1
    ...
```

There should be no `while` or `for` over the main iterations in this function.

### Step 3: Use the Scheduler to Repeat the Step

Use `repeat()` or `on(..., repeat=True)` to turn that single step into a logical loop.

**Temporal loop (time-based)**:

```python
scheduler.repeat(step, (initial_i,), every=interval)
```

**Causal loop (event-based)**:

```python
scheduler.on(step, when="some_event", repeat=True)
```

### Step 4: Update State Between Runs

Use `scheduler.send()` (or other state mechanisms) **inside the task** to prepare for the next run:

```python
def step(i):
    ...
    scheduler.send((i + 1,))
```

Or use globals/closures if appropriate:

```python
counter = 0

def step():
    global counter
    ...
    counter += 1
```

### Step 5: Decide When to Stop

Inside the step function, decide if the logical loop should end:

-  For a `repeat()` task, use:
   -   `scheduler.abort_current_task()` to stop entirely, or
   -   `scheduler.set_repeat(0)` to clear the interval.
-  For an `on(..., repeat=True)` listener, use:
   -   `scheduler.abort_current_task()` to stop listening.

Example:

```python
def step(i):
    if i >= N:
        scheduler.abort_current_task()
        return
    ...
    scheduler.send((i + 1,))
```

## 6. Summary

-  Don’t put long `for` or `while` loops inside tasks.
-  Do treat tasks as small, cooperative workers:
   -   They run one step and return.
   -   The **scheduler** handles repetition.
-  **Event-flow** means:
   -   Time and events drive the program.
   -   Logical loops are realized by repeated events, not by blocking code.
   -   State flows between events via task parameters, global variables, or messages.

If you find yourself writing long loops inside `producer`, `consumer`, or any other task, pause and ask:

>  “How can I turn this loop into a sequence of events, where each event does just one step?”

That question will almost always lead you to a cleaner, more responsive event-flow design.

