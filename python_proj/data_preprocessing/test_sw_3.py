import csv
import shutil

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.mt_utils import parallelize_tasks

import python_proj.data_preprocessing.sliding_window_2 as sw2
import python_proj.data_preprocessing.sliding_window_3 as sw3

output_sw2 = None
output_sw3 = None

def run_sw2():
    global output_sw2
    output_sw2 = sw2.sliding_window()
    tmp_sw2 = exp_utils.BASE_PATH + "/temp/test_out.csv"
    shutil.move(output_sw2, tmp_sw2)
    output_sw2 = tmp_sw2


def run_sw3():
    global output_sw3
    output_sw3 = sw3.cmd_create_sliding_window_dataset()


task = [run_sw2, run_sw3]
parallelize_tasks(task, lambda task_runnable: task_runnable(), thread_count=2)

with open(output_sw2, "r", encoding='utf-8') as sw2_file:
    sw2_reader = csv.reader(sw2_file)
    with open(output_sw3, "r", encoding='utf-8') as sw3_file:
        sw3_reader = csv.reader(sw3_file)

        zipped_reader = zip(sw2_reader, sw3_reader)
        header, sw3_header = next(zipped_reader)

        sw2_header_to_sw3_header_idx_mapping = {header: sw3_header.index(header)
                                                for header in header}

        for sw2_entry, sw3_entry in zipped_reader:
            for sw2_idx, header in enumerate(header):
                sw3_idx = sw2_header_to_sw3_header_idx_mapping[sw2_idx]

                sw2_entry = sw2_entry[sw2_idx]
                sw3_entry = sw3_entry[sw3_idx]

                if sw2_entry != sw3_entry:
                    print(f'{header}: {sw2_entry}, {sw3_entry}')
