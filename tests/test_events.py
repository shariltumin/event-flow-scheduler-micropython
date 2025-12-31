import sys
sys.path.insert(0, '.')

from events import Work, Task
from time import sleep_ms, ticks_ms

def test_task_creation():
    print("Testing Task creation...")
    task = Task(lambda: None, (), 100, 0, '', 1)
    assert task.task_id == 1
    assert task.delay == 100
    assert task.cancelled == False
    print("✓ Task creation passed")

def test_work_initialization():
    print("Testing Work initialization...")
    work = Work(max_tasks=50)
    assert work._max_tasks == 50
    assert len(work._tasks) == 0
    assert len(work._heap) == 0
    print("✓ Work initialization passed")

def test_do_scheduling():
    print("Testing do() scheduling...")
    work = Work()
    executed = []
    
    def task():
        executed.append(1)
    
    task_id = work.do(task)
    assert task_id is not None
    assert task_id in work._tasks
    print("✓ do() scheduling passed")

def test_at_scheduling():
    print("Testing at() scheduling...")
    work = Work()
    
    def task():
        pass
    
    task_id = work.at(task, at=1000)
    assert task_id is not None
    task_obj = work._tasks[task_id]
    assert task_obj.delay == 1000
    print("✓ at() scheduling passed")

def test_repeat_scheduling():
    print("Testing repeat() scheduling...")
    work = Work()
    
    def task():
        pass
    
    task_id = work.repeat(task, every=500)
    assert task_id is not None
    task_obj = work._tasks[task_id]
    assert task_obj.repeat == 500
    print("✓ repeat() scheduling passed")

def test_event_scheduling():
    print("Testing on() event scheduling...")
    work = Work()
    
    def task():
        pass
    
    task_id = work.on(task, when="test_event")
    assert task_id is not None
    assert "test_event" in work._flags
    assert len(work._flags["test_event"]) == 1
    print("✓ on() event scheduling passed")

def test_trigger_event():
    print("Testing trigger_event()...")
    work = Work()
    triggered = []
    
    def task(value):
        triggered.append(value)
    
    work.on(task, when="test_event")
    count = work.trigger_event("test_event", (42,))
    assert count == 1
    print("✓ trigger_event() passed")

def test_cancel_task():
    print("Testing cancel()...")
    work = Work()
    
    def task():
        pass
    
    task_id = work.do(task)
    result = work.cancel(task_id)
    assert result == True
    assert work._tasks[task_id].cancelled == True
    print("✓ cancel() passed")

def test_task_status():
    print("Testing status()...")
    work = Work()
    
    def my_task():
        pass
    
    task_id = work.do(my_task)
    status = work.status(task_id)
    assert status["id"] == task_id
    assert status["job"] == "my_task"
    assert status["cancelled"] == False
    print("✓ status() passed")

def test_send():
    print("Testing send()...")
    work = Work()
    
    def task(value):
        pass
    
    task_id = work.do(task, (1,))
    result = work.send((2,), task_id)
    assert result == True
    assert work._tasks[task_id].params == (2,)
    print("✓ send() passed")

def test_set_repeat():
    print("Testing set_repeat()...")
    work = Work()
    
    def task():
        pass
    
    task_id = work.repeat(task, every=1000)
    result = work.set_repeat(2000, task_id)
    assert result == True
    assert work._tasks[task_id].repeat == 2000
    print("✓ set_repeat() passed")

def test_task_count():
    print("Testing task_count()...")
    work = Work()
    
    def task():
        pass
    
    assert work.task_count() == 0
    work.do(task)
    work.do(task)
    assert work.task_count() == 2
    print("✓ task_count() passed")

def test_max_tasks_limit():
    print("Testing max_tasks limit...")
    work = Work(max_tasks=2)
    
    def task():
        pass
    
    task1 = work.do(task)
    task2 = work.do(task)
    task3 = work.do(task)
    
    assert task1 is not None
    assert task2 is not None
    assert task3 is None
    print("✓ max_tasks limit passed")

def test_invalid_parameters():
    print("Testing invalid parameters...")
    work = Work()
    
    result = work.do(None)
    assert result is None
    
    result = work.repeat(lambda: None, every=0)
    assert result is None
    
    result = work.on(lambda: None, when=None)
    assert result is None
    
    print("✓ invalid parameters handling passed")

def test_cleanup():
    print("Testing lazy cleanup...")
    work = Work()
    
    def task():
        pass
    
    task_id = work.do(task)
    work.cancel(task_id)
    
    work._last_cleanup = ticks_ms() - 11000
    work._cleanup_lazy()
    
    assert task_id not in work._tasks
    print("✓ lazy cleanup passed")

def run_all_tests():
    print("=" * 50)
    print("Running Event Scheduler Tests")
    print("=" * 50)
    
    tests = [
        test_task_creation,
        test_work_initialization,
        test_do_scheduling,
        test_at_scheduling,
        test_repeat_scheduling,
        test_event_scheduling,
        test_trigger_event,
        test_cancel_task,
        test_task_status,
        test_send,
        test_set_repeat,
        test_task_count,
        test_max_tasks_limit,
        test_invalid_parameters,
        test_cleanup,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
