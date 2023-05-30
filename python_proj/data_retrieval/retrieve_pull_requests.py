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

from csv import reader
from datetime import datetime
import dotenv
import json
from os import path, makedirs, remove
from perceval.backends.core.github import GitHub, CATEGORY_PULL_REQUEST
import traceback

from python_proj.data_retrieval.gl_filters.gl_github_filters import PullFilter
from python_proj.utils.arg_utils import safe_get_argv
import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.mt_utils import parallelize_tasks

# Loads relevant paths.
# TODO: load these paths somewhere else for prevent sideeffects.
exp_utils.load_paths_for_eco()
exp_utils.load_paths_for_data_path()
input_path = exp_utils.PROJECTS_WITH_REPO_PATH()
output_path = exp_utils.RAW_DATA_PATH
filter_path = exp_utils.FILTER_PATH

# These headers correspond with the "libraries.io/data"
# headers in the "projects_with_repository_fields" file.
headers = exp_utils.PROJECTS_WITH_REPOSITORY_FIELDS_HEADERS

# Finds indices of relevant fields.
repo_host_type_index = headers.index("Repository Host Type")
repo_name_index = headers.index("Repository Name with Owner")
is_fork_index = headers.index("Repository Fork?")
# HACK: Somehow the index is misaligned by 1.
prs_enabled_index = headers.index("Repository Pull requests enabled?") + 1

end_date = exp_utils.LIBRARIES_IO_DATASET_END_DATE

# Loads API keys.
dotenv.load_dotenv()
gh_token_count = safe_get_argv('-a', 3)
all_gh_tokens = exp_utils.get_gh_tokens(gh_token_count)

# General settings
job_count = 1
skip_processed = False
included_projects = None
processed_projects = set()


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
    with open(input_path, 'r', encoding="utf-8") as input_file:
        csv_reader = reader(input_file, quotechar='"')
        tasks = [list(entry) for entry in csv_reader]
        gh_tokens = [exp_utils.get_my_tokens(all_gh_tokens, index, job_count)
                     for index in range(job_count)]
        parallelize_tasks(tasks, retrieve_prs_for_entry,
                          job_count, gh_tokens=gh_tokens)


def retrieve_prs_for_entry(task: list, gh_tokens: list[str], worker_index: int,
                           task_id: int, total_tasks: int):
    if not matches_inclusion_criteria(task):
        return

    repo_name = task[repo_name_index]
    repo_host = task[repo_host_type_index]

    # Skips project if a filter list is used
    # and the repository is not in it.
    if not included_projects is None and not repo_name in included_projects:
        print(f'Skipping filtered project: {repo_name}.')
        return

    # To prevent the same repo from being processed multiple times.
    unique_entry = (repo_name, repo_host)
    if unique_entry in processed_projects:
        print(f'Skipping duplicate entry: {unique_entry}.')
        return
    processed_projects.add(unique_entry)

    print(
        f'Worker-{worker_index}: ({task_id}/{total_tasks}) Starting with {repo_name} at {repo_host}.')
    my_gh_tokens = gh_tokens[worker_index]
    try:
        fetch_prs(repo_name, repo_host, my_gh_tokens)
    except Exception as e:
        print(
            f'Worker-{worker_index}: Failed to process {repo_name} at {repo_host} with error: {e}')
        traceback.print_exception(e)

    print(f'Worker-{worker_index}: Done with {repo_name} at {repo_host}.')


def __build_github(repo_name: str, tokens: list):
    owner, repo_name = repo_name.split("/")
    repo: GitHub = GitHub(owner=owner, repository=repo_name,
                          api_token=tokens,
                          sleep_for_rate=True)
    data_iterator = repo.fetch(
        category=CATEGORY_PULL_REQUEST, to_date=end_date)
    pr_filter = PullFilter(ignore_empty=True)
    return owner, repo_name, data_iterator, pr_filter


def fetch_prs(repo_name: str, repo_host: str, gh_tokens: list):
    # Selects the right Perceval backend and corresponding data filter.
    if repo_host.lower() == "github":
        owner, repo_name, data_iterator, pr_filter = __build_github(
            repo_name, gh_tokens)
    else:
        # TODO implement this if theres a large number of non-GitHub/GitLab repositories.
        raise NotImplementedError(f"Unsupported repository type: {repo_host}.")

    r_output_path = output_path(owner=owner, repo=repo_name, ext="")

    if skip_processed and path.exists(r_output_path):
        print(
            f"Skipping already processed repo: {owner}/{repo_name} at {repo_host}.")
        return

    if not path.exists((output_dir := path.dirname(r_output_path))):
        makedirs(output_dir)

    try:
        # HACK: Somehow writing to a file from multiple processes works without a lock.
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


def set_filter(f_type: str):
    global included_projects

    r_filter_path = filter_path(filter_type=f'_{f_type}')
    with open(r_filter_path, "r", encoding="utf-8") as filter_file:
        included_projects = set([entry.strip()
                                for entry in filter_file.readlines()])


if __name__ == "__main__":
    start = datetime.now()

    # TODO: this key is incompatible with exp_utils ``file_name``.
    if not (f_type := safe_get_argv("-f")) is None:
        set_filter(f_type.lower())
        print(f"Using filter {f_type}")

    job_count = safe_get_argv(key="-t", default=1, data_type=int)
    mode = safe_get_argv(key="-m", default="s").lower()
    print(f'Starting in mode "{mode}".')

    match mode:
        case "r":
            retrieve_pull_requests()
        case "s":
            skip_processed = True
            retrieve_pull_requests()
        case "c":
            count_projects_that_match_criteria()
        case _:
            raise ValueError(f"Invalid mode \"{mode}\".")

    delta_time = datetime.now() - start
    print(f'{delta_time=}')
