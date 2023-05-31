"""
This script generates a list of all known users using the chronological dataset.
The generated list is used as the input for: https://github.com/bvasiles/ght_unmasking_aliases
"""

from csv import writer
from typing import Generator, Dict, Tuple
import json
from os import path

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.util import safe_get


def user_list_generator() -> Generator[Tuple[Dict, str], None, None]:
    for entry in exp_utils.iterate_through_chronological_data():
        owner, repo = exp_utils.get_owner_and_repo_from_source_path(
            entry["__source_path"])
        project_name = f'{owner}/{repo}'
        try:
            yield entry["user_data"], project_name
            integrator_key = exp_utils.get_integrator_key(entry)
            # TODO: This can be removed once the dataset is complete.
            if integrator_key not in entry:
                pass
                # print("MISSING INTEGRATOR KEY!!!")
            else:
                yield entry[integrator_key], project_name
            if entry["comments"] == 0 or "comments_data" not in entry:
                continue
            for comment in entry["comments_data"]:
                yield comment["user_data"], project_name
        except:
            print(json.dumps(entry))
            raise


def create_user_list():
    unique_users: dict[str, dict] = {}
    user_to_projects: dict[str, set[str]] = {}
    for (user, project) in user_list_generator():
        user_id = user["id"]
        # Store user.
        if user_id not in unique_users:
            unique_users[user_id] = user
        # Store project.
        if user_id not in user_to_projects:
            user_to_projects[user_id] = set()
        user_to_projects[user_id].add(project)

    def __user_to_entry(user: dict) -> list[str]:
        user_id = safe_get(user, "id", "")
        login = safe_get(user, "login", "")
        name = safe_get(user, "name", "")
        email = safe_get(user, "email", "")
        projects = ";".join(user_to_projects[user_id])
        return [user_id, login, name, email, projects]

    output_path = exp_utils.BASE_PATH + "/extract/user_ids/{project_name}.csv"
    for user_id, projects in user_to_projects.items():
        for project in projects:
            r_output_path = output_path.format(
                project_name=project.replace("/", '--'))

            # File creation
            if not path.exists(r_output_path):
                with open(r_output_path, "w+") as output_file:
                    csv_writer = writer(output_file)
                    csv_writer.writerow(["user_id", "login",
                                         "name", "email", "projects"])

            # File filling.
            with open(r_output_path, "a+") as output_file:
                csv_writer = writer(output_file)
                user = __user_to_entry(user)
                csv_writer.writerow(user)


if __name__ == "__main__":
    exp_utils.load_paths_for_all_argv()
    create_user_list()
