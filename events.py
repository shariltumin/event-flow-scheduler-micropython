#
# MIT License
# 
# Copyright (c) 2025 shariltumin
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from time import sleep_ms, ticks_ms, ticks_diff
import heapq
from micropython import schedule

class Task:
    def __init__(
        self,
        job= None,
        params= (),
        delay= 0,
        repeat= 0,
        flag= '',
        task_id= 0,
    ):
        self.job = job
        self.params = params
        self.delay = delay
        self.repeat = repeat
        self.flag = flag
        self.task_id = task_id
        self.cancelled = False
        self.event_triggered = False
        self.next_run = ticks_ms() + delay

    def __lt__(self, other):
        return self.next_run < other.next_run

    def __repr__(self):
        try:
            job_name = self.job.__name__
        except AttributeError:
            job_name = "anonymous"
        return f"Task(id={self.task_id}, job={job_name}, next_run={self.next_run})"

class Work:
    def __init__(self, max_tasks=256):
        if not isinstance(max_tasks, int) or max_tasks < 1:
            raise ValueError('max_tasks must be a positive integer')
        self._heap = []
        self._tasks = {}
        self._flags = {}
        self._task_counter = 0
        self._running = False
        self._max_tasks = max_tasks
        self._last_cleanup = ticks_ms()
        self._last_heap_compact = ticks_ms()

    def _generate_task_id(self):
        cnt = 100
        while cnt > 0:
            self._task_counter = (self._task_counter % 1_000_000) + 1
            if self._task_counter not in self._tasks:
                return self._task_counter
            cnt -= 1
        raise OSError("No free task identifier available")

    def _cleanup_lazy(self):
        now = ticks_ms()
        if ticks_diff(now, self._last_cleanup) < 10_000:
            return
        self._last_cleanup = now
        self._flags = {k: [t for t in v if not t.cancelled] for k, v in self._flags.items()}
        self._flags = {k: v for k, v in self._flags.items() if v}
        self._tasks = {tid: t for tid, t in self._tasks.items() if not t.cancelled}

    def _compact_heap(self):
        now = ticks_ms()
        if ticks_diff(now, self._last_heap_compact) < 60_000:
            return
        self._last_heap_compact = now
        alive = [t for t in self._heap if not t.cancelled]
        heapq.heapify(alive)
        self._heap = alive

    def status(self, task_id= 0):
        task = self._tasks.get(task_id or self.current_task_id())
        if not task:
            return None
        try:
            job_name = task.job.__name__
        except AttributeError:
            job_name = "anonymous"
        return {
            "id": task.task_id,
            "job": job_name,
            "params": task.params,
            "delay": task.delay,
            "repeat": task.repeat,
            "flag": task.flag,
            "event_triggered": task.event_triggered,
            "next_run": task.next_run,
            "cancelled": task.cancelled,
        }

    def send(self, pkg= (), task_id= 0):
        if not isinstance(pkg, tuple):
            pkg = (pkg,)
        task = self._tasks.get(task_id or self.current_task_id())
        if not task:
            return False
        if pkg != ():
            task.params = pkg
            return True
        return False

    def trigger_event(self, flag= None, pkg= ()):
        if flag is None or flag not in self._flags:
            return 0
        triggered_count = 0
        for task in self._flags[flag]:
            if task.cancelled or task.event_triggered:
                continue
            task.event_triggered = True
            if not isinstance(pkg, tuple):
                pkg = (pkg,)
            if pkg != ():
                task.params = pkg
            task.next_run = ticks_ms()
            heapq.heappush(self._heap, task)
            triggered_count += 1
            if task.repeat <= 0:
                task.flag = None
        # Remove tasks that are now ready
        self._flags[flag] = [t for t in self._flags[flag] if t.flag == flag]
        if not self._flags[flag]:
            del self._flags[flag]
        return triggered_count

    def await_event(self, flag= None, task_id= 0):
        if flag is None:
            return False
        task = self._tasks.get(task_id or self.current_task_id())
        if not task:
            return False
        task.flag = flag
        task.event_triggered = False
        task.repeat = 1
        self._flags.setdefault(flag, []).append(task)
        return True

    def set_repeat(self, repeat_interval= 100, task_id = 0):
        if not isinstance(repeat_interval, int) or repeat_interval < 0:
            return False
        task = self._tasks.get(task_id or self.current_task_id())
        if task:
            task.repeat = repeat_interval
            return True
        return False

    def current_task_id(self):
        return getattr(self, "_current_tid", None)

    def _schedule_task(
        self,
        job= None,
        params= (),
        delay= 0,
        repeat= 0,
        wait_for= None,
        task_id= 0,
    ):
        if not isinstance(params, tuple):
            params = (params,)
        if len(self._tasks) >= self._max_tasks:
            self.print("Maximum task limit reached")
            return None

        if not (callable(job) and isinstance(params, tuple) and
                isinstance(delay, int) and delay >= 0 and
                (isinstance(repeat, int) or isinstance(repeat, bool))):
            self.print("Invalid schedule_task parameters")
            return None

        if isinstance(repeat, bool):
            repeat = 1 if repeat else 0

        if isinstance(task_id, int) and task_id != 0:
            if task_id in self._tasks:
                task_id = 0
        else:
            task_id = 0

        task_id = task_id or self._generate_task_id()
        task = Task(job, params, delay, repeat, wait_for or None, task_id)
        self._tasks[task_id] = task

        if wait_for:
            self._flags.setdefault(wait_for, []).append(task)
        else:
            heapq.heappush(self._heap, task)
        return task_id

    def repeat(
        self,
        job= None,
        params= (),
        at= 0,
        every= 0,
        task_id= 0,
    ):
        if every <= 0:
            self.print("repeat interval must be positive")
            return None
        return self._schedule_task(job, params, delay=at, repeat=every, task_id=task_id)

    def at(
        self,
        job= None,
        params= (),
        at= 0,
        task_id= 0,
    ):
        return self._schedule_task(job, params, delay=at, task_id=task_id)

    def do(
        self,
        job= None,
        params= (),
        task_id= 0,
    ):
        return self._schedule_task(job, params, task_id=task_id)

    def on(
        self,
        job= None,
        params= (),
        when= None,
        at= 0,
        repeat= False,
        task_id= 0,
    ):
        if when is None:
            self.print("event flag 'when' cannot be None")
            return None
        return self._schedule_task(job, params, wait_for=when, delay=at, repeat=repeat, task_id=task_id)

    def cancel(self, task_id= 0):
        task = self._tasks.get(task_id)
        if not task:
            return False
        task.cancelled = True
        if task.flag and task.flag in self._flags:
            try:
                self._flags[task.flag].remove(task)
                if not self._flags[task.flag]:
                    del self._flags[task.flag]
            except ValueError:
                pass
        return True

    def abort_current_task(self):
        tid = self.current_task_id()
        return self.cancel(tid) if tid else False

    def print(self, *txt):
        try:
            schedule(lambda args: print(*args), txt)
        except Exception:
            print(f"ERROR in scheduler print for task {self.current_task_id()}:", *txt)

    def run(self, p=None, q=()):
        if p is None:
            return
        if not isinstance(q, tuple):
            q = (q,)
        try:
            schedule(lambda args: p(*args), q)
            sleep_ms(0)
        except Exception as e:
            self.print(f"Task {self.current_task_id()} run error: {e}")

    def stop(self):
        self._running = False
        self._heap.clear()
        self._tasks.clear()
        self._flags.clear()

    def task_count(self):
        return len(self._tasks)

    def pending_count(self):
        return len(self._heap)

    def start(self):
        self._running = True
        while self._running:
            try:
                self._cleanup_lazy()
                self._compact_heap()

                if not self._heap:
                    sleep_ms(100)
                    continue

                now = ticks_ms()
                task = self._heap[0]

                if task.cancelled or (task.flag and not task.event_triggered):
                    heapq.heappop(self._heap)
                    continue

                wait_time = ticks_diff(task.next_run, now)
                if wait_time > 0:
                    sleep_ms(min(wait_time, 100))
                    continue

                task = heapq.heappop(self._heap)
                self._current_tid = task.task_id

                try:
                    task.job(*task.params)
                except Exception as e:
                    self.print(f"Task {task.task_id} execution error: {e}")

                if task.repeat > 0 and not task.cancelled:
                    task.next_run = now + task.repeat
                    heapq.heappush(self._heap, task)
                else:
                    self._tasks.pop(task.task_id, None)
                    if len(self._tasks) == 0: self._running = False # no more task

                if task.flag:
                    task.event_triggered = False
                    if task.repeat <= 0 or task.cancelled:
                        if task.flag in self._flags and task in self._flags[task.flag]:
                            self._flags[task.flag].remove(task)
                            if not self._flags[task.flag]:
                                del self._flags[task.flag]
                        task.flag = None

            except Exception as e:
                self.print(f"Scheduler error: {e}")
                sleep_ms(100)

        self._running = False

