import itertools
from typing import Generator
from dataclasses import dataclass
import json

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import safe_get_argv
from python_proj.utils.util import SafeDict


@dataclass
class UserData:
    """Contains hashable user data."""
    id: int = -1
    data: dict = None

    def __hash__(self) -> int:
        return self.id


def get_users(activity: dict) -> Generator[dict, None, None]:
    """Returns submitter, integrator, and commenter user data."""
    if 'user_data' in activity:
        yield activity['user_data']
    if 'merged' in activity:
        integrator_key = exp_utils.get_integrator_key(activity)
        if integrator_key in activity:
            yield activity[integrator_key]
    if not "comments" in activity \
            or activity['comments'] == 0 \
                or "comments_data" not in activity:
        return
    for comment in activity['comments_data']:
        if 'user_data' in comment:
            yield comment['user_data']


def create_project_user_list(input_pr_dataset_names: list[str],
                             input_issue_dataset_names: list[str],
                             ext: str):
    data_set_names = list(itertools.chain(
        input_pr_dataset_names, input_issue_dataset_names))
    data_sources = ["pull-requests"] * len(input_pr_dataset_names)
    data_sources.extend(["issues"] * len(input_issue_dataset_names))

    generator = exp_utils.iterate_through_multiple_chronological_datasets(
        data_set_names, data_sources=data_sources)

    # Stores all users.
    users_per_project = SafeDict(default_value=set)
    for entry in generator:
        project = entry["__source_path"]
        for user in get_users(entry):
            if not 'id' in user:
                continue
            user_id = user['id']
            ud = UserData(user_id, user)
            users_per_project[project].add(ud)

    # Writes all users to a file.
    proj_list_output_path = exp_utils.RAW_DATA_PATH(
        data_type='user-ids', owner="proj", repo="list", ext=ext)
    proj_list_output_file = open(proj_list_output_path, "w+", encoding="utf-8")
    for project, users in users_per_project.items():
        (owner, repo) = exp_utils.get_owner_and_repo_from_source_path(project)
        proj_list_output_file.write(f'{owner}/{repo}\n')
        output_path = exp_utils.RAW_DATA_PATH(
            data_type="user-ids", owner=owner, repo=repo, ext="")
        with open(output_path, "w+", encoding='utf-8') as output_file:
            users = list([user.data for user in users])
            output_file.write(json.dumps(users))

    return proj_list_output_path


if __name__ == "__main__":
    exp_utils.load_paths_for_eco()
    # Sets path for chronological input data
    __input_pr_dataset_names = [entry for entry in safe_get_argv(key="-pd", default="").split(",")
                                if entry != '']
    __input_issue_dataset_names = [entry for entry in safe_get_argv(key='-id', default="").split(",")
                                   if entry != '']
    __ext = safe_get_argv(key='--ext', default="")

    create_project_user_list(__input_pr_dataset_names,
                             __input_issue_dataset_names,
                             __ext)
