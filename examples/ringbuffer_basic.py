from ringbuffer import Ring

buffer = Ring(1024)

print("Ring Buffer Basic Example")
print("=" * 40)

print("\n1. Putting messages into buffer...")
buffer.put(1, b"First message")
buffer.put(2, b"Second message")
buffer.put(3, b"Third message")
print(f"   Buffer contains {len(buffer)} bytes")

print("\n2. Listing all message IDs...")
ids = buffer.list()
print(f"   Message IDs: {ids}")

print("\n3. Peeking at next message...")
result = buffer.peek()
if result:
    msg_id, msg = result
    print(f"   Next message: ID={msg_id}, Data={msg}")

print("\n4. Getting messages (FIFO)...")
msg_id, msg = buffer.get()
print(f"   Got: ID={msg_id}, Data={msg}")

msg_id, msg = buffer.get()
print(f"   Got: ID={msg_id}, Data={msg}")

print("\n5. Remaining messages...")
ids = buffer.list()
print(f"   Message IDs: {ids}")

print("\n6. Adding more messages...")
buffer.put(4, b"Fourth message")
buffer.put(5, b"Fifth message")
ids = buffer.list()
print(f"   Message IDs: {ids}")

print("\n7. Pulling specific message (ID=4)...")
msg_id, msg = buffer.pull(4)
print(f"   Pulled: ID={msg_id}, Data={msg}")

print("\n8. Final state...")
ids = buffer.list()
print(f"   Message IDs: {ids}")
print(f"   Buffer contains {len(buffer)} bytes")
print(f"   Is empty: {buffer.is_empty()}")

print("\n9. Clearing buffer...")
buffer.clear()
print(f"   Is empty: {buffer.is_empty()}")

print("\n" + "=" * 40)
print("Example complete!")
