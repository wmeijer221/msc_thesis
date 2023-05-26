from typing import Generator
from csv import reader
import json
from os import path, makedirs, remove
import requests
import dotenv
from perceval.backends.core.github import GitHub, CATEGORY_ISSUE as GH_CATEGORY_ISSUE

from python_proj.data_retrieval.retrieve_pull_requests import matches_inclusion_criteria

from python_proj.data_retrieval.gl_filters.gl_github_filters import IssueFilter as GHIssueFilter
import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import safe_get_argv
from python_proj.utils.mt_utils import parallelize_tasks

# TODO: Move this argv and path stuff into ``__main__``.
# Loads API keys.
dotenv.load_dotenv()
gh_token_count = safe_get_argv('-a', 3)
all_gh_tokens = exp_utils.get_gh_tokens(gh_token_count)

skip_processed = False

# HACK: Because ``retrieve_pull_requests`` is imported, this line can't be called.
# exp_utils.load_paths_for_eco()
input_path = exp_utils.PROJECTS_WITH_REPO_PATH()
output_path = exp_utils.RAW_DATA_PATH
filter_path = exp_utils.FILTER_PATH


def build_github(repo_name: str, tokens: list):
    owner, repo_name = repo_name.split("/")
    repo: GitHub = GitHub(owner=owner, repository=repo_name,
                          api_token=tokens,
                          sleep_for_rate=True)
    data_iterator = repo.fetch(
        category=GH_CATEGORY_ISSUE, to_date=exp_utils.LIBRARIES_IO_DATASET_END_DATE)
    iss_filter = GHIssueFilter(ignore_empty=True)
    return owner, repo_name, data_iterator, iss_filter


def retrieve_issues_for_entry(task: dict, task_id: int, total_tasks: int, gh_tokens: list[str], worker_index: int):
    entry = task['entry']
    full_repo_name = entry[exp_utils.repo_name_index]
    print(f'Starting with ({task_id}/{total_tasks}) {full_repo_name}.')

    my_gh_tokens = gh_tokens[worker_index]

    # Builds a GrimoireLab iterator.
    match entry[exp_utils.repo_host_type_index].lower():
        case 'github':
            owner, repo_name, iterator, filter = build_github(
                full_repo_name, my_gh_tokens)
        case _:
            print(
                f"Skipped ({task_id}) {full_repo_name} because repository \"{entry[exp_utils.repo_host_type_index]}\" isn't supported.")
            return

    # r_output_path = output_path.format(
    #     project_name=f'{owner}--{repo_name}')

    r_output_path = output_path(
        owner=owner, repo=repo_name, ext="", data_type="issues")

    # Skips already processed projects.
    if skip_processed and path.exists(r_output_path):
        print(f'Skipped ({task_id}) {full_repo_name}.')
        return

    # Makes directory if it doesn't exist yet.
    if not path.exists((output_dir := path.dirname(r_output_path))):
        makedirs(output_dir)

    # Writes issues to file.
    try:
        issue_count = 0
        with open(r_output_path, "w+", encoding='utf-8') as output_file:
            output_file.write("[\n")
            for index, entry in enumerate(iterator):
                if index > 0:
                    output_file.write(",\n")
                filtered_entry = filter.filter(entry["data"])
                output_file.write(json.dumps(filtered_entry, indent=2))
                issue_count += 1
            output_file.write("\n]\n")
    except requests.exceptions.HTTPError:
        print(f'HTTP error for {owner}/{repo_name}.')

    # Deletes empty files.
    if issue_count == 0:
        remove(r_output_path)

    print(f'Finished with ({task_id}) {full_repo_name}.')


def retrieve_issues(worker_count: int, filter_type: str = ""):
    """
    Main method for retrieving issues of interesting projects.
    """

    tasks = list(task_generator(filter_type))
    tokens = [exp_utils.get_my_tokens(all_gh_tokens, index, worker_count)
              for index in range(worker_count)]
    parallelize_tasks(tasks, retrieve_issues_for_entry,
                      worker_count, gh_tokens=tokens)


def task_generator(filter_type: str) -> Generator:
    # Loads libraries.io project file and filtered projectname list.
    input_file = open(input_path, "r")
    input_reader = reader(input_file, quotechar='"')
    filter_file = open(filter_path(filter_type=filter_type))
    included_projects = {entry.strip().lower()
                         for entry in filter_file.readlines()}

    # Submits each valid data entry.
    unique = set()
    job_count = 0
    for entry in input_reader:
        entry_tuple = (entry[exp_utils.repo_name_index],
                       entry[exp_utils.repo_host_type_index])

        # Only adds tasks if they are in the filtered list and have not been processed before.
        if matches_inclusion_criteria(entry) and \
            entry[exp_utils.repo_name_index].lower() in included_projects and \
                entry_tuple not in unique:
            unique.add(entry_tuple)
            job_kwargs = {
                "entry": entry,
                "job_id": job_count,
            }
            job_count += 1
            yield job_kwargs


if __name__ == "__main__":
    worker_count = int(safe_get_argv('-t', default=3))
    filter_type = safe_get_argv("-f", default="")

    retrieve_issues(worker_count, filter_type)
