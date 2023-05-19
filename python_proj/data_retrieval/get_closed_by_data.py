"""
Retrieves the ``closed_by`` fields for pull requests that have been closed but not merged.
This script is only here because I forgot to include the ``closed_by`` field in the ``IssueFilter``.
If you re-run the experiment in its entirety, you don't need this script.
"""

from dataclasses import dataclass
import dotenv
import json
from os import getenv
import requests
import time

from python_proj.data_retrieval.gl_filters.gl_github_filters import UserFilter
from python_proj.utils.arg_utils import safe_get_argv
import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.mt_utils import parallelize_tasks


@dataclass
class PullRequestEntry:
    owner: str = None
    repo: str = None
    issue: int = -1


token: str | None = None
user_filter: UserFilter | None


def get_closed_by(owner: str,
                  repo: str, issue: int,
                  gh_token: str | None = None) \
        -> dict | None:
    global token, user_filter

    used_token = None
    if not gh_token is None:
        used_token = gh_token
    elif token is None:
        dotenv.load_dotenv()
        used_token = getenv("GITHUB_TOKEN_1")

    user_filter = UserFilter()

    headers = {
        'Accept': 'application/vnd.github+json',
        "Authorization": f'bearer {used_token}',
        "X-GitHub-Api-Version": "2022-11-28"
    }

    url = "https://api.github.com/repos/{owner}/{repo}/issues/{issue}"

    real_url = url.format(owner=owner, repo=repo, issue=issue)

    succeeded = False

    while not succeeded:
        result = requests.get(real_url, headers=headers)

        if result.status_code == 403:
            print("Going to sleep...")
            time.sleep(300)
            continue
        elif result.status_code // 100 != 2:
            print(
                f'Error for ({owner=}, {repo=}, {issue=}): status code {result.status_code} with message "{result.text}"')
            return
        succeeded = True

    j_data = json.loads(result.text)

    is_closed = j_data["state"] == "closed"
    if not is_closed:
        print(f'Has state {j_data["state"]}')
        return

    closed_by = j_data['closed_by']
    filtered = user_filter.filter(closed_by)

    return filtered


def get_closed_by_for_closed_and_unmerged_prs():
    """
    Iterates through the chronological data file and retrieves ``closed_by``
    data for each pull request that has been closed and not merged.
    """

    def __get_owner_and_repo(entry: dict) -> tuple[str, str]:
        """Helper method for string magic."""
        source_path = entry["__source_path"]
        file_name_with_ext = source_path.split("/")[-1]
        file_name = ".".join(file_name_with_ext.split(".")[:-1])
        owner_repo = file_name.split("--")
        return (owner_repo[0], owner_repo[1])

    # Creates tasks
    input_path = exp_utils.CHRONOLOGICAL_DATASET_PATH
    tasks = []
    total_entries = 0
    with open(input_path, "r") as input_file:
        for line in input_file:
            total_entries += 1
            entry = json.loads(line)
            if entry["merged"] != True:
                continue
            owner, repo = __get_owner_and_repo(entry)
            issue = entry['number']
            new_pr = PullRequestEntry(owner, repo, issue)
            tasks.append(new_pr)

    print(f'{len(tasks)}/{total_entries} ({100 * (len(tasks)/total_entries):.03f}%).')

    def __pull_data(task: PullRequestEntry, worker_index: int, gh_tokens: list[list[str]], *args, **kwargs):
        """Helper method for parallel retrieval and storage of data."""
        my_token = gh_tokens[worker_index]
        closed_by = get_closed_by(
            task.owner, task.repo, task.issue, gh_token=my_token)
        if closed_by is None:
            return
        entry = {"owner": task.owner, "repo": task.repo,
                 "issue": task.issue, "closed_by": closed_by}
        output_path = f"./data/temp/closed_by_t_{worker_index}.json"
        with open(output_path, "a+") as output_file:
            output_file.write(f"{json.dumps(entry)}\n")

    # Parallelizes the tasks.
    worker_count = 3
    gh_tokens = exp_utils.get_gh_tokens(worker_count)
    parallelize_tasks(tasks, __pull_data, worker_count, gh_tokens=gh_tokens)


def add_closed_by_data_to_prs():
    pass


if __name__ == "__main__":
    dotenv.load_dotenv()
    exp_utils.load_paths_for_all_argv()

    mode = safe_get_argv(key='-m', default="r")
    match(mode):
        case "r":
            get_closed_by_for_closed_and_unmerged_prs()
        case "m":
            add_closed_by_data_to_prs()
        case "b":
            get_closed_by_for_closed_and_unmerged_prs()
            add_closed_by_data_to_prs()
        case _:
            raise ValueError(f"Invalid mode {mode}.")
