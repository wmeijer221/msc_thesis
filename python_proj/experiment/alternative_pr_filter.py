"""
Applies stricter pull request count requirements on the projects.
"""

import json

input_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/sorted_filtered.json"
input_file = open(input_path, "r")

pr_counts = {}

for line in input_file:
    entry = json.loads(line)
    src = entry["__source_path"]
    if src not in pr_counts:
        pr_counts[src] = 0
    pr_counts[src] += 1


tested_thresholds = [5, 15, 30]
entries_per_threshold = {t: (0, 0) for t in tested_thresholds}

for key, entry in pr_counts.items():
    for threshold in tested_thresholds:
        if entry >= threshold:
            old_count = entries_per_threshold[threshold]
            new_count = (old_count[0] + 1, old_count[1] + entry)
            entries_per_threshold[threshold] = new_count


print(entries_per_threshold)
