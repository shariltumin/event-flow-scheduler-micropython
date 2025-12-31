from events import Work

scheduler = Work()

led_state = False

def toggle_led():
    global led_state
    led_state = not led_state
    state_str = "ON" if led_state else "OFF"
    scheduler.print(f"LED: {state_str}")

def read_temperature():
    import random
    temp = 20 + random.randint(0, 10)
    scheduler.print(f"Temperature: {temp}°C")
    
    if temp > 25:
        scheduler.trigger_event("high_temp", (temp,))

def temperature_alert(temp):
    scheduler.print(f"⚠️  High temperature alert: {temp}°C")

def read_button():
    import random
    if random.random() > 0.7:
        scheduler.print("Button pressed!")
        scheduler.trigger_event("button_press")

def on_button_press():
    scheduler.print("Handling button press event")

def heartbeat():
    scheduler.print("❤️  System alive")

def system_status():
    task_count = scheduler.task_count()
    pending = scheduler.pending_count()
    scheduler.print(f"📊 Status: {task_count} tasks, {pending} pending")

scheduler.repeat(toggle_led, every=1000)

scheduler.repeat(read_temperature, every=3000)

scheduler.repeat(read_button, every=2000)

scheduler.repeat(heartbeat, every=5000)

scheduler.repeat(system_status, every=10000)

scheduler.on(temperature_alert, when="high_temp")

scheduler.on(on_button_press, when="button_press", repeat=True)

print("IoT Device Simulator")
print("=" * 40)
print("Simulating:")
print("  - LED blinking (1s)")
print("  - Temperature sensor (3s)")
print("  - Button polling (2s)")
print("  - Heartbeat (5s)")
print("  - Status report (10s)")
print("=" * 40)
print("Press Ctrl+C to stop\n")

try:
    scheduler.start()
except KeyboardInterrupt:
    print("\n\nShutting down...")
    scheduler.stop()
    print("Device stopped")
