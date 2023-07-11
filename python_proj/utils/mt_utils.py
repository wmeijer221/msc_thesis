"""
Contains utility scripts for multithreading related tasks.
"""

from typing import Callable, Generator
import multiprocessing


class SimpleConsumer(multiprocessing.Process):
    """Simple consumer thread."""

    class TerminateTask:
        """When received by the simple consumer, it terminates."""

    def __init__(
        self,
        on_message_received: Callable,
        task_list: multiprocessing.JoinableQueue,
        worker_index: int, 
        consumer_name: str = "SimpleConsumer",
        print_lifetime_events: bool = True,
        *args, **kwargs
    ) -> None:
        super().__init__()
        self._on_message_received = on_message_received
        self._task_list = task_list
        self._worker_index = worker_index
        self._args = args
        self._kwargs = kwargs
        self._consumer_name = consumer_name
        self._print_lifetime_events = print_lifetime_events
        if print_lifetime_events:
            print(f"{consumer_name}-{worker_index} started.")

    def run(self) -> None:
        is_running = True
        while is_running:
            task = self._task_list.get()
            if isinstance(task, SimpleConsumer.TerminateTask):
                if self._print_lifetime_events:
                    print(
                        f'{self._consumer_name}-{self._worker_index}: Received termination task.')
                is_running = False
                break
            try:
                task_kwargs = {**self._kwargs, **task,
                               "worker_index": self._worker_index}
                self._on_message_received(*self._args, **task_kwargs)
            except Exception as ex:
                print(
                    f"{self._consumer_name}-{self._worker_index}: Failed with entry {task}: {ex}.")
                raise

        if self._print_lifetime_events:
            print(f'{self._consumer_name}-{self._worker_index}: Stopped.')


def parallelize_tasks(
    tasks: list | Generator,
    on_message_received: Callable,
    thread_count: int,
    *args, **kwargs
):
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
    total_tasks = len(tasks) if isinstance(tasks, list) else "unknown"
    for task_id, task in enumerate(tasks, start=1):
        work_task = {
            'task': task,
            'task_id': task_id,
            'total_tasks': total_tasks
        }
        worklist.put(work_task)

    # Kills workers.
    for _ in range(thread_count):
        worklist.put(SimpleConsumer.TerminateTask())

    # Waits until workers terminate.
    for worker in workers:
        worker.join()
