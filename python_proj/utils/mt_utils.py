"""
Contains utility scripts for multithreading related tasks.
"""

from typing import Callable, Iterator
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
        result_queue: multiprocessing.Queue,
        consumer_name: str = "SimpleConsumer",
        print_lifetime_events: bool = True,
        *args, **kwargs
    ) -> None:
        super().__init__()
        self._on_message_received = on_message_received
        self._task_list = task_list
        self._worker_index = worker_index
        self._result_queue = result_queue
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
                task_kwargs = {
                    **self._kwargs, **task,
                    "worker_index": self._worker_index
                }
                result = self._on_message_received(*self._args, **task_kwargs)
                if not result is None:
                    self._result_queue.put(result)
            except Exception as ex:
                print(
                    f"{self._consumer_name}-{self._worker_index}: Failed with entry {task}: {ex}.")
                raise

        if self._print_lifetime_events:
            print(f'{self._consumer_name}-{self._worker_index}: Stopped.')


def parallelize_tasks(
    tasks: list | Iterator,
    on_message_received: Callable,
    thread_count: int | None = None,
    return_results: bool = False,
    *args, **kwargs
) -> list | None:
    """
    Starts a bunch of simple consumer threads that work away on the given tasks. 
    The tasks are passed through ``task`` parameter; i.e., if it's a dict is not unpacked.
    """

    if thread_count is None:
        thread_count = min(len(tasks), 8)

    worklist = multiprocessing.JoinableQueue()
    workers: list[SimpleConsumer] = [None] * thread_count

    result_queue = multiprocessing.Queue() if return_results else None

    # Creates workers.
    for index in range(thread_count):
        worker = SimpleConsumer(on_message_received,
                                worklist, index,
                                result_queue,
                                *args, **kwargs)
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

    # Returns the results if necessary.
    if not return_results:
        return
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())
    return results


def parallelize_tasks_2(
    tasks: Iterator,
    on_message_received: Callable,
    thread_count: int = 1,
    return_results: bool = False,
    *args, **kwargs
):
    executor = ExecutorService(thread_count, return_results, *args, **kwargs)
    executor.start()
    total_tasks = len(tasks) if isinstance(tasks, list) else "unknown"
    for task_id, task in enumerate(tasks, start=1):
        executor.submit(
            task_callable=on_message_received,
            task=task,
            task_id=task_id,
            total_tasks=total_tasks
        )
    executor.stop()
    results = executor.get_results()
    return results


class ExecutorService:
    def __init__(
        self,
        thread_count: int = 1,
        return_results: bool = False,
        print_lifetime_events: bool = True,
        *args, **kwargs
    ):
        if thread_count < 1:
            raise ValueError("There's a minimum of 1 thread.")

        self._thread_count = thread_count
        self._return_results = return_results
        self._print_lifetime_events = print_lifetime_events
        self._args = args
        self._kwargs = kwargs

        self._worklist = multiprocessing.JoinableQueue()
        self._workers: list[SimpleConsumer] = [None] * thread_count
        self._result_queue = multiprocessing.Queue() if return_results else None

    def do_task(self, task_callable, targs, tkwargs, *args, **kwargs):
        return task_callable(task_callable, *targs, *args, **tkwargs, **kwargs)

    def start(self):
        if self._print_lifetime_events:
            print("Executor Starting!")
        # Creates workers.
        for index in range(self._thread_count):
            worker = SimpleConsumer(
                self.do_task,
                self._worklist, index,
                result_queue=self._result_queue,
                print_lifetime_events=self._print_lifetime_events,
                *self._args, **self._kwargs
            )
            worker.start()
            self._workers[index] = worker

        if self._print_lifetime_events:
            print("Executor Started!")

    def submit(self, task_callable: Callable, *targs, **tkwargs):
        task_wrapper = {
            'task_callable': task_callable,
            'targs': targs,
            'tkwargs': tkwargs
        }
        self._worklist.put(task_wrapper)

    def stop(self):
        if self._print_lifetime_events:
            print("Executor Stopping!")
        # Kills workers.
        for _ in range(self._thread_count):
            self._worklist.put(SimpleConsumer.TerminateTask())
        # Waits until workers terminate.
        for worker in self._workers:
            worker.join()
            print(self._workers)
        if self._print_lifetime_events:
            print("Executor Stopped!")

    def get_results(self) -> list | None:
        # Returns the results if necessary.
        if not self._return_results:
            return
        results = []
        while not self._result_queue.empty():
            results.append(self._result_queue.get())
        return results
