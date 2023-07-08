

from python_proj.utils.mt_utils import parallelize_tasks


MY_VARIALBE = None


class SomeClass:
    def __init__(self) -> None:
        global MY_VARIALBE

        if MY_VARIALBE is None:
            print('it was none')
            MY_VARIALBE = 1


def do_task(*args, **kwargs):
    SomeClass()


tasks = list(range(32))

parallelize_tasks(tasks, do_task, thread_count=3)
