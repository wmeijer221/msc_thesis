"""
Counts the number of reviewers.
"""

import itertools

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import safe_get_argv

exp_utils.load_paths_for_eco()
# Sets path for chronological input data
input_pr_dataset_names = [entry for entry in safe_get_argv(key="-pd", default="").split(",")
                          if entry != '']
input_issue_dataset_names = [entry for entry in safe_get_argv(key='-id', default="").split(",")
                             if entry != '']

data_set_names = list(itertools.chain(
    input_pr_dataset_names, input_issue_dataset_names))
data_sources = ["pull-requests"] * len(input_pr_dataset_names)
data_sources.extend(["issues"] * len(input_issue_dataset_names))

generator = exp_utils.iterate_through_multiple_chronological_datasets(
    data_set_names, data_sources=data_sources)

reviewer_count = 0
assignee_count = 0
total = 0
for entry in generator:
    rev_key = 'requested_reviewers_data'
    if rev_key in entry and len(entry[rev_key]) > 0:
        reviewer_count += 1
    assign_key = 'assignees'
    if assign_key in entry and len(entry[assign_key]) > 0:
        assignee_count += 1
    total += 1

rev_perc = 100 * reviewer_count / total
assign_perc = 100 * assignee_count / total

print(f'Reviewers: {reviewer_count}/{total} ({rev_perc:.03f}%)')
print(f'Assignees: {assignee_count}/{total} ({assign_perc:.03f}%)')
