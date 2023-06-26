"""
Contains utility scripts for multithreading related tasks.
"""

from typing import Callable
import multiprocessing


class SimpleConsumer(multiprocessing.Process):

    def __init__(self, on_message_received: Callable, task_list: multiprocessing.JoinableQueue,
                 worker_index: int, *args, **kwargs) -> None:
        super().__init__()
        self._on_message_received = on_message_received
        self._task_list = task_list
        self._worker_index = worker_index
        self._args = args
        self._kwargs = kwargs
        print(f"Consumer-{worker_index} started.")

    def run(self) -> None:
        is_running = True
        while is_running:
            task = self._task_list.get()
            if task is None:
                is_running = False
                break
            try:
                task_kwargs = {**self._kwargs, **task,
                               "worker_index": self._worker_index}
                self._on_message_received(*self._args, **task_kwargs)
            except Exception as ex:
                print(f"Failed with entry {task}: {ex}.")
                raise
        print(f'Consumer-{self._worker_index} stopped.')


def parallelize_tasks(tasks: list, on_message_received: Callable, thread_count: int, *args, **kwargs):
    """
    Starts a bunch of simple consumer threads that work away on the given tasks. 
    The tasks are passed through ``task`` parameter; i.e., if it's a dict is not unpacked.
    """

    worklist = multiprocessing.JoinableQueue()
    workers: list[SimpleConsumer] = [None] * thread_count

    # Creates workers.
    for index in range(thread_count):
        worker = SimpleConsumer(on_message_received,
                                worklist, index, *args, **kwargs)
        worker.start()
        workers[index] = worker

    # Creates tasks.
    total_tasks = len(tasks)
    for task_id, task in enumerate(tasks, start=1):
        work_task = {
            'task': task,
            'task_id': task_id,
            'total_tasks': total_tasks
        }
        worklist.put(work_task)

    # Kills workers.
    for _ in range(thread_count):
        worklist.put(None)

    # Waits until workers terminate.
    for worker in workers:
        worker.join()
