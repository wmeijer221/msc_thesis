"""
Merges aliases of all projects using GHT alias unmasking by Vasilescu et al.
"""

import json

import python_proj.utils.exp_utils as exp_utils
import python_proj.data_preprocessing.alias_unmasking.ght_alias_unmasking.merge_aliases as ght


def merge_project_aliases(project_name: str):
    owner, repo = project_name.strip().split("/")[0:2]
    input_path = exp_utils.RAW_DATA_PATH(
        data_type='user-ids',
        owner=owner, repo=repo, ext="")

    with open(input_path, 'r', encoding='utf-8') as input_file:
        j_data = json.loads(input_file.read())
        if len(j_data) == 1:
            return

    output_dir = exp_utils.BASE_PATH + '/temp/mass_user_merge/'

    ght.merge_aliases(
        input_path, output_dir,
        thr_min=1, thr_max=3,
        min_prefix_length=4,
        require_email=True,
        require_name=False,
        use_simple_name=False
    )


def merge_all_project_aliases():
    exp_utils.load_paths_for_eco()
    proj_list_output_path = exp_utils.RAW_DATA_PATH(
        data_type='user-ids', owner="proj", repo="list", ext="")

    with open(proj_list_output_path, "r", encoding='utf-8') as input_file:
        for entry in input_file:
            merge_project_aliases(entry)
            break


if __name__ == "__main__":
    merge_all_project_aliases()
