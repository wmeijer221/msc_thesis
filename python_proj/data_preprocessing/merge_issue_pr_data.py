"""
This script merges the data from ``retrieve_pull_requests.py`` 
and ``retrieve_issues.py``, such that all pull request data is extended with its respective issue data. Consequently, all issue entries that are in reality a pull request are removed from the issue dataset.

(In GitHub, functionally, pull requests inherit issues, adding code-related stuff to it. The pull request API does not return the issue data, though (commments etc.). To get the full picture, both datasources therefore need to be merged.)
"""

import json
from functools import partial
from os import path, remove

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import get_argv_flag

base_file_name = '{owner}--{repo_name}'


def do_the_merge(filter_type: str, delete_old: bool = False, write_new: bool = False):
    filter_path: partial[str] = exp_utils.FILTER_PATH(filter_type=filter_type)
    print(f'Using filter: "{filter_path}".')
    filter_file = open(filter_path, "r")

    missing_issue_count = 0
    missing_issue_projects = []
    failed_decode_projects = []

    for entry in filter_file:
        name_split = entry.strip().split("/")
        (owner, repo) = (name_split[0], name_split[1])
        project_name = base_file_name.format(owner=owner, repo_name=repo)
        pull_requests_path = exp_utils.RAW_DATA_PATH(data_type="pull-requests",
                                                     owner=owner,
                                                     repo=repo,
                                                     ext="")
        issue_path = exp_utils.RAW_DATA_PATH(data_type="issues",
                                             owner=owner,
                                             repo=repo,
                                             ext="")

        if not path.exists(pull_requests_path):
            continue

        if not path.exists(issue_path):
            print(f"Can't find issues for {project_name}")
            missing_issue_projects.append(project_name)
            continue

        pull_request_file = open(pull_requests_path, "r")
        issue_file = open(issue_path, "r")

        try:
            prs = json.loads(pull_request_file.read())
            issues = json.loads(issue_file.read())
        except json.JSONDecodeError:
            print(f"Decode error for {project_name}.")
            failed_decode_projects.append(project_name)
            continue

        issues_mapping = {issue["number"]: issue for issue in issues}

        new_prs = []

        # Merges PR with corresponding issue data.
        for pr in prs:
            try:
                pr_number = pr["number"]
            except KeyError:
                # This happens when the PRs are retrieved from GitLab.
                print(f"PR has no number in {project_name}.")
                break

            if pr_number not in issues_mapping:
                print(f'Missing issue in {project_name} for PR #{pr_number}.')
                missing_issue_count += 1
                continue

            issue = issues_mapping[pr_number]
            new_pr = {}
            for key, value in issue.items():
                new_pr[key] = value
            for key, value in pr.items():
                new_pr[key] = value

            new_prs.append(new_pr)

        if len(new_prs) > 0:
            # Writes enriched PRs.
            pr_output_path = exp_utils.RAW_DATA_PATH(data_type="pull-requests",
                                                     owner=owner,
                                                     repo=repo,
                                                     ext="--with-issue-data")
            print(pr_output_path)
            with open(pr_output_path, "w+") as output_file:
                if write_new:
                    output_file.write(json.dumps(new_prs, indent=2))

            # Filters out issues that are also PRs.
            for pr in prs:
                pr_number = pr["number"]
                if pr_number not in issues_mapping:
                    continue
                del issues_mapping[pr_number]

            # Writes filtered issues.
            issue_output_path = exp_utils.RAW_DATA_PATH(data_type="issues",
                                                        owner=owner,
                                                        repo=repo,
                                                        ext="--no-prs")
            print(issue_output_path)
            with open(issue_output_path, "w+") as issue_output_file:
                data = list(issues_mapping.values())
                issue_output_file.write(json.dumps(data, indent=2))

        issue_file.close()
        pull_request_file.close()

        if delete_old:
            remove(pull_requests_path)
            remove(issue_path)

    filter_file.close()

    print(f'Skipped {missing_issue_count} issues.')
    print(
        f'Skipped {len(missing_issue_projects)} projects: {missing_issue_projects}.')


if __name__ == "__main__":
    exp_utils.load_paths_for_eco()
    filter_file_name = exp_utils.get_file_name()
    write_new = get_argv_flag("-w")
    delete_old = get_argv_flag("-d")
    print(f'{write_new=}, {delete_old=}')
    do_the_merge(filter_file_name, delete_old, write_new)
