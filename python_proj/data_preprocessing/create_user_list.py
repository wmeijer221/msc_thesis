"""
This script generates a list of all known users using the chronological dataset.
The generated list is used as the input for: https://github.com/bvasiles/ght_unmasking_aliases
"""

from csv import writer
from typing import Generator
import json

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.util import safe_get


def user_list_generator() -> Generator[dict, None, None]:
    for entry in exp_utils.iterate_through_chronological_data():
        try:
            yield entry["user_data"]
            integrator_key = exp_utils.get_integrator_key(entry)
            # TODO: This can be removed once the dataset is complete.
            if integrator_key not in entry:
                pass
                # print("MISSING INTEGRATOR KEY!!!")
            else:
                yield entry[integrator_key]
            if entry["comments"] == 0 or "comments_data" not in entry:
                continue
            for comment in entry["comments_data"]:
                yield comment["user_data"]
        except:
            print(json.dumps(entry))
            raise


def create_user_list():
    unique_users = {}
    for entry in user_list_generator():
        if entry["id"] not in unique_users:
            unique_users[entry["id"]] = entry
    with open("./data/libraries/npm-libraries-1.6.0-2020-01-12/extract/user_ids.csv", "w+")as output_file:
        csv_writer = writer(output_file)
        csv_writer.writerow(["login", "name", "email"])
        for user in unique_users.values():
            login = safe_get(user, "login", "")
            name = safe_get(user, "name", "")
            email = safe_get(user, "email", "")
            csv_writer.writerow([login, name, email])


if __name__ == "__main__":
    exp_utils.load_paths_for_all_argv()
    create_user_list()
