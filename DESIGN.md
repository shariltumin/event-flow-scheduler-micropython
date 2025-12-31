>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# Design Guide

## Designing Your System as Events in Time
Embedded systems live in a world where nothing holds still. Voltages change, sensors update, packets appear and vanish, buttons are pressed and released. Your code does not run in a vacuum; it runs in this flow.

This library is built around that simple observation:
 
> Your system is not a static set of functions. It is a network of
**events** unfolding in time.

This guide shows how to think about your system in terms of:

- **Temporal events** -- things that happen *when the time
comes*.

- **Causal events** -- things that happen *because something else
happened*.

- **Messages** -- short-lived traces of events that pass through the
system.

We will build up an example system and map each part to `events.py`
and `ringbuffer.py`, and later compare this approach to
`async/await` and `_thread` in MicroPython.

---

## 1. Vocabulary: Temporal vs Causal Events

Before touching code, it helps to name the forces at work.

### Temporal Events

Temporal events care about *when*:

- "Read the sensor every second."

- "If we don't hear from the server for 30 seconds, raise an alarm."

- "Retry this request 3 times with a delay."

In the scheduler, these are primarily expressed with:

- `do(job, ...)` -- "do this soon."

- `at(job, at=delay, ...)` -- "do this after `delay` ms."

- `repeat(job, every=interval, ...)` -- "do this every `interval`
ms."

### Causal Events

Causal events care about *because*:

- "Because the button was pressed, toggle the LED."

- "Because new data arrived, parse and store it."

- "Because the temperature went above a threshold, sound an alarm."

In the scheduler, these are expressed with:

- `on(job, when="flag", ...)` -- "when `flag` happens, run
`job`."

- `trigger_event("flag", pkg=...)` -- "`flag` has happened;
notify everyone listening."

- `await_event("flag")` -- "pause this task until `flag`
happens."

### Messages

Events often leave behind **messages**:

- Sensor samples

- Log lines

- Commands

- State snapshots

These messages are brief and impermanent. They matter while the system
responds, then they can be discarded. The ring buffer gives you a
disciplined way to handle them:

- `put(id, bytes)` -- "this event created a message."

- `get()` / `peek()` -- "what's next in the stream?"

- `pull(id)` -- "fetch this specific message."

- `list()` -- "what's currently in memory?"

---

## 2. A Small Story: Sensor + Button + Logger

Imagine a simple IoT node:

- A **sensor** reports a temperature.

- A **button** can mark a "checkpoint" in time.

- A **logger** stores readings in a ring buffer.

- An **alarm** is raised if temperature is too high or if readings
stop.

Instead of writing "main loop" + `sleep` + "if this then that" code,
we design the system as events:

1. **Temporal**: `read_sensor` runs every second.

2. **Causal**: when new sensor data arrives, an event
`sensor_event` is triggered.

3. **Causal**: when `sensor_event` happens:
- store the reading in the ring buffer,
- check thresholds,
- maybe trigger `alarm_event`.

4. **Causal**: when `button_event` happens:
- mark the current time or reading as a checkpoint.

5. **Temporal**: a watchdog checks periodically whether readings
have stopped.

---

## 3. Mapping the Story to Code

### 3.1. Setting Up the Scheduler and Ring

```python
from events import Work
from ringbuffer import Ring

scheduler = Work()
log_buffer = Ring(2048)
```

We now have:

- A **timeline** (scheduler) on which events will unfold.

- A **short-term memory** (log_buffer) where messages can be stored.

### 3.2. Temporal Event: Periodic Sensor Read

We want:

> "Every 1000 ms, read the sensor."

```python
def read_sensor():
    value = read_temp_sensor() # your hardware-specific function
    # Create a sensor event and pass the value along
    scheduler.trigger_event("sensor_event", (value,))

# Temporal event: runs over and over in time
scheduler.repeat(read_sensor, every=1000)
```

Here:

- repeat encodes the **temporal** part.

