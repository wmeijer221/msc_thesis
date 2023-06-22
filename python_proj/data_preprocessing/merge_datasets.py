"""
Inputs mutiple chronological datafiles and merges them into one.
"""

import json

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import safe_get_argv

if __name__ == "__main__":
    exp_utils.load_paths_for_eco()

    # Sets path for chronological input data
    input_pr_dataset_names = [entry for entry in safe_get_argv(key="-pd", default="").split(",")
                              if entry != '']
    input_issue_dataset_names = [entry for entry in safe_get_argv(key='-id', default="").split(",")
                                 if entry != '']

    output_file_name = safe_get_argv(key='-o', default="complete_dataset")

    data_iterator = exp_utils.iterate_through_multiple_chronological_issue_pr_datasets(
        input_issue_dataset_names,
        input_pr_dataset_names)

    output_path = exp_utils.CHRONOLOGICAL_DATASET_PATH(
        data_type="", file_name=output_file_name)
    print(f'Outputting at: "{output_path}".')
    with open(output_path, "w+", encoding="utf-8") as output_file:
        for entry in data_iterator:
            output_file.write(json.dumps(output_file) + "\n")
