from typing import Any


def safe_index(list: list, entry: object) -> int:
    try:
        return list.index(entry)
    except ValueError:
        return -1


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



import multiprocessing
from typing import Callable


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
                break
            try:
                task_kwargs = {**self._kwargs, **task}
                self._on_message_received(*self._args, **task_kwargs)
            except Exception as ex:
                print(f"Failed with entry {task}: {ex}.")
        print(f'Consumer-{self._worker_index} stopped.')
