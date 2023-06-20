"""
Generates a dictionary of each user ID and the
number of PRs committed by that person.
"""

import json

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import get_argv
from python_proj.utils.util import SafeDict


def create_committer_frequency_list():
    """
    prints list of users and the number of pull_requests they made.
    """
    
    exp_utils.load_paths_for_eco()
    exp_utils.load_paths_for_data_path()

    file_names = get_argv(key="-f").split(",")
    pulls_per_user = SafeDict(default_value=0)
    data_iterator = exp_utils.iterate_through_multiple_chronological_datasets(
        file_names)
    for entry in data_iterator:
        login = entry['user_data']["login"]
        pulls_per_user[login] += 1
    user_pull_count = list(pulls_per_user.items())
    user_pull_count.sort(key=lambda x: -x[1])
    print(json.dumps(user_pull_count))


if __name__ == "__main__":
    create_committer_frequency_list()
