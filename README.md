
# MicroPython Event Scheduler & Ring Buffer

**Impermanence is the creator of time**. It is behind all changes---the
power that keeps everything in a state of perpetual becoming. It drives
all processes and makes life possible.

Embedded systems live in this same flow. Voltages rise and fall, sensors
drift, packets are sent and lost, buttons are pressed and released.
Nothing is ever truly static; everything is always *on its way* to
something else.

In software, a *waitable* or *actionable* happening is an
**event**. This library takes that seriously. It is built around the
idea that your program is not a list of instructions---it is a
choreography of events unfolding in time.

We are interested in two fundamental kinds of events:

1. **Temporal events** -- things that happen *when the time
comes*: after a delay, at a moment, or with a rhythm (intervals,
schedules, timeouts).

2. **Causal events** -- things that happen *because something else
happened*: chains of cause and effect that ripple through your system.

This project provides a lightweight, efficient event-driven task
scheduler and ring buffer implementation for MicroPython, designed for
resource-constrained embedded systems. Its purpose is to give shape and
structure to impermanence---to let you express both temporal and causal
events clearly in code, instead of fighting against the constant change
your system lives in.


## Features

### Event Scheduler (`events.py`)

Life on a microcontroller is often a tangle of `sleep` calls, flags,
and callbacks. The event scheduler cuts through this by making time and
causality first-class concepts.

- **Cooperative multitasking** - Express concurrent flows of
behavior without preemption

- **Temporal scheduling** - Schedule tasks with delays and repeating
intervals (temporal events)

- **Event-driven architecture** - Tasks can wait for and trigger
custom events (causal events)

- **Heap-based priority queue** - Efficient ordering of what must
happen next using `heapq`

- ~~**Memory efficient** - Uses `__slots__` to minimize memory footprint~~

- **Lazy cleanup** - Automatic garbage collection of cancelled
tasks

- **Error handling** - Robust exception handling with fallback
mechanisms

- **Task management** - Cancel, modify, and query task status

The scheduler lets you say:

- *"Run this when enough time has passed."*

- *"Run that when this other thing has happened."*

Instead of micromanaging loops and delays, you describe how your system
should respond as time passes and events occur.

#

### Ring Buffer (`ringbuffer.py`)

In a world of impermanence, information appears, is needed briefly, and
then can be forgotten. The ring buffer gives you a disciplined way to
handle that flow.

- **Fixed-size circular buffer** - Efficient memory usage with
wraparound

- **Message-based protocol** - Store messages with unique IDs
(1-65535)

- **Random access** - Pull specific messages by ID without consuming
others

- **Lazy deletion** - Mark messages as deleted without immediate
cleanup

- **Peek support** - Inspect next message without consuming it

- **Memory safe** - Bounds checking and validation on all
operations

Events produce messages: sensor readings, commands, logs, state
transitions. The ring buffer is where those traces of change can be kept
just long enough---accessible while they matter, gone when they don't.

#

## Installation

Copy `events.py` and `ringbuffer.py` to your MicroPython device:

```bash
ampy --port /dev/ttyUSB0 put events.py
ampy --port /dev/ttyUSB0 put ringbuffer.py
```

Or use mpremote:

```bash
mpremote cp events.py :
mpremote cp ringbuffer.py :
```

## Quick Start

### Event Scheduler

A "Hello, World!" is a tiny event in time.

```python
from events import Work

scheduler = Work()

def hello():
    print("Hello, World!")

# Schedule a simple temporal event: run `hello` soon
scheduler.do(hello)

scheduler.start()
```

Under the hood, `hello` is placed into a timeline of things that will
happen. As time advances, events are pulled from that timeline and
allowed to unfold.

### Ring Buffer

Messages are the footprints of events. The ring buffer keeps a short
memory of them.

```python
from ringbuffer import Ring

buffer = Ring(1024)

buffer.put(1, b"Hello")
buffer.put(2, b"World")

msg_id, msg = buffer.get()
print(f"Message {msg_id}: {msg}")

```

