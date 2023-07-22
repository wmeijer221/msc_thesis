from python_proj.utils.mt_utils import parallelize_tasks, parallelize_tasks_2, ExecutorService
from python_proj.utils.util import Counter

import multiprocessing


some_pre_filled_dict = {
    'value_a': 1,
    'value_b': 2
}

the_counter = Counter()


def task(*args, **kwargs):
    return 2

    if task % 2 == 0:
        return some_pre_filled_dict['value_a']
    else:
        return some_pre_filled_dict['value_b']


results = parallelize_tasks(
    range(0, 10000), task, 16, return_results=True, counter=the_counter)

total = sum(results)
print(total)


# the_counter = Counter()
# executor = ExecutorService(16, True, print_lifetime_events=False)
# executor.start()

# for i in range(0, 1000):
#     executor.submit(task, counter=the_counter)

# executor.stop()
# results = executor.get_results()
# total_2 = sum(results)
# print(total_2)


# the_counter_2 = Counter()

# results = parallelize_tasks_2(
#     tasks=range(0, 1000), on_message_received=task,
#     thread_count=2, return_results=True,
#     counter=the_counter_2)

# total = sum(results)
# print(total)
