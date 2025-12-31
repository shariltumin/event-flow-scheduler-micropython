from events import Work
from ringbuffer import Ring

scheduler = Work()
message_queue = Ring(2048)

producer_count = 0
consumer_count = 0

def producer():
    global producer_count
    producer_count += 1
    
    message = f"Message #{producer_count}".encode()
    
    if not message_queue.is_full():
        message_queue.put(producer_count, message)
        scheduler.print(f"[Producer] Sent: {message.decode()}")
        
        if producer_count >= 10:
            scheduler.trigger_event("production_complete")
    else:
        scheduler.print("[Producer] Buffer full, waiting...")

def consumer():
    global consumer_count
    
    if not message_queue.is_empty():
        msg_id, msg = message_queue.get()
        consumer_count += 1
        scheduler.print(f"[Consumer] Received: {msg.decode()}")
        
        if consumer_count >= 10:
            scheduler.trigger_event("consumption_complete")
    else:
        scheduler.print("[Consumer] Buffer empty, waiting...")

def on_complete():
    scheduler.print("\n✓ All messages processed!")
    scheduler.print(f"  Produced: {producer_count}")
    scheduler.print(f"  Consumed: {consumer_count}")
    scheduler.stop()

scheduler.repeat(producer, every=500)

scheduler.repeat(consumer, every=800)

scheduler.on(on_complete, when="consumption_complete")

print("Producer-Consumer Example")
print("=" * 40)
print("Producer: sends every 500ms")
print("Consumer: receives every 800ms")
print("=" * 40)

try:
    scheduler.start()
except KeyboardInterrupt:
    print("\nStopped by user")
    scheduler.stop()

print("\nFinal Statistics:")
print(f"  Messages produced: {producer_count}")
print(f"  Messages consumed: {consumer_count}")
print(f"  Messages in buffer: {len(message_queue.list())}")