As events fire and messages appear, you can store, inspect, and consume
them without losing track of order.

## Basic Usage

### Scheduling Tasks (Temporal Events)

Temporal events are those that depend on *when* something happens:
timeouts, periodic tasks, retries, maintenance passes. They are your way
of saying:

> "If enough time passes, this should occur."

```python
from events import Work

work = Work()

def task():
    print("Task executed")

# Run as soon as possible
work.do(task)

# Run at or after t = 1000 (scheduler time base)
work.at(task, at=1000)

# Run repeatedly every 5000 units
work.repeat(task, every=5000)

work.start()

```

Instead of sprinkling `time.sleep()` or manual counters throughout your
code, you place your intentions into the scheduler: *here is what I want
to happen and when*.

### Event-Driven Tasks (Causal Events)

Causal events express relationships of the form:

> "When this happens, make that happen."

They turn the invisible chain of cause and effect in your system into
explicit structure: button → action, packet received → parse, threshold
crossed → alarm.

```python
from events import Work

work = Work()

def on_button_press():
    print("Button pressed!")

# Register a handler for the causal event "button_event"
work.on(on_button_press, when="button_event")

# Somewhere else, when the cause actually occurs:
work.trigger_event("button_event")

work.start()
```

By separating **temporal** scheduling (`do`, `at`, `repeat`) from **causal**
signalling (`on`, `trigger_event`), your design begins to mirror reality:

- Time flows forward and occasionally triggers things.

- Events happen and cause other events in response.

Your code becomes less about "what line runs next" and more about "what
should happen in this world when circumstances change".

## Ring Buffer Operations

Every temporal and causal event can generate information: logs, sensor
values, commands, acknowledgments. Most of it only matters briefly, but
for that brief time you want clean, reliable access.

```python
from ringbuffer import Ring

ring = Ring(512)

ring.put(1, b"First message")
ring.put(2, b"Second message")

msg_id, msg = ring.peek()
print(f"Next: {msg}")

msg_id, msg = ring.get()
print(f"Got: {msg}")

msg_id, msg = ring.pull(2)
print(f"Pulled: {msg}")

ids = ring.list()
print(f"Remaining IDs: {ids}")
```

The ring buffer lets your system remember just enough of its recent past
to respond intelligently, without pretending that anything is permanent.

## Requirements

- MicroPython v1.19 or later

- Minimum 32KB RAM recommended

- heapq module (included in MicroPython)

## Performance

Impermanence does not mean chaos. It can be managed with discipline and
efficiency, even on very small devices.

- **Event Scheduler** : Handles 100+ concurrent tasks on ESP32

- **Ring Buffer** : O(1) put/get operations, O(n) for pull/peek

- **Memory** : ~200 bytes per task, configurable buffer size

The architecture is built so that many little changes---many small
events---can be handled smoothly without overwhelming CPU or RAM.

## License

MIT License - See LICENSE file for details.

## Documentation

For detailed API documentation and advanced usage, see USER-MANUAL.md.

There you will find a more concrete description of how to:

- Model your system as flows of temporal and causal events.

- Use the scheduler to orchestrate them.

- Use the ring buffer to move information between them.

## Examples

See the examples/ directory for complete working examples:

- Basic task scheduling (temporal events)

- Event-driven patterns (causal events)

- Ring buffer message passing

- Real-world IoT applications that live in constant change

## File Structure

```
.
├── DESIGN.md
├── events.py
├── examples
│   ├── basic_scheduling.py
│   ├── event_driven.py
│   ├── iot_device.py
│   ├── priority_messages.py
│   ├── producer_consumer.py
│   ├── ringbuffer_basic.py
│   └── task_chain.py
├── MPY
│   ├── events.mpy
│   └── ringbuffer.mpy
├── PROGRAMMING_TIPS.md
├── README.md
├── ringbuffer.py
├── tests
│   ├── test_events.py
│   └── test_ringbuffer.py
└── USER-MANUAL.md

```
