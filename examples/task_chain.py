from events import Work

scheduler = Work()

def task_a():
    scheduler.print("Task A started")
    scheduler.trigger_event("task_a_done")

def task_b():
    scheduler.print("Task B started (after A)")
    scheduler.trigger_event("task_b_done")

def task_c():
    scheduler.print("Task C started (after B)")
    scheduler.trigger_event("task_c_done")

def task_d():
    scheduler.print("Task D started (after C)")
    scheduler.trigger_event("task_d_done")

def all_done():
    scheduler.print("\n✓ All tasks completed!")
    scheduler.stop()

scheduler.do(task_a)

scheduler.on(task_b, when="task_a_done")

scheduler.on(task_c, when="task_b_done")

scheduler.on(task_d, when="task_c_done")

scheduler.on(all_done, when="task_d_done")

print("Task Chain Example")
print("=" * 40)
print("Executing: A → B → C → D")
print("=" * 40)

scheduler.start()
print("Done!")
