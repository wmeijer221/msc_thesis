"""
This script retrieves all data necessary to replicate
the results of Dey et al. (2020); i.e., pull request data.
"""

import json
from csv import reader, writer
from datetime import datetime
import dotenv
from os import getenv, path, makedirs, remove
from perceval.backends.core.github import GitHub, CATEGORY_PULL_REQUEST
from perceval.backends.core.gitlab import GitLab, CATEGORY_MERGE_REQUEST
from requests.exceptions import HTTPError

from python_proj.experiment.filters.gl_github_filters import PullFilter


input_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/projects_with_repository_fields-1.6.0-2020-01-12.csv"
output_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/{project_name}.json"
error_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/error.csv"
count_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/pr-count.csv"

headers = ['ID', 'Platform', 'Name', 'Created Timestamp', 'Updated Timestamp', 'Description', 'Keywords', 'Homepage URL', 'Licenses', 'Repository URL', 'Versions Count', 'SourceRank', 'Latest Release Publish Timestamp', 'Latest Release Number', 'Package Manager ID', 'Dependent Projects Count', 'Language', 'Status', 'Last synced Timestamp', 'Dependent Repositories Count', 'Repository ID', 'Repository Host Type', 'Repository Name with Owner', 'Repository Description', 'Repository Fork?', 'Repository Created Timestamp', 'Repository Updated Timestamp', 'Repository Last pushed Timestamp', 'Repository Homepage URL', 'Repository Size', 'Repository Stars Count', 'Repository Language', 'Repository Issues enabled?', 'Repository Wiki enabled?',
           'Repository Pages enabled?', 'Repository Forks Count', 'Repository Mirror URL', 'Repository Open Issues Count', 'Repository Default branch', 'Repository Watchers Count', 'Repository UUID', 'Repository Fork Source Name with Owner', 'Repository License', 'Repository Contributors Count', 'Repository Readme filename', 'Repository Changelog filename', 'Repository Contributing guidelines filename', 'Repository License filename', 'Repository Code of Conduct filename', 'Repository Security Threat Model filename', 'Repository Security Audit filename', 'Repository Status', 'Repository Last Synced Timestamp', 'Repository SourceRank', 'Repository Display Name', 'Repository SCM type', 'Repository Pull requests enabled?', 'Repository Logo URL', 'Repository Keywords']

repo_host_type_index = headers.index("Repository Host Type")
repo_name_index = headers.index("Repository Name with Owner")
is_fork_index = headers.index("Repository Fork?")
prs_enabled_index = headers.index("Repository Pull requests enabled?") + 1

end_date = datetime(year=2020, month=1, day=12)

# To log retrieval errors without stopping the program.
if path.exists(error_path):
    remove(error_path)
error_output = open(error_path, "a+", encoding="utf-8", newline="\n")
error_writer = writer(error_output, quotechar='"')
error_writer.writerow(["project", "http status code", "message"])
error_output.flush()

# To log the number of PRs a repository has.
if path.exists(count_path):
    remove(count_path)
count_output = open(count_path, "a+", encoding="utf-8", newline="\n")
count_writer = writer(count_output, quotechar='"')
count_writer.writerow(["project", "pr count"])
count_output.flush()

dotenv.load_dotenv()
github_token = getenv("GITHUB_TOKEN")
github_token_2 = getenv("GITHUB_TOKEN_2")
github_token_3 = getenv("GITHUB_TOKEN_3")

gitlab_token_1 = getenv("GITLAB_TOKEN_1")


def matches_inclusion_criteria(entry):
    # TODO filter on is_fork (ignore forks), pull_request_enabled (requirement), repository_pushed (last month?), repo_contrib_count (min 2), repo_status (active), proj_status (active). Maybe popularity metrics (stars, or dependent project count)
    # It must have a repository entry.
    if entry[repo_name_index] == '':
        return False
    # It can't be a fork.
    if entry[is_fork_index] == 'true':
        return False
    # Must have PRs enabled.
    # THIS DOESN'T WORK FOR GITHUB PROJECTS.
    # print(entry[prs_enabled_index])
    # if entry[prs_enabled_index] != 't':
    #     return False
    return True


def retrieve_pull_requests():
    input_file = open(input_path, 'r', encoding="utf-8")
    csv_reader = reader(input_file, quotechar='"')

    for entry in csv_reader:
        if not matches_inclusion_criteria(entry):
            continue
        repo_name = entry[repo_name_index]
        repo_host = entry[repo_host_type_index]
        try:
            fetch_prs(repo_name, repo_host)
        except HTTPError as e:
            error_writer.writerow([repo_name, e.response.status_code, str(e)])
            error_output.flush()
        # except Exception as e:
        #     print(e)
        #     error_writer.writerow([repo_name, "", e])
        #     error_output.flush()

    input_file.close()


def fetch_prs(repo_name: str, repo_host: str):
    # try:
    # Attempts to retrieve all PRs in the repo,
    # and filters.
    if repo_host == "GitLab":
        name_split = repo_name.split("/")
        owner = name_split[0]
        repo_name = name_split[-1]
        print(f'{owner=}, {repo_name=}')
        repo: GitLab = GitLab(owner=owner, repository=repo_name,
                              api_token=gitlab_token_1, sleep_for_rate=True)
        # TODO: TO DATE IS NOT CONSIDERED IN THE GITLAB BACKEND.
        data_iterator = repo.fetch(
            category=CATEGORY_MERGE_REQUEST)
    elif repo_host == "GitHub":
        owner, repo_name = repo_name.split("/")
        repo: GitHub = GitHub(owner=owner, repository=repo_name,
                              api_token=[github_token, github_token_2, github_token_3], sleep_for_rate=True)
        data_iterator = repo.fetch(
            category=CATEGORY_PULL_REQUEST, to_date=end_date)
        pr_filter = PullFilter(ignore_empty=True)
        return
    else:
        print(f'Unsupported repository type: {repo_host}')
        return

    r_output_path = output_path.format(
        project_name=f'{owner}--{repo_name}')

    if not path.exists((output_dir := path.dirname(r_output_path))):
        makedirs(output_dir)

    output_file = open(r_output_path, "w+", encoding="utf-8")
    output_file.write("[\n")

    pr_count = 0

    for index, pull_request in enumerate(data_iterator):
        # Adds commas between entries.
        if index > 0:
            output_file.write(",\n")
            pr_count = index

        data = pull_request["data"]
        print(json.dumps(data, indent=2))
        filtered_pr = pr_filter.filter(data)
        output_file.write(json.dumps(filtered_pr, indent=1))

    # TODO: remove files with zero PRs.
    count_writer.writerow([f'{owner}/{repo_name}', pr_count])
    count_output.flush()

    output_file.write("\n]\n")
    output_file.close()
    # except Exception as e:
    #     # Deletes the output file to preserve storage.
    #     output_file.close()
    #     remove(r_output_path)
    #     raise e


def count_projects_that_match_criteria():
    input_file = open(input_path, 'r', encoding="utf-8")
    csv_reader = reader(input_file, quotechar='"')
    count_included = 0
    count_all = 0
    for entry in csv_reader:
        count_all += 1
        if matches_inclusion_criteria(entry):
            count_included += 1
    print(f'{count_included=}, {count_all=}')


if __name__ == "__main__":
    retrieve_pull_requests()
    # count_projects_that_match_criteria()
