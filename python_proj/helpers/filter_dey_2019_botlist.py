"""
This script exctracts the bots contained in the botlist published by Dey et al. (2020),
which is publically available at https://zenodo.org/record/3694401.
For any details, see their paper: https://dl.acm.org/doi/10.1145/3379597.3387478.
For this script to work, download the dataset and extract it at the file path used below.
"""

import sys
import csv
from pydantic.dataclasses import dataclass
from dataclasses_json import dataclass_json
import json
from csv import reader
csv.field_size_limit(sys.maxsize)

from python_proj.utils.exp_utils import BASE_PATH

@dataclass_json
@dataclass(frozen=True)
class Author:
    name: str
    email: str


input_path = BASE_PATH + "bot_data/known_bot_dataset"
with open(input_path, "r") as input_file:
    bots = set()
    input_reader = reader(input_file, delimiter=';')

    for entry in input_reader:
        author_id = entry[0]

        segments = author_id.split("<")
        name = "<".join(segments[:-1]).strip()
        email = segments[-1][:-1]
        auth = Author(name, email)

        if auth not in bots:
            bots.add(auth)

output_path = BASE_PATH + "bot_data/dey_2020_bots.json"
with open(output_path, "w+") as output_file:
    data_dict = Author.schema().dump(bots, many=True)
    output_file.write(json.dumps(data_dict, indent=2))
