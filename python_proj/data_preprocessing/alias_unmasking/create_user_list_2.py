"""
Input: multiple chronological datasets, both PR ones and issue ones.
Ouptut: json files per project containing all of the users of said project.
"""

from functools import partial
import json
from typing import Generator, Dict, Tuple
from os import path, makedirs

import python_proj.utils.exp_utils as exp_utils
import python_proj.utils.arg_utils as arg_utils


def user_list_generator_pr(entry: dict) -> Generator[Tuple[Dict, str, str], None, None]:
    owner, repo = exp_utils.get_owner_and_repo_from_source_path(
        entry["__source_path"])
    try:
        yield entry["user_data"], owner, repo
        integrator_key = exp_utils.get_integrator_key(entry)
        if integrator_key in entry:
            yield entry[integrator_key], owner, repo
        if entry["comments"] == 0 or "comments_data" not in entry:
            return
        for comment in entry["comments_data"]:
            yield comment["user_data"], owner, repo
    except Exception as ex:
        print(json.dumps(entry))
        raise ex


def user_list_generator_issue(entry: dict) -> Generator[Tuple[Dict, str, str], None, None]:
    owner, repo = exp_utils.get_owner_and_repo_from_source_path(
        entry["__source_path"])
    yield entry["user_data"], owner, repo
    if entry["comments"] > 0 and "comments_data" in entry:
        for comment in entry["comments_data"]:
            yield comment["user_data"], owner, repo


def user_list_generator_chronological_datasets(input_pr_names: list[str], input_issue_names: list[str]) -> Generator[Tuple[Dict, str, str], None, None]:
    dataset_sources = ["pull-requests"] * len(input_pr_names)
    dataset_sources.extend(["issues"] * len(input_issue_names))
    all_data_sources = [*input_pr_names, *input_issue_names]
    dataset_iterator = exp_utils.iterate_through_multiple_chronological_datasets(
        all_data_sources, dataset_sources, dataset_sources)
    for entry in dataset_iterator:
        entry_user_iterator = None
        match entry["__data_type"]:
            case "pull-requests":
                entry_user_iterator = user_list_generator_pr(entry)
            case "issues":
                entry_user_iterator = user_list_generator_issue(entry)
            case _:
                raise ValueError("Invalid data type")
        for user in entry_user_iterator:
            yield user

def create_user_list(input_pr_names: list[str], input_issue_names: list[str], output_path: partial[str]):
    # Get users per project.
    user_iterator = user_list_generator_chronological_datasets(
        input_pr_names, input_issue_names)
    users_per_project: dict[Tuple[str, str], dict[dict]] = {}
    for (user, owner, repo) in user_iterator:
        # Some users don't have an ID.
        if 'id' not in user:
            continue
        key = (owner, repo)
        if key not in users_per_project:
            users_per_project[key] = {}
        users_per_project[user['id']] = user

    # Write it all to files.
    for (owner, repo), users in users_per_project.items():
        r_output_path = output_path(owner=owner, repo=repo, ext="")
        # Dir creation.
        dirname = path.dirname(r_output_path)
        if not path.exists(dirname):
            makedirs(dirname)
        # File creation
        with open(r_output_path, 'w+') as ouptut_file:
            ouptut_file.write(json.dumps(list(users.values())))


if __name__ == "__main__":
    exp_utils.load_paths_for_eco()
    output_path = partial(exp_utils.RAW_DATA_PATH, data_type="user-ids")
    input_pr_data = [entry for entry in
                     arg_utils.safe_get_argv(key="-pd", default="").split(",")
                     if entry != ""]
    input_issue_data = [entry for entry in
                        arg_utils.safe_get_argv(
                            key="-d", default="").split(",")
                        if entry != ""]

    create_user_list(input_pr_data, input_issue_data, output_path)
