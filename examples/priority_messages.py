from ringbuffer import Ring

MSG_TYPE_SENSOR = 1
MSG_TYPE_COMMAND = 2
MSG_TYPE_STATUS = 3
MSG_TYPE_ERROR = 4

buffer = Ring(1024)

print("Message Queue with Priority Example")
print("=" * 40)

print("\n1. Adding messages with different priorities...")
buffer.put(MSG_TYPE_SENSOR, b"Temperature: 25C")
buffer.put(MSG_TYPE_STATUS, b"System OK")
buffer.put(MSG_TYPE_SENSOR, b"Humidity: 60%")
buffer.put(MSG_TYPE_ERROR, b"Sensor disconnected")
buffer.put(MSG_TYPE_COMMAND, b"RESTART")
buffer.put(MSG_TYPE_SENSOR, b"Pressure: 1013hPa")

print(f"   Added 6 messages")
print(f"   Message IDs in buffer: {buffer.list()}")

print("\n2. Processing high-priority messages first...")

msg_id, msg = buffer.pull(MSG_TYPE_ERROR)
if msg_id != 0:
    print(f"   [ERROR] {msg.decode()}")

msg_id, msg = buffer.pull(MSG_TYPE_COMMAND)
if msg_id != 0:
    print(f"   [COMMAND] {msg.decode()}")

print(f"\n3. Remaining messages: {buffer.list()}")

print("\n4. Processing remaining messages in order...")
while not buffer.is_empty():
    msg_id, msg = buffer.get()
    if msg_id == MSG_TYPE_SENSOR:
        print(f"   [SENSOR] {msg.decode()}")
    elif msg_id == MSG_TYPE_STATUS:
        print(f"   [STATUS] {msg.decode()}")

print("\n5. Buffer is now empty")
print(f"   Is empty: {buffer.is_empty()}")

print("\n" + "=" * 40)
print("Priority processing complete!")
