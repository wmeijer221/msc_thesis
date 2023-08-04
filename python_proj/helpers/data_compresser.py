"""
Utility script to minimize the storage required to store the research raw data.
"""

import os
from python_proj.utils.arg_utils import get_argv
import json


def shrink_json_in_directory():
    directory = get_argv('--dir')
    print(f'Shrinking JSON files in "{directory}"')
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        print(file_path)
        if not os.path.isfile(file_path):
            continue
        try:
            with open(file_path, "r", encoding='utf-8') as file:
                j_data = json.loads(file.read())
        except json.JSONDecodeError:
            print(f'File "{file_path}" is no JSON.')
            continue

        os.remove(file_path)
        with open(file_path, "w+", encoding='utf-8') as file:
            file.write(json.dumps(j_data, separators=(',', ':')))


if __name__ == "__main__":
    match get_argv('-m'):
        case "shrink_json":
            shrink_json_in_directory()
        case _:
            raise ValueError("invalid mode")
