"""
micro utility to count the projects per platform in the libraries.io dataset.

ouput:
{
    "": 492802,
    "GitHub": 775461,
    "Bitbucket": 3192,
    "GitLab": 5766
}
total=1277221
"""


import csv
import json

from python_proj.utils.util import SafeDict

# input_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/projects_with_repository_fields-1.6.0-2020-01-12.csv"
input_path = "./data/libraries/libraries-1.6.0-2020-01-12/projects_with_repository_fields-1.6.0-2020-01-12.csv"
with open(input_path, "r", encoding='utf-8') as input_file:
    reader = csv.reader(input_file)
    projects_per_platform = SafeDict(default_value=0)
    platform_idx = 21
    for entry in reader:
        if entry[1].lower() != 'npm':
            continue
        platform = entry[platform_idx]
        projects_per_platform[platform] += 1
    total = sum([v for v in projects_per_platform.values()])
    print(json.dumps(projects_per_platform, indent=4))
    print(f'{total=}')
