import Queue
import threading

from yaku.task_manager \
    import \
        run_task, order_tasks, TaskManager

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
        ordered_tasks = order_tasks(self.task_manager.tasks)
        for t in ordered_tasks:
            run_task(self.ctx, t)

class ParallelRunner(object):
    def __init__(self, ctx, task_manager, maxjobs=1):
        self.njobs = maxjobs
        self.task_manager = task_manager
        self.ctx = ctx

        self.worker_queue = Queue.Queue()

    def start(self):
        def _worker():
            while True:
                task = self.worker_queue.get()
                run_task(self.ctx, task)
                #task.run()
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
            while True:
                if self.worker_queue.empty():
                    self.worker_queue.join()
                    break
            grp = self.task_manager.next_set()
