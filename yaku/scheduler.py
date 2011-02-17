import traceback
import sys
import Queue
import threading

from yaku.task_manager \
    import \
        run_task, order_tasks, TaskManager
import yaku.errors

def run_tasks(ctx, tasks=None):
    if tasks is None:
        tasks = ctx.tasks
    task_manager = TaskManager(tasks)
    s = SerialRunner(ctx, task_manager)
    s.start()
    s.run()

class SerialRunner(object):
    def __init__(self, ctx, task_manager):
        self.ctx = ctx
        self.task_manager = task_manager

    def start(self):
        # Dummy to give same interface as ParallelRunner
        pass

    def run(self):
        grp = self.task_manager.next_set()
        while grp:
            for task in grp:
                run_task(self.ctx, task)
            grp = self.task_manager.next_set()

class ParallelRunner(object):
    def __init__(self, ctx, task_manager, maxjobs=1):
        self.njobs = maxjobs
        self.task_manager = task_manager
        self.ctx = ctx

        self.worker_queue = Queue.Queue()
        self.error_out = Queue.Queue()
        self.failure_lock = threading.Lock()
        self.stop = False

    def start(self):
        def _worker():
            # XXX: this whole thing is an hack - find a better way to
            # notify task execution failure to all worker threads
            while not self.stop:
                task = self.worker_queue.get()
                try:
                    run_task(self.ctx, task)
                except yaku.errors.TaskRunFailure, e:
                    self.failure_lock.acquire()
                    self.stop = True
                    self.failure_lock.release()
                    task.error_msg = e.explain
                    task.error_cmd = e.cmd
                    self.error_out.put(task)
                except Exception, e:
                    exc_type, exc_value, tb = sys.exc_info()
                    lines = traceback.format_exception(exc_type, exc_value, tb)
                    self.failure_lock.acquire()
                    self.stop = True
                    self.failure_lock.release()
                    task.error_msg = "".join(lines)
                    task.error_cmd = []
                    self.error_out.put(task)
                self.worker_queue.task_done()

        for i in range(self.njobs):
            t = threading.Thread(target=_worker)
            t.setDaemon(True)
            t.start()

    def run(self):
        grp = self.task_manager.next_set()
        while grp:
            for task in grp:
                self.worker_queue.put(task)
            # XXX: we only join once we detect the worker queue to be empty, to
            # avoid blocking for a long time. This is naive, and will break if
            # the worker_queue is filled after this point
            while not self.stop:
                if self.worker_queue.empty():
                    self.worker_queue.join()
                    break
            if not self.error_out.empty():
                task = self.error_out.get()
                msg = task.error_msg
                cmd = task.error_cmd
                raise yaku.errors.TaskRunFailure(cmd, msg)

            grp = self.task_manager.next_set()