- trigger_event("sensor_event", (value,)) bridges into **causal**
  logic:
  "Because we just read the sensor, these other things should happen."

### 3.3. Causal Event: Logging Sensor Data

We want:

> "Whenever a sensor reading arrives, log it."

```python
def log_sensor_reading(value):
    # In a real system, msg_id might be a counter, timestamp bucket, or type.
    # Here we just use a simple incrementing ID.
    log_sensor_reading.counter += 1
    msg_id = log_sensor_reading.counter

    payload = f"{value}".encode()
    try:
        log_buffer.put(msg_id, payload)
    except MemoryError:
        # If the buffer is full, you decide which impermanence you accept:
        # drop oldest, clear, or drop new reading. Here we drop the oldest.
        _drop_oldest_message()
        log_buffer.put(msg_id, payload)

log_sensor_reading.counter = 0

def _drop_oldest_message():
    log_buffer.get() # Discard the earliest message
```

Now wire this to the causal event:

```python
scheduler.on(log_sensor_reading, when="sensor_event")
```

Whenever sensor_event is triggered, log_sensor_reading(value) runs with
the current value.

### 3.4. Causal Event: Alarm on High Temperature

We want:

> "Because the temperature went above 80°C, trigger an alarm."

```python
THRESHOLD = 80

def check_threshold(value):
    if value > THRESHOLD:
        scheduler.trigger_event("alarm_event", (value,))

# Attach another causal reaction to the same sensor_event
scheduler.on(check_threshold, when="sensor_event")
```

Now define what the alarm actually does:

```python
def alarm_handler(value):
    scheduler.print("!!! TEMPERATURE ALARM !!!")
    scheduler.print("Value:", value)
    # Here you could toggle GPIOs, send network packets, etc.

scheduler.on(alarm_handler, when="alarm_event")
```

Notice:

- sensor_event is one cause.

- alarm_event is another, derived cause.

- The system is a *chain of reasons*, not a flat "if" block.

### 3.5. Causal Event: Button Checkpoints

We want:

> "Because the user pressed the button, mark a checkpoint in the logs."

First, imagine your hardware interrupt calls a small function when the
button changes. Using MicroPython's `schedule()` (see USER-MANUAL.md for
details):

```python
from micropython import schedule

def button_isr(pin):
    schedule(lambda _: scheduler.trigger_event("button_event"), None)
```

Now define what happens when button_event occurs:

```python
def mark_checkpoint():
    # For example, add a special message to the ring buffer
    mark_checkpoint.counter += 1
    msg_id = 10000 + mark_checkpoint.counter # reserved ID range for checkpoints
    try:
        log_buffer.put(msg_id, b"CHECKPOINT")
    except MemoryError:
        _drop_oldest_message()
        log_buffer.put(msg_id, b"CHECKPOINT")

mark_checkpoint.counter = 0

scheduler.on(mark_checkpoint, when="button_event")
```

When the user presses the button, an **external cause** (button_event)
enters the system and leaves a trace in the buffer.

## 4. Processing the Stream of Events

At some point, you may want to process the log:

- Flush it to persistent storage.

- Send it upstream over a network.

- Print summaries or perform analysis.

You can do this **periodically** (temporal) or **on demand** (causal).

### 4.1. Temporal Log Flush

> "Every 10 seconds, send whatever is in the buffer."

```python
def flush_logs():
    while not log_buffer.is_empty():
        msg_id, msg = log_buffer.get()
        _send_log(msg_id, msg) # your transport layer

def _send_log(msg_id, msg):
    # Replace with your implementation: UART, Wi-Fi, BLE, etc.
    scheduler.print(f"LOG {msg_id}: {msg}")

scheduler.repeat(flush_logs, every=10_000)
```

### 4.2. Causal Log Flush

> "Because the user pressed the button, flush all logs now."

```python
def flush_on_button():
    flush_logs()

scheduler.on(flush_on_button, when="button_event")
```

Again, temporal and causal logic are orthogonal, but they interact neatly.

