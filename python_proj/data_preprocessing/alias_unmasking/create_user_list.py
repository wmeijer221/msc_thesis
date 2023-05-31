"""
This script generates a list of all known users using the chronological dataset.
The generated list is used as the input for: https://github.com/bvasiles/ght_unmasking_aliases
"""

from csv import writer
from typing import Generator, Dict, Tuple
import json
from os import path, makedirs

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.util import safe_get


def user_list_generator() -> Generator[Tuple[Dict, str], None, None]:
    for entry in exp_utils.iterate_through_chronological_data():
        owner, repo = exp_utils.get_owner_and_repo_from_source_path(
            entry["__source_path"])
        try:
            yield entry["user_data"], owner, repo
            integrator_key = exp_utils.get_integrator_key(entry)
            if integrator_key in entry:
                yield entry[integrator_key], owner, repo
            if entry["comments"] == 0 or "comments_data" not in entry:
                continue
            for comment in entry["comments_data"]:
                yield comment["user_data"], owner, repo
        except Exception as ex:
            print(json.dumps(entry))
            raise ex


def create_user_list():
    unique_users: dict[str, dict] = {}
    user_to_projects: dict[str, set[str]] = {}
    for (user, owner, repo) in user_list_generator():
        user_id = user["id"]
        # Store user
        if user_id not in unique_users:
            unique_users[user_id] = user
        # Store project.
        if user_id not in user_to_projects:
            user_to_projects[user_id] = set()
        user_to_projects[user_id].add((owner, repo))

    print(f'Identified Aliases: {len(unique_users)}.')

    def __user_to_entry(__user: dict) -> list[str]:
        user_id = safe_get(__user, "id", "")
        login = safe_get(__user, "login", "")
        name = safe_get(__user, "name", "")
        email = safe_get(__user, "email", "")

        projects = user_to_projects[user_id]
        str_projects = [f'{owner}/{repo}' for (owner, repo) in projects]
        projs = ";".join(str_projects)

        return [user_id, login, name, email, projs]

    output_path = exp_utils.RAW_DATA_PATH
    for user_id, projects in user_to_projects.items():
        for (owner, repo) in projects:
            r_output_path = output_path(
                owner=owner, repo=repo, ext="--user-ids")

            dirname = path.dirname(r_output_path)
            if not path.exists(dirname):
                makedirs(dirname)

            # File creation
            with open(r_output_path, "w+") as output_file:
                csv_writer = writer(output_file)
                csv_writer.writerow(["user_id", "login",
                                     "name", "email", "projects"])

            # File filling.
            user_row = __user_to_entry(unique_users[user_id])
            with open(r_output_path, "a+") as output_file:
                csv_writer = writer(output_file)
                csv_writer.writerow(user_row)


if __name__ == "__main__":
    exp_utils.load_paths_for_all_argv()
    create_user_list()
