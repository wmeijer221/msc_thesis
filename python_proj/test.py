from python_proj.utils.mt_utils import parallelize_tasks


import random

from threading import Lock


my_base_dict = {
    "a": 451619,
    "b": 342,
    "c": 4747,
    "d": 24368,
}


def proc_task(task: str, *args, **kwargs):
    task = task

    other = {
        "a": int(task),
        "b": int(task) * 2,
        "c": int(task) ** 2,
        "d": int(task) / 5,
    }

    res = {}

    for field in other.keys():
        res[field] = my_base_dict[field] - other[field]

    print(res)


tasks = [str(i) for i in range(15)]
parallelize_tasks(tasks, proc_task, 4)
