"""
This script merges the data from ``retrieve_pull_requests.py`` 
and ``retrieve_issues.py``, such that all pull request data is extended with its respective issue data. Consequently, all issue entries that are in reality a pull request are removed from the issue dataset.

(In GitHub, functionally, pull requests inherit issues, adding code-related stuff to it. The pull request API does not return the issue data, though (commments etc.). To get the full picture, both datasources therefore need to be merged.)
"""

import json
from os import path, remove
from sys import argv

from python_proj.experiment.util import safe_index
import python_proj.experiment.replication_study.retrieve_pull_requests as rpr
import python_proj.experiment.retrieve_issues as ri


eco = "npm"

# If you don't use -d and do use -w, it's a dry run.
# Deletes the original files that data was extracted from.
delete_old = safe_index(argv, "-d") >= 0
# Writes merged data to a file.
write_new = safe_index(argv, "-w") >= 0

pull_request_path = rpr.filter_path.format(filter_type="")
pr_output_path = "./data/libraries/{eco}-libraries-1.6.0-2020-01-12/pull-requests/{project_name}--with-issue-data.json"
issue_output_path = "./data/libraries/{eco}-libraries-1.6.0-2020-01-12/issues/{project_name}--no-prs.json"
base_file_name = '{owner}--{repo_name}'


def do_the_merge():
    pr_filter_file = open(pull_request_path, "r")

    for entry in pr_filter_file:
        print(f'Starting with {entry}.')
        name_split = entry.strip().split("/")
        (owner, repo) = (name_split[0], name_split[1])
        project_name = base_file_name.format(owner=owner, repo_name=repo)
        pr_path = rpr.output_path.format(project_name=project_name)
        issue_path = ri.output_path.format(project_name=project_name)

        if not path.exists(pr_path):
            continue

        pr_file = open(pr_path, "r")
        issue_file = open(issue_path, "r")

        prs = json.loads(pr_file.read())
        issues = json.loads(issue_file.read())

        issues_mapping = {issue["number"]: issue for issue in issues}

        new_prs = []

        # Merges PR with corresponding issue data.
        for pr in prs:
            issue = issues_mapping[pr["number"]]
            new_pr = {}
            for key, value in issue.items():
                new_pr[key] = value
            for key, value in pr.items():
                new_pr[key] = value

            new_prs.append(new_pr)

        # Writes enriched PRs.
        real_output_path = pr_output_path.format(
            project_name=project_name, eco=eco)
        with open(real_output_path, "w+") as output_file:
            if write_new:
                output_file.write(json.dumps(new_prs, indent=2))

        # Filters out issues that are also PRs.
        for pr in prs:
            del issues_mapping[pr["number"]]

        # Writes filtered issues.
        real_issue_output_path = issue_output_path.format(
            project_name=project_name, eco=eco)
        with open(real_issue_output_path, "w+") as issue_output_file:
            data = list(issues_mapping.values())
            issue_output_file.write(json.dumps(data, indent=2))

        issue_file.close()
        pr_file.close()

        if delete_old:
            remove(issue_path)
            remove(pr_path)

    pr_filter_file.close()


if __name__ == "__main__":
    do_the_merge()