## 5. Thinking in Events, Not Loops

A traditional "super loop" might look like this:

```python
while True:
    if time_to_read_sensor():
        read_sensor()
    if button_pressed():
        mark_checkpoint()
    if time_to_flush_logs():
        flush_logs()
    # ...
```

This approach:

- Mixes **time** logic (`time_to_*`) with **behavior** logic in one
  place.

- Makes it hard to add new behaviors without complicating the main loop.

- Encourages ad-hoc flags and state variables.

The event-driven design above instead says:

- "Here is **what** should happen when the time comes." ➜ `repeat`, `at`, `do`

- "Here is **what** should happen when this cause occurs." ➜ `on`, `trigger_event`

- "Here is **how** I want to remember recent events." ➜ `Ring`

The scheduler and ring buffer then maintain the structure, so your main program can be as simple as:

```python
# Set everything up...
scheduler.start()
```

## 6. Design Patterns with Temporal & Causal Events

Here are a few patterns that often show up in real systems.

### 6.1. Watchdog Pattern (Temporal Safety Net)

> "If nothing has happened for a while, treat that as an event."

```python
LAST_SENSOR_MS = 0

def remember_sensor_time(value):
    global LAST_SENSOR_MS
    LAST_SENSOR_MS = ticks_ms() # from time module

scheduler.on(remember_sensor_time, when="sensor_event")

def watchdog():
    now = ticks_ms()
    if now - LAST_SENSOR_MS > 30_000:
        scheduler.trigger_event("sensor_stalled")

scheduler.repeat(watchdog, every=5_000)

def handle_stall():
    scheduler.print("Sensor stalled; taking recovery action") # e.g. reset hardware, notify user, etc.

scheduler.on(handle_stall, when="sensor_stalled")
```

Here, "nothing happening" (no sensor events) becomes its own **causal event** .

### 6.2. Debounced Button (Temporal Guard on a Causal Event)

> "Because the button was pressed, but only if it stays that way for 50 ms."

```python
def raw_button_event(state):
    if state: # pressed
        # Wait 50 ms and then check again
        scheduler.at(_confirm_button_press, at=50)

def _confirm_button_press():
    if read_button_state(): # hardware-specific
        scheduler.trigger_event("button_event")

# raw_button_event would be triggered from ISR / hardware layer
```

Temporal delay (`at`) is used to "stabilize" a causal signal.

### 6.3. Rate-Limited Actions (Temporal Throttle on Causal Events)

> "Because many packets may arrive, but only send one summary per second."

```python
LATEST_VALUE = None

def on_fast_event(value):
    global LATEST_VALUE
    LATEST_VALUE = value

scheduler.on(on_fast_event, when="fast_sensor_event")

def summary_tick():
    global LATEST_VALUE
    if LATEST_VALUE is not None:
        _send_summary(LATEST_VALUE)
        LATEST_VALUE = None

def _send_summary(value):
    scheduler.print("Summary:", value)

scheduler.repeat(summary_tick, every=1000)
```

Fast causal events accumulate into a single temporal summary.

## 7. Comparison with `async/await` and `_thread`

You can think of this library as a deliberately small, explicit
alternative to other concurrency tools MicroPython offers. It doesn't
replace them in all cases, but it makes **time and events** the main
characters instead of abstractions hidden behind a scheduler or an RTOS.

### 7.1. Compared to `async/await` (asyncio)**

MicroPython's `asyncio` uses coroutines and an event loop:

- You write `async def` functions (coroutines).

- You use `await` to `yield` control (e.g., `await asyncio.sleep(1)`).

- The event loop schedules coroutine execution.

**Similarities:**

- Both approaches are **cooperative** : tasks must yield (or complete)
  so others can run.

- Both handle **temporal** behavior (delays, intervals) and **causal**
  behavior (callbacks, awaited events).

- Both can help you avoid blocking `while True` loops and tangled sleeps.

**Differences in emphasis:**

