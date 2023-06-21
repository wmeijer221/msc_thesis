import itertools
from typing import Generator
from dataclasses import dataclass
import json

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import safe_get_argv
from python_proj.utils.util import SafeDict


def get_users(activity: dict) -> Generator[dict, None, None]:
    """Returns submitter, integrator, and commenter user data."""
    yield activity['user_data']
    if 'merged' in activity:
        integrator_key = exp_utils.get_integrator_key(activity)
        yield activity[integrator_key]
    if activity['comments'] == 0:
        return
    for comment in activity['comments_data']:
        yield comment['user_data']


exp_utils.load_paths_for_eco()
# Sets path for chronological input data
input_pr_dataset_names = [entry for entry in safe_get_argv(key="-pd", default="").split(",")
                          if entry != '']
input_issue_dataset_names = [entry for entry in safe_get_argv(key='-id', default="").split(",")
                             if entry != '']

data_set_names = list(itertools.chain(
    input_pr_dataset_names, input_issue_dataset_names))
data_sources = ["pull-requests"] * len(input_pr_dataset_names)
data_sources.extend(["issues"] * len(input_issue_dataset_names))

generator = exp_utils.iterate_through_multiple_chronological_datasets(
    data_set_names, data_sources=data_sources)


@dataclass
class UserData:
    """Contains hashable user data."""
    id: int = -1
    data: dict = None

    def __hash__(self) -> int:
        return self.id


# Stores all users.
users_per_project = SafeDict(default_value=set)
for entry in generator:
    project = entry["__source_path"]
    for user in get_users(entry):
        user_id = user['id']
        ud = UserData(user_id, user)
        users_per_project[project].add(ud)

# Writes all users.
proj_list_output_path = exp_utils.RAW_DATA_PATH(
    data_type='user-ids', owner="proj", repo="list")
proj_list_output_file = open(proj_list_output_path, "w+", encoding="utf-8")
for project, users in users_per_project.items():
    (owner, repo) = exp_utils.get_owner_and_repo_from_source_path(project)
    proj_list_output_file.write(f'{owner}/{repo}\n')
    output_path = exp_utils.RAW_DATA_PATH(
        data_type="user-ids", owner=owner, repo=repo)
    with open(output_path, "w+", encoding='utf-8') as output_file:
        users = list(users)
        output_file.write(json.dumps(users))
