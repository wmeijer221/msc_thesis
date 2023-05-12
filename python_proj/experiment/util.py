from typing import Callable
import multiprocessing
from typing import Any


def safe_index(list: list, entry: object) -> int:
    try:
        return list.index(entry)
    except ValueError:
        return -1


def get_arg(args: list, key: str, default: object = None) -> object:
    if (idx := safe_index(args, key)) >= 0:
        return args[idx + 1]
    return default


def safe_add_list_element(dictionary: dict[Any, list], key, value):
    if key in dictionary:
        dictionary[key].append(value)
    else:
        dictionary[key] = [value]


def safe_add_set_element(dictionary: dict[Any, set], key, value):
    if key in dictionary:
        dictionary[key].add(value)
    else:
        dictionary[key] = set()
        dictionary[key].add(value)


class SimpleConsumer(multiprocessing.Process):

    def __init__(self, on_message_received: Callable, task_list: multiprocessing.JoinableQueue, worker_index: int, *args, **kwargs) -> None:
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
                task_kwargs = {**self._kwargs, **task}
                self._on_message_received(*self._args, **task_kwargs)
            except Exception as ex:
                print(f"Failed with entry {task}: {ex}.")
                raise
        print(f'Consumer-{self._worker_index} stopped.')


def parallelize_tasks(tasks: list, on_message_received: Callable, thread_count: int):
    worklist = multiprocessing.JoinableQueue()
    workers: list[SimpleConsumer] = [None] * thread_count

    # Creates workers.
    for index in range(thread_count):
        worker = SimpleConsumer(on_message_received, worklist, index)
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


def get_nested(obj: dict, key: list[str]) -> Any | None:
    """
    Returns value corresponding to the key by recursively
    searching in the given dictionary.

    :params obj: The used dictionary.
    :params key: The query key.
    """

    current = obj
    for key in key:
        if not key in current:
            return None
        current = current[key]
    return current