- `async/await` is *syntax-level*:
    - The structure of your code is shaped by and .asyncawait
    - Concurrency is expressed as coroutines that suspend and resume.

- This scheduler is *event-level*:
    - The structure of your code is shaped by **events** (`on`, `trigger_event`, `repeat`, `at`).
    - Concurrency is expressed as flows of temporal and causal events, plus messages in a ring buffer.

**When this library is a good fit compared to `asyncio`:**

- You want a **minimal mental model** :
    - No coroutines, no `await`, no special function types.
    - Just plain functions scheduled in time or bound to events.

- You want explicit **event graphs** :
    - It's more natural to visualize *"event A triggers B and C, which may trigger D"* than to reason about multiple coroutines.

- You want tight control over memory:
   - ~~The scheduler uses `__slots__` and is tuned for small MCUs.~~

- You like the philosophy that **everything is an event** , and messages
  are explicit, not hidden in coroutine state.

**When uasyncio might be better:**

- You are already invested in asyncio-style code (e.g. porting from CPython).

- You rely heavily on existing async libraries.

- You are comfortable with coroutines and want direct `await` syntax for readability.

### 7.2. Compared to `_thread` (Preemptive Threads)

MicroPython's `_thread` module gives you real threads (where supported):

- Code runs on multiple threads that can, in principle, run concurrently.

- The scheduler of the underlying RTOS/firmware decides which thread runs when.

- Shared state must be protected with locks or other synchronization primitives.

**Similarities:**

- Both let multiple "things" appear to be happening at once.

- Both can be used to separate concerns (e.g. "network thread" vs "application logic").

**Crucial differences:**

- `_thread` is **preemptive** :
    - A thread can be interrupted at almost any point.
    - You must guard shared data with locks, critical sections, or other mechanisms.
    - Bugs can be subtle: race conditions, deadlocks, priority inversions.

- This scheduler is **cooperative** :
    - Tasks run until they return; they are not preempted in the middle.
    - Shared data can often be managed without locks, as long as tasks are short and disciplined.
    - Causality is explicit: events trigger other events; you don't have hidden parallelism.

**When this library is a better fit than `_thread`:**

- You're running on a **small MCU** where preemptive threads are heavy or unreliable.

- You want to avoid **concurrency bugs** :
    - No locks, no race conditions from mid-function preemption.

- Your system is fundamentally **event-driven** :
    - Buttons, sensors, timers, messages---all nicely modeled as events in a single timeline.

- You can accept that **long-running tasks must be broken down** into smaller actions over time.

**When `_thread` might be necessary:**

- You truly need **blocking operations** that can't easily be expressed as events or broken into small steps.

- You rely on a **separate core** (e.g. on rp2 Pico) doing something intensive while the main core runs application logic.

- You are integrating with a library that assumes a threaded model.

### 7.3. Philosophical Summary

- `async/await` says:
> "Your program is many little **stories** (coroutines) that occasionally pause and let others speak."

- `_thread` says:
> "Your program is many **people talking at once** , and you must keep them from stepping on each other."

- This library says:
> "Your program is a **world in motion** , where events happen in time, cause other events, and leave behind messages that soon fade."

If the last sentence matches how you like to think about embedded systems, then modeling your design with **temporal events** , **causal events** , and **ring-buffered messages** will feel natural and coherent---and the APIs in `events.py` and `ringbuffer.py` will be a direct reflection of that worldview.

## 8. Embracing Impermanence

The design of this library is deliberately modest:

- Tasks are small and cooperative.

- Buffers are finite.

- Messages are disposable.

- Events come and go.

Rather than fighting these constraints, you **embrace** them:

- You decide which events matter and for how long.

- You represent time and causality explicitly.

- You let the system evolve as a network of relationships, not a rigid script.

If you keep asking:

> "Is this a temporal event, a causal event, or a message that one of them produced?"

your design will naturally align with the scheduler and ring buffer, and the resulting code will be easier to reason about, extend, and debug.

