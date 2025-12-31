from events import Work

scheduler = Work()

def sensor_reading(value):
    print(f"Sensor reading received: {value}")
    if value > 100:
        scheduler.trigger_event("high_value_alert", (value,))

def high_value_handler(value):
    print(f"⚠️  HIGH VALUE ALERT: {value}")

def button_pressed():
    print("Button pressed!")

def system_ready():
    print("System is ready")
    scheduler.trigger_event("button_event")

scheduler.on(sensor_reading, when="sensor_data")
scheduler.on(high_value_handler, when="high_value_alert")
scheduler.on(button_pressed, when="button_event", repeat=True)

scheduler.do(system_ready)

scheduler.at(lambda: scheduler.trigger_event("sensor_data", (50,)), at=1000)
scheduler.at(lambda: scheduler.trigger_event("sensor_data", (150,)), at=2000)
scheduler.at(lambda: scheduler.trigger_event("button_event"), at=3000)
scheduler.at(lambda: scheduler.trigger_event("button_event"), at=4000)

scheduler.at(lambda: scheduler.stop(), at=5000)

print("Starting event-driven example...")
scheduler.start()
print("Done!")
