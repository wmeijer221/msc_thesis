from typing import Generator
from csv import reader
import multiprocessing
import json
from os import path, makedirs, remove
import requests
from perceval.backends.core.github import GitHub, CATEGORY_ISSUE as GH_CATEGORY_ISSUE
from perceval.backends.core.gitlab import GitLab, CATEGORY_ISSUE as GL_CATEGORY_ISSUE

import python_proj.data_retrieval.retrieve_pull_requests as rpr

from python_proj.data_retrieval.gl_filters.gl_github_filters import IssueFilter as GHIssueFilter
from python_proj.data_retrieval.gl_filters.gl_gitlab_filters import IssueFilter as GLIssueFilter
from python_proj.utils.arg_utils import safe_get_argv
from python_proj.utils.mt_utils import parallelize_tasks

skip_processed = False

output_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/issues/{project_name}.json"


def build_github(repo_name: str, tokens: list):
    owner, repo_name = repo_name.split("/")
    repo: GitHub = GitHub(owner=owner, repository=repo_name,
                          api_token=tokens,
                          sleep_for_rate=True)
    data_iterator = repo.fetch(
        category=GH_CATEGORY_ISSUE, to_date=rpr.end_date)
    iss_filter = GHIssueFilter(ignore_empty=True)
    return owner, repo_name, data_iterator, iss_filter


def retrieve_issues_for_entry(entry: dict, job_id: int, gh_tokens: list[str], worker_index: int, **kwargs):
    full_repo_name = entry[rpr.repo_name_index]
    print(f'Starting with ({job_id}) {full_repo_name}.')

    my_gh_tokens = gh_tokens[worker_index]

    # Builds a GrimoireLab iterator.
    match entry[rpr.repo_host_type_index].lower():
        case 'github':
            owner, repo_name, iterator, filter = build_github(
                full_repo_name, my_gh_tokens)
        case _:
            print(
                f"Skipped ({job_id}) {full_repo_name} because repository \"{entry[rpr.repo_host_type_index]}\" isn't supported.")
            return

    r_output_path = output_path.format(
        project_name=f'{owner}--{repo_name}')

    # Skips already processed projects.
    if skip_processed and path.exists(r_output_path):
        print(f'Skipped ({job_id}) {full_repo_name}.')
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

    print(f'Finished with ({job_id}) {full_repo_name}.')


def retrieve_issues(worker_count: int, filter_type: str = ""):
    """
    Main method for retrieving issues of interesting projects.
    """

    tasks = task_generator(filter_type)
    tokens = [rpr.get_my_tokens(rpr.all_gh_tokens, index)
              for index in range(worker_count)]
    parallelize_tasks(tasks, retrieve_issues_for_entry,
                      worker_count, gh_tokens=tokens)


def task_generator(filter_type: str) -> Generator:
    # Loads libraries.io project file and filtered projectname list.
    input_file = open(rpr.input_path, "r")
    input_reader = reader(input_file, quotechar='"')
    filter_file = open(rpr.filter_path.format(filter_type=filter_type))
    included_projects = {entry.strip().lower()
                         for entry in filter_file.readlines()}

    # Submits each valid data entry.
    unique = set()
    job_count = 0
    for entry in input_reader:
        entry_tuple = (entry[rpr.repo_name_index],
                       entry[rpr.repo_host_type_index])

        # Only adds tasks if they are in the filtered list and have not been processed before.
        if rpr.matches_inclusion_criteria(entry) and \
            entry[rpr.repo_name_index].lower() in included_projects and \
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
