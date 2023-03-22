"""
This script retrieves all data necessary to replicate
the results of Dey et al. (2020); i.e., pull request data.

It outputs a number of files:
 - Pull Requests per project from GitHub, GitLab stored as .json files.
   - Note that projects with 0 PRs don't have this file.
 - An error log .csv file (HTTP errors generally mean the data is inaccessible).
 - A file containing the number of PRs per project.
 - A file containing the number of PRs per platform (i.e., GitHub etc.).
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
from python_proj.experiment.filters.gl_gitlab_filters import MergeRequestFilter


input_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/projects_with_repository_fields-1.6.0-2020-01-12.csv"
output_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/{project_name}.json"
error_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/error.csv"
count_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/pr-count.csv"
repo_count_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/repo-count.csv"

# These headers correspond with the "libraries.io/data"
# headers in the "projects_with_repository_fields" file.
headers = ['ID', 'Platform', 'Name', 'Created Timestamp', 'Updated Timestamp', 'Description', 'Keywords', 'Homepage URL', 'Licenses', 'Repository URL', 'Versions Count', 'SourceRank', 'Latest Release Publish Timestamp', 'Latest Release Number', 'Package Manager ID', 'Dependent Projects Count', 'Language', 'Status', 'Last synced Timestamp', 'Dependent Repositories Count', 'Repository ID', 'Repository Host Type', 'Repository Name with Owner', 'Repository Description', 'Repository Fork?', 'Repository Created Timestamp', 'Repository Updated Timestamp', 'Repository Last pushed Timestamp', 'Repository Homepage URL', 'Repository Size', 'Repository Stars Count', 'Repository Language', 'Repository Issues enabled?', 'Repository Wiki enabled?',
           'Repository Pages enabled?', 'Repository Forks Count', 'Repository Mirror URL', 'Repository Open Issues Count', 'Repository Default branch', 'Repository Watchers Count', 'Repository UUID', 'Repository Fork Source Name with Owner', 'Repository License', 'Repository Contributors Count', 'Repository Readme filename', 'Repository Changelog filename', 'Repository Contributing guidelines filename', 'Repository License filename', 'Repository Code of Conduct filename', 'Repository Security Threat Model filename', 'Repository Security Audit filename', 'Repository Status', 'Repository Last Synced Timestamp', 'Repository SourceRank', 'Repository Display Name', 'Repository SCM type', 'Repository Pull requests enabled?', 'Repository Logo URL', 'Repository Keywords']

repo_host_type_index = headers.index("Repository Host Type")
repo_name_index = headers.index("Repository Name with Owner")
is_fork_index = headers.index("Repository Fork?")
# HACK: Somehow the index is misaligned by 1.
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
github_token_1 = getenv("GITHUB_TOKEN_1")
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

    # The number of projects per hosts is kept for bookkeeping.
    host_count = {}

    for entry in csv_reader:
        if not matches_inclusion_criteria(entry):
            continue

        repo_name = entry[repo_name_index]
        repo_host = entry[repo_host_type_index]

        # Updates host count.
        if not repo_host in host_count:
            host_count[repo_host] = 1
        else:
            host_count[repo_host] += 1

        try:
            fetch_prs(repo_name, repo_host)
        except HTTPError as e:
            # If it's an HTTP error it basically
            # means the repo is private / removed.
            error_writer.writerow([repo_name, e.response.status_code, str(e)])
            error_output.flush()
        except Exception as e:
            # All other errors are stored for debuggin.
            error_writer.writerow([repo_name, "", e])
            error_output.flush()

    input_file.close()

    # Writes the repository host counts to a file.
    with open(repo_count_path, "w+", encoding="utf-8") as repo_count_file:
        csv_writer = writer(repo_count_file)
        entries = [[key, value] for key, value in host_count.items()]
        csv_writer.writerows(entries)


def __build_github(repo_name: str):
    owner, repo_name = repo_name.split("/")
    repo: GitHub = GitHub(owner=owner, repository=repo_name,
                          api_token=[github_token_1,
                                     github_token_2, github_token_3],
                          sleep_for_rate=True)
    data_iterator = repo.fetch(
        category=CATEGORY_PULL_REQUEST, to_date=end_date)
    pr_filter = PullFilter(ignore_empty=True)
    return owner, repo_name, data_iterator, pr_filter


def __build_gitlab(repo_name: str):
    repo_split = repo_name.split("/")
    owner = repo_split[0]
    repo_name = repo_split[-1]
    repo: GitLab = GitLab(owner=owner, repository=repo_name,
                          api_token=gitlab_token_1, sleep_for_rate=True)
    data_iterator = repo.fetch(category=CATEGORY_MERGE_REQUEST)
    pr_filter = MergeRequestFilter(ignore_empty=True)
    return owner, repo_name, data_iterator, pr_filter


def fetch_prs(repo_name: str, repo_host: str):
    # Selects the right Perceval backend
    # and corresponding data filter.
    if repo_host.lower() == "github":
        owner, repo_name, data_iterator, pr_filter = __build_github(repo_name)
    elif repo_host.lower() == "gitlab":
        owner, repo_name, data_iterator, pr_filter = __build_gitlab(repo_name)
    # TODO: Add bitbucket support; this isn't natively supported by grimoirelab, though...
    else:
        # TODO implement this if theres a large number of non-GitHub/GitLab repositories.
        raise NotImplementedError(f"Unsupported repository type: {repo_host}.")

    print(f'Starting with: {owner}/{repo_name} at {repo_host}.')

    r_output_path = output_path.format(
        project_name=f'{owner}--{repo_name}')

    if not path.exists((output_dir := path.dirname(r_output_path))):
        makedirs(output_dir)

    try:
        output_file = open(r_output_path, "w+", encoding="utf-8")
        output_file.write("[\n")

        pr_count = 0

        for index, pull_request in enumerate(data_iterator):
            # Adds commas between entries.
            if index > 0:
                output_file.write(",\n")
                pr_count = index

            data = pull_request["data"]
            filtered_pr = pr_filter.filter(data)
            output_file.write(json.dumps(filtered_pr, indent=2))

        count_writer.writerow([f'{owner}/{repo_name}', pr_count])
        count_output.flush()

        if pr_count == 0:
            # Removes empty files.
            output_file.close()
            remove(r_output_path)
        else:
            output_file.write("\n]\n")
            output_file.close()

    except Exception as e:
        # Deletes the output file of failed
        # requests to preserve storage.
        output_file.close()
        remove(r_output_path)
        raise e


def count_projects_that_match_criteria():
    """
    Simply iterates through the libraries.io file
    and counts the number of files that respect
    inclusion criteria.
    """

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
