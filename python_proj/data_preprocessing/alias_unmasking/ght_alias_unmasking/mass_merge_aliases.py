"""
Merges aliases of all projects using GHT alias unmasking by Vasilescu et al.
"""

import json
from os import path, remove
import csv

import python_proj.utils.exp_utils as exp_utils
import python_proj.data_preprocessing.alias_unmasking.ght_alias_unmasking.merge_aliases as ght


def merge_project_aliases(project_name: str, all_pairs_path: str):
    """Merges the aliases at an intra-project level."""

    owner, repo = project_name.strip().split("/")[0:2]
    input_path = exp_utils.RAW_DATA_PATH(
        data_type='user-ids',
        owner=owner, repo=repo, ext="")

    # Skips all projects with only one user.
    with open(input_path, 'r', encoding='utf-8') as input_file:
        j_data = json.loads(input_file.read())
        if len(j_data) == 1:
            return

    output_dir = exp_utils.BASE_PATH + '/temp/mass_user_merge/'

    # Merges aliases
    ght.merge_aliases(
        input_path, output_dir,
        thr_min=1, thr_max=3,
        min_prefix_length=4,
        require_email=True,
        require_name=True,
        use_simple_name=False
    )

    pairs_path = output_dir + "identified_pairs.csv"

    with open(pairs_path, "r", encoding='utf-8') as pair_file:
        csv_reader = csv.reader(pair_file)
        header = next(csv_reader)

        # Writes header if necessary.
        if not path.exists(all_pairs_path):
            with open(all_pairs_path, "w+", encoding='utf-8') as all_pairs_file:
                csv_writer = csv.writer(all_pairs_file)
                csv_writer.writerow(header)

        # Adds pairs
        with open(all_pairs_path, "a+", encoding='utf-8') as all_pairs_file:
            csv_writer = csv.writer(all_pairs_file)
            csv_writer.writerow(csv_reader)


def merge_all_project_aliases():
    """Merges aliases of all projects."""
    exp_utils.load_paths_for_eco()
    proj_list_input_path = exp_utils.RAW_DATA_PATH(
        data_type='user-ids', owner="proj", repo="list", ext="")
    all_pairs_path = exp_utils.TRAIN_DATASET_PATH(
        file_name='all_identified_pairs')
    
    remove(all_pairs_path)

    with open(proj_list_input_path, "r", encoding='utf-8') as input_file:
        for entry in input_file:
            merge_project_aliases(entry, all_pairs_path)

    print(f'Stored pairs in "{all_pairs_path}".')


if __name__ == "__main__":
    merge_all_project_aliases()
