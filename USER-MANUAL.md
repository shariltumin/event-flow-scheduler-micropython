# User Manual

## MicroPython Event Scheduler & Ring Buffer - Complete API Reference

## Table of Contents

1. [Design Philosophy](#design-philosophy)

2. [Event Scheduler (events.py)](#event-scheduler)
- [Work Class](#work-class)
- [Task Scheduling Methods](#task-scheduling-methods)
- [Event Management](#event-management)
- [Task Control](#task-control)
- [Utility Methods](#utility-methods)

3. [Ring Buffer (ringbuffer.py)](#ring-buffer)
- [Ring Class](#ring-class)
- [Buffer Operations](#buffer-operations)
- [Message Retrieval](#message-retrieval)
- [Utility Methods](#buffer-utility-methods)

4. [Advanced Usage](#advanced-usage)

5. [Best Practices](#best-practices)

6. [Troubleshooting](#troubleshooting)

7. [Performance Tips](#performance-tips)

8. [Memory Usage](#memory-usage)

9. [Thread Safety](#thread-safety)

10. [Version History](#version-history)

11. [Support](#support)

---

## Design Philosophy

Embedded systems do not live in a static world. Voltages drift, sensors update, packets arrive and vanish, buttons are pressed and then released. Nothing holds still; everything is in motion.

This library takes that impermanence seriously.

Instead of pretending that your program is a fixed sequence of steps, it treats it as a choreography of **events** unfolding in time. An event is a *waitable* or *actionable* happening---something your system can respond to.

We focus on two fundamental kinds of events:

1. **Temporal events** -- things that happen *when the time comes*:
   - after a delay,
   - at a moment,
   - or with a rhythm (intervals, schedules, timeouts).

2. **Causal events** -- things that happen *because something else happened*:
   - a button was pressed,
   - a packet arrived,
   - a threshold was crossed,
   - one task signaled another.

The **Event Scheduler** (`events.py`) lets you describe both:

- *"Do this after N milliseconds."* (temporal)

- *"When this happens, do that."* (causal)

The **Ring Buffer** (`ringbuffer.py`) complements this by handling the messages that events produce---short-lived pieces of information that matter for a moment, then can be forgotten.

The core idea is:

> Make time and change explicit in code, instead of scattering them across sleeps, flags, and ad-hoc callbacks.

The rest of this manual shows how each API fits into this model of impermanent, event-driven behavior.

## Event Scheduler

The Event Scheduler provides a cooperative multitasking system for MicroPython, allowing you to schedule tasks with delays, repeating intervals, and event-driven triggers. In practice, this means you describe **when** and **why** things should happen, and the scheduler orchestrates the unfolding.

### Work Class

#### Constructor

```python
Work(max_tasks=256)
```

Creates a new scheduler instance.

**Parameters:**

- max_tasks` (int, optional): Maximum number of concurrent tasks. Default: 256

**Example:**

```python
from events import Work

scheduler = Work(max_tasks=100)
```

**Raises:**

- `ValueError`: If max_tasks is not a positive integer

### Task Scheduling Methods

In terms of the philosophy:

- `do`, `at`, and `repeat` define **temporal events** .

- They say *"at this time, let this happen."*

**`do()`**

Schedule a task to run immediately (on next scheduler cycle).

```python
do(job=None, params=(), task_id=0)
```

**Parameters:**

- `job` (callable): Function to execute

- `params` (tuple, optional): Arguments to pass to the function

- `task_id` (int, optional): Specific task ID to use (0 = auto-generate)

**Returns:**

- `int`: Task ID on success, `None` on failure

**Example:**

```python
def greet(name):
    print(f"Hello, {name}!")

task_id = scheduler.do(greet, ("Alice",))
```

---

**`at()`**

Schedule a task to run after a delay.

```python
at(job=None, params=(), at=0, task_id=0)
```

**Parameters:**

- `job` (callable): Function to execute

- `params` (tuple, optional): Arguments to pass to the function

- `at` (int): Delay in milliseconds before execution

- `task_id` (int, optional): Specific task ID to use

**Returns:**

- `int`: Task ID on success, `None` on failure

**Example:**

```python
def delayed_task():
    print("Executed after 5 seconds")

scheduler.at(delayed_task, at=5000)
```
---

**`repeat()`**

Schedule a task to run repeatedly at fixed intervals.

```python
repeat(job=None, params=(), at=0, every=0, task_id=0)
```

**Parameters:**

- `job` (callable): Function to execute

- `params` (tuple, optional): Arguments to pass to the function

- `at` (int, optional): Initial delay in milliseconds

- `every` (int): Repeat interval in milliseconds (must be > 0)

- `task_id` (int, optional): Specific task ID to use

**Returns:**

- `int`: Task ID on success, `None` on failure

**Example:**

```python
def heartbeat():
    print("Heartbeat")

scheduler.repeat(heartbeat, every=1000)
```
---

**`on()`**

Schedule a task to run when a specific event is triggered.

```python
on(job=None, params=(), when=None, at=0, repeat=False, task_id=0)
```

**Parameters:**

- `job` (callable): Function to execute

- `params` (tuple, optional): Arguments to pass to the function

- `when` (str): Event flag name to wait for (required)

- `at` (int, optional): Delay after event trigger

- `repeat` (bool/int, optional): Whether to re-register for the event after execution

- `task_id` (int, optional): Specific task ID to use

**Returns:**

- `int`: Task ID on success, `None` on failure

**Example:**

```python
def on_sensor_data(value):
    print(f"Sensor reading: {value}")

scheduler.on(on_sensor_data, when="sensor_event")
```

This is your main tool for expressing **causal events** : "when sensor_event happens, run on_sensor_data."

---

### Event Management

Event management methods are about *connecting causes and effects*.

**`trigger_event()`**

Trigger an event, causing all tasks waiting for it to execute.

```python
trigger_event(flag=None, pkg=())
```

**Parameters:**

- `flag` (str): Event flag name

- `pkg` (tuple, optional): Data to pass to waiting tasks

**Returns:**

- `int`: Number of tasks triggered

**Example:**

```python
count = scheduler.trigger_event("sensor_event", (42,))
print(f"Triggered {count} tasks")
```

**`await_event()`**

Make a task wait for a specific event.

```python
await_event(flag=None, task_id=0)
```

**Parameters:**

- flag (str): Event flag name

- task_id (int, optional): Task ID (0 = current task)

**Returns:**

- `bool`: True on success, False on failure

**Example:**

```python
def my_task():
    scheduler.await_event("data_ready")

scheduler.do(my_task)
```

### Task Control

**`cancel()`**

Cancel a scheduled task.

```python
cancel(task_id=0)
```

**Parameters:**

- task_id (int): Task ID to cancel (0 = current task)

**Returns:**

- bool: `True` if task was cancelled, `False` if not found

**Example:**

```python
task_id = scheduler.repeat(some_function, every=1000)
scheduler.cancel(task_id)
```

**`abort_current_task()`**

Cancel the currently executing task.

```python
abort_current_task()
```

**Returns:**

- bool: `True` if task was cancelled, `False` otherwise

**Example:**

```python
def self_cancelling_task():
print("Running once")
scheduler.abort_current_task()

scheduler.repeat(self_cancelling_task, every=1000)
```

**`set_repeat()`**

Change the repeat interval of a task.

```python
set_repeat(repeat_interval=100, task_id=0)
```

**Parameters:**

- repeat_interval (int): New interval in milliseconds (0 = stop repeating)

- task_id (int, optional): Task ID (0 = current task)

**Returns:**

- bool: `True` on success, `False` on failure

**Example:**

```python
def adaptive_task():
    if some_condition:
        scheduler.set_repeat(5000)
    else:
        scheduler.set_repeat(1000)

scheduler.repeat(adaptive_task, every=1000)
```

**`send()`**

Update the parameters of a scheduled task.

```python
send(pkg=(), task_id=0)
```

**Parameters:**

- `pkg` (tuple): New parameters for the task

- `task_id` (int, optional): Task ID (0 = current task)

**Returns:**

- bool : `True` on success, `False` on failure

**Example:**

```python
def configurable_task(config):
    print(f"Config: {config}")

task_id = scheduler.repeat(configurable_task, ("default",), every=1000)
scheduler.send(("updated",), task_id)
```

### Utility Methods

**`start()`**

Start the scheduler main loop (blocking).

```python
start()
```

**Example:**

```python
scheduler.start()
```

**`stop()`**

Stop the scheduler and clear all tasks.

```python
stop()
```

**Example:**

```python
scheduler.stop()
```

**`status()`**

Get the status of a task.

```python
status(task_id=0)
```

**Parameters:**

- `task_id` (int, optional): Task ID (0 = current task)

**Returns:**

- dict: Task status information, or empty dict if not found

**Example:**

```python
info = scheduler.status(task_id)
print(f"Task {info['id']}: {info['job']} - Next run: {info['next_run']}")
```

**`current_task_id()`**

Get the ID of the currently executing task.

```python
current_task_id()
```

**Returns:**

- `int`: Current task ID, or `None` if not in a task

**Example:**

```python
def my_task():
    tid = scheduler.current_task_id()
    print(f"I am task {tid}")
```

**`task_count()`**

Get the total number of active tasks.

```python
task_count()
```

**Returns:**

- `int`: Number of active tasks

**Example:**

```python
print(f"Active tasks: {scheduler.task_count()}")
```

**`pending_count()`**

Get the number of tasks in the execution queue.

```python
pending_count()
```

**Returns:**

- `int`: Number of pending tasks

**Example:**

```python
print(f"Pending tasks: {scheduler.pending_count()}")
```

**`run()`**

Execute a function via the scheduler (for safe printing/scheduling).

```python
run(p=None, q=())
```

**Parameters:**

- `p` (callable): Function to execute

- `q` (tuple, optional): Arguments

**Example:**

```python
scheduler.run(print, ("Safe print",))
```

**`print()`**

Safe print function that works within tasks.

```python
print(*txt)
```

**Parameters:**

- `*txt`: Values to print

**Example:**

```python
def my_task():
    scheduler.print("This is safe to print from a task")
```

## Ring Buffer

The Ring Buffer provides a fixed-size circular buffer for storing
messages with unique IDs, supporting random access and lazy deletion.
Conceptually, it is a controlled short-term memory of **events that have
left traces** .

### Ring Class

#### Constructor

```python
Ring(size)
```

Creates a new ring buffer.

**Parameters:**

- `size` (int): Buffer size in bytes (must be >= 8)

**Example:**

```python
from ringbuffer import Ring

buffer = Ring(1024)
```

**Raises:**

- `ValueError`: If size is not an integer or is less than 8

### Buffer Operations

**`put()`**

Store a message in the buffer.

```python
put(msg_id, msg_bytes)
```

**Parameters:**

- `msg_id` (int): Message ID (1-65535)

- `msg_bytes` (bytes/bytearray): Message data

**Raises:**

- `ValueError`: If msg_id is out of range or message is too large

- `TypeError`: If msg_bytes is not bytes or bytearray

- `MemoryError`: If buffer is full

**Example:**

```python
buffer.put(1, b"Hello, World!")
buffer.put(2, bytearray([0x01, 0x02, 0x03]))
```

### Message Retrieval

**`get()`**

Retrieve and remove the next message from the buffer (FIFO).

```python
get()
```

**Returns:**

- `tuple`: (msg_id, msg_bytes) or (0, b'') if empty

**Example:**

```python
msg_id, msg = buffer.get()
if msg_id != 0:
   print(f"Message {msg_id}: {msg}")
```

**`peek()`**

View the next message without removing it.

```python
peek()
```

**Returns:**

- `tuple`: (msg_id, msg_bytes) or `None` if empty

**Example:**

```python
result = buffer.peek()
if result:
   msg_id, msg = result
   print(f"Next message: {msg_id}")
```

**`pull()`**

Retrieve and remove a specific message by ID (random access).

```python
pull(wanted_id)
```

**Parameters:**

- `wanted_id` (int): Message ID to retrieve

**Returns:**

- `tuple` : (msg_id, msg_bytes) or (0, b'') if not found

**Example:**

```python
msg_id, msg = buffer.pull(5)
if msg_id != 0:
   print(f"Found message {msg_id}: {msg}")
```

### Buffer Utility Methods

**`list()`**

Get a list of all message IDs in the buffer.

```python
list()
```

**Returns:**

- `list`: List of message IDs (excluding deleted messages)

**Example:**

```python
ids = buffer.list()
print(f"Messages in buffer: {ids}")
```

**`is_empty()`**

Check if the buffer is empty.

```python
is_empty()
```

**Returns:**

- `bool`: `True` if empty, `False` otherwise

**Example:**

```python
if buffer.is_empty():
   print("Buffer is empty")
```

**`is_full()`**

Check if the buffer is full.

```python
is_full()
```

**Returns:**

- `bool`: `True` if full, `False` otherwise

**Example:**

```python
if buffer.is_full():
   print("Buffer is full")
```

**`clear()`**

Clear all messages from the buffer.

```python
clear()
```

**Example:**

buffer.clear()

**`len()`**

Get the number of bytes currently in the buffer.

```python
len(buffer)
```

**Returns:**

- `int`: Number of bytes used

**Example:**

```python
print(f"Buffer usage: {len(buffer)}/{buffer.size} bytes")
```

## Advanced Usage

Advanced usage is where the temporal and causal structure of your system
starts to become visible: you chain events, establish flows, and use the
ring buffer as the trail that events leave behind.

### Nested Task Scheduling

```python
def child_task():
    scheduler.print("Child task")

def parent_task():
    scheduler.print("Parent task")
    # Temporal relationship: child happens *after* parent has run
    scheduler.do(child_task)

scheduler.do(parent_task)
```

### Event Chains

Here, one event causes another, forming a causal chain:

```python
def task1():
    scheduler.print("Task 1")
    scheduler.trigger_event("event2")

def task2():
    scheduler.print("Task 2")
    scheduler.trigger_event("event3")

def task3():
    scheduler.print("Task 3")

scheduler.on(task1, when="event1")
scheduler.on(task2, when="event2")
scheduler.on(task3, when="event3")

scheduler.trigger_event("event1")
scheduler.start()
```

event1 → event2 → event3 expresses *because this happened, that should follow*.

### Ring Buffer as Message Queue

The ring buffer can act as the record of what just happened, waiting to
be processed:

```python
buffer = Ring(2048)

def producer(i):
    if i <= 10:
        buffer.put(i+1, f"Message {i}".encode())
        scheduler.trigger_event("data_ready")
        scheduler.send(i+1)
    else:
       buffer.put(i+1, b"Done")
       scheduler.trigger_event("data_ready") 
       scheduler.abort_current_task() # stop 
    
def consumer():
    msg_id, msg = buffer.get()
    msg = msg.decode()
    scheduler.print(f"Consumed: {msg}")
    if msg == "Done":
       scheduler.abort_current_task()

scheduler.repeat(producer, (0,), every=10)
scheduler.on(consumer, when="data_ready", repeat=True)
scheduler.start()
```

### Priority Message Processing**

```python
buffer = Ring(1024)

buffer.put(1, b"Low priority")
buffer.put(100, b"High priority")
buffer.put(2, b"Low priority")

msg_id, msg = buffer.pull(100)
print(f"Processing high priority: {msg}")

while not buffer.is_empty():
    msg_id, msg = buffer.get()
    print(f"Processing: {msg}")
```

## Best Practices

Think in terms of **flows of events** rather than lines of code. The
following best practices reflect that mindset.

### Event Scheduler

1.  **Keep tasks short**
    Tasks should complete quickly to avoid blocking other tasks. Let long-running behavior emerge from many small events over time.

2.  **Use events for coordination**
    Prefer event-driven patterns (`on`, `trigger_event`, `await_event`) over polling. Polling ignores that "nothing happening" is also a kind of information.

3.  **Handle exceptions**
    Always wrap risky code in `try-except` blocks. A single failing event should not collapse the entire unfolding.

4.  **Cancel unused tasks**
    Free resources by cancelling tasks you no longer need. Not every event stream is meant to run forever.

5.  **Monitor task count**
    Use `task_count()` to detect task leaks. If the system is permanent but your tasks are not, they must eventually end or be cancelled.

6.  **Use appropriate delays**
    Balance responsiveness with power consumption. Frequent temporal events cost CPU and energy.

### Ring Buffer

1.  **Size appropriately**
    Buffer size should accommodate peak message load without pretending you have infinite memory.

2.  **Check before put**
    Use `is_full()` to avoid MemoryError. If the world is generating events faster than you can handle, decide which ones you can safely drop.

3.  **Validate message IDs**
    Use IDs consistently (e.g., message types or priorities) so you can reason about the stream of events.

4. **Clean up regularly**
    Use `pull()` or `get()` to reclaim space. Messages belong to the past;
    only keep them as long as they serve the present.

5. **Handle empty buffer**
    Always check return values for (0, b''). No message is also a meaningful state.

5. **Use `peek()` wisely**
    Peek before `get()` to implement conditional processing without
    consuming data prematurely.

## Troubleshooting

### Event Scheduler Issues

**Problem:** Tasks not executing

- Check that `start()` has been called

- Verify task was scheduled successfully (check return value)

- Ensure task function is callable

**Problem:** Memory errors

- Reduce `max_tasks` parameter

- Cancel unused tasks

- Check for task leaks (tasks that never complete)

**Problem:** Tasks executing at wrong time

- Verify delay/repeat values are in milliseconds

- Check for timer overflow (`ticks_ms()` wraps at ~49 days)

**Problem:** Events not triggering

- Ensure event flag names match exactly

- Check that tasks are registered with `on()` before triggering

- Verify `trigger_event()` is called with correct flag

### Ring Buffer Issues

**Problem:**MemoryError when putting messages

- Check buffer size is sufficient

- Use `is_full()` before `put()`

- Consider increasing buffer size or consuming messages faster

**Problem:** Messages not found with `pull()`

- Verify message ID is correct

- Check if message was already consumed

- Use `list()` to see available message IDs

**Problem:** Unexpected `(0, b'')` returns

- Buffer may be empty -- check with `is_empty()`

- Message may have been deleted

- Incomplete message in buffer (corrupted data)

**Problem:** Buffer appears full but `is_empty()` returns True

- Deleted messages may be taking space

- Call `get()` repeatedly to clean up deleted messages

- Consider using `clear()` to reset buffer

## Performance Tips

### Event Scheduler

- Use `repeat()` instead of rescheduling inside the task

- Minimize work in frequently-called tasks

- Use events instead of polling

- Batch operations when possible

- Profile with `task_count()` and `pending_count()`

### Ring Buffer

- Pre-allocate buffer size based on expected load

- Use `pull()` sparingly (O(n) operation)

- Prefer `get()` for sequential access (O(1))

- Keep message sizes reasonable

- Use message IDs as type indicators

## Memory Usage

### Event Scheduler

- Base overhead: ~100 bytes

- Per task: ~80--120 bytes (depending on parameters)

- Heap overhead: ~20 bytes per task in queue

### Ring Buffer

- Base overhead: ~40 bytes

- Buffer: Exactly size bytes

- Per message: 4 bytes header + message length

## Thread Safety

**Warning:** Neither the Event Scheduler nor Ring Buffer are
thread-safe. Do not access from multiple threads or interrupt handlers
without proper synchronization.

For interrupt-driven events, use MicroPython's schedule() function:

```python
from micropython import schedule

def button_isr(pin):
    schedule(lambda _: scheduler.trigger_event("button"), None)
```

## Version History

- **v1.0** - Initial release with basic scheduling and ring buffer

- **v1.1** - Added __slots__, improved memory efficiency

- **v1.2** - Added validation, error handling, utility methods

- **v1.3** - Bug fix, insert `len(self._tasks) == 0` to break out of `start` loop

- **v1.4** - Removed __slots__, has no effect in MicroPython

