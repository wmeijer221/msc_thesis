"""
Utility script to minimize the storage required to store the research raw data.
"""

import os
from python_proj.utils.arg_utils import get_argv
import json


def shrink_json_in_directory():
    directory = get_argv('--dir')
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if not os.path.isfile(file_path):
            continue

        with open(file_path, "rw", encoding='utf-8') as file:
            j_data = json.loads(file.read())
            file.write(json.dumps(j_data, separators=''))






if __name__ == "__main__":
    
    jdata = {'key_a': "asdff,", "key_b": 134}
    print(json.dumps(jdata, separators=''))

