from python_proj.utils.mt_utils import parallelize_tasks, SafeCounter

import multiprocessing


some_pre_filled_dict = {
    'value_a': 1,
    'value_b': 2
}

the_counter = SafeCounter()


def task(task, counter: SafeCounter, *ags, **kwargs):
    ret = counter.get_next()
    print(ret)
    return ret

    if task % 2 == 0:
        return some_pre_filled_dict['value_a']
    else:
        return some_pre_filled_dict['value_b']


results = parallelize_tasks(
    range(0, 1000), task, 16, return_results=True, counter=the_counter)

total = sum(results)
print(total)
