"""
Retrieves the ``closed_by`` fields for pull requests that have been closed but not merged.
This script is only here because I forgot to include the ``closed_by`` field in the ``IssueFilter``.
If you re-run the experiment in its entirety, you don't need this script.

To gather this data, run ``python3 ./python_proj/data_retrieval/get_closed_by_data.py -m b -t 3 -f sorted_filtered``
where -t is the number of used threads/API keys, and -f the targeted chronological datafile.
Alternatively, you could run it in two goes using ``-t r`` and the ``-t m`` arguments instead.
The result of this will be a ``.temp`` file in the folder where the used chronological datafile is stored as well.
"""

from dataclasses import dataclass
import dotenv
import json
from os import getenv, path, makedirs
import requests
import time

from python_proj.data_retrieval.gl_filters.gl_github_filters import UserFilter
from python_proj.utils.arg_utils import safe_get_argv
import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.mt_utils import parallelize_tasks


@dataclass(frozen=True)
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


def __get_owner_and_repo(entry: dict) -> tuple[str, str]:
    """Helper method for string magic."""
    source_path: str = entry["__source_path"]
    file_name_with_ext = source_path.split("/")[-1]
    file_name = ".".join(file_name_with_ext.split(".")[:-1])
    owner_repo = file_name.split("--")
    return (owner_repo[0], owner_repo[1])


def get_closed_by_for_closed_and_unmerged_prs(worker_count: int, output_path: str, worker_index_offset: int):
    """
    Iterates through the chronological data file and retrieves ``closed_by``
    data for each pull request that has been closed and not merged.
    """

    # Creates tasks
    input_path = exp_utils.CHRONOLOGICAL_DATASET_PATH
    tasks = []
    total_entries = 0
    print(f'Using inputdata: {input_path}')
    with open(input_path, "r") as input_file:
        for line in input_file:
            total_entries += 1
            entry = json.loads(line)
            # merged entries don't have a ``closed_by`` field,
            # and it doesn't make sense to load it for those the
            # data has been collected for already.
            integrator_key = exp_utils.get_integrator_key(entry)
            if entry['merged'] or integrator_key in entry:
                continue
            owner, repo = __get_owner_and_repo(entry)
            issue = entry['number']
            new_pr = PullRequestEntry(owner, repo, issue)
            tasks.append(new_pr)

    print(
        f'Tasks: {len(tasks)}/{total_entries} ({100 * (len(tasks)/total_entries):.03f}%).')

    def __pull_data(task: PullRequestEntry, worker_index: int, gh_tokens: list[list[str]], *args, **kwargs):
        """Helper method for parallel retrieval and storage of data."""

        my_token = gh_tokens[worker_index]
        closed_by = get_closed_by(
            task.owner, task.repo, task.issue, gh_token=my_token)
        if closed_by is None:
            return
        entry = {"owner": task.owner, "repo": task.repo,
                 "issue": task.issue, "closed_by": closed_by}
        r_worker_index = worker_index_offset + worker_index
        r_output_path = output_path.format(worker_index=r_worker_index)
        with open(r_output_path, "a+") as output_file:
            output_file.write(f"{json.dumps(entry)}\n")

    # Parallelizes the tasks.
    gh_tokens = exp_utils.get_gh_tokens(worker_count)
    parallelize_tasks(tasks, __pull_data, worker_count,
                      gh_tokens=gh_tokens, worker_index_offset=worker_index_offset)


def add_closed_by_data_to_prs(worker_count: int, input_path: str):
    identities = {}
    # Loads data from files.
    for index in range(0, worker_count):
        r_input_path = input_path.format(worker_index=index)
        print(f'Loading entries from: {r_input_path}.')
        with open(r_input_path, "r") as input_file:
            for line in input_file:
                j_data = json.loads(line.strip())
                pr_entry = PullRequestEntry(j_data["owner"],
                                            j_data["repo"],
                                            j_data["issue"])
                identities[pr_entry] = j_data["closed_by"]
    print(f'Loaded {len(identities)} closed by entries.')
    # Loads data from sorted_file.
    missing = 0
    merged_total = 0
    unmerged_total = 0
    output_path = f'{exp_utils.CHRONOLOGICAL_DATASET_PATH}.temp'
    with open(output_path, "w+") as output_file:
        for entry in exp_utils.iterate_through_chronological_data():
            if entry["merged"]:
                merged_total += 1
                output_file.write(f'{json.dumps(entry)}\n')
                continue
            (owner, repo) = __get_owner_and_repo(entry)
            repo_entry = PullRequestEntry(owner, repo, entry['number'])
            unmerged_total += 1
            if repo_entry in identities:
                closed_by = identities[repo_entry]
                entry["closed_by"] = closed_by
                output_file.write(f'{json.dumps(entry)}\n')
            else:
                # i.e., entries for which there is no closed_by data is removed
                # from the dataset! When applying, this happened for
                # 1769/1189740 (0.149%) of the UNMERGED PRs in hte core projects
                # (so ~0.12% of the total dataset).
                missing += 1
    print(
        f'Missing {missing}/{unmerged_total} ({100 * missing / unmerged_total:.03f}%) entries for UNMERGED PRs.')
    print(
        f'Missing {missing}/{unmerged_total + merged_total} ({100 * missing / (unmerged_total + merged_total):.03f}%) entries for ALL PRs.')


def get_closed_by_data():
    dotenv.load_dotenv()
    exp_utils.load_paths_for_all_argv()

    subfolder = safe_get_argv(key="-s", default="")
    # TODO: Move this path somewhere else;
    # technically it's not temp data either.
    temp_data_path = f'{exp_utils.BASE_PATH}/temp/{subfolder}/' + \
        "closed_by_t_{worker_index}.json"
    
    print(f'Outputting in: {temp_data_path}.')

    dir_name = path.dirname(temp_data_path)
    if not path.exists(dir_name):
        makedirs(dir_name)

    mode = safe_get_argv(key='-m', default="r")
    worker_count = safe_get_argv(key="-t", default=3, data_type=int)
    worker_index_offset = safe_get_argv(key="-wo", default=0, data_type=int)
    
    match(mode):
        case "r":
            get_closed_by_for_closed_and_unmerged_prs(
                worker_count, temp_data_path, worker_index_offset)
        case "m":
            add_closed_by_data_to_prs(worker_count, temp_data_path)
        case "b":
            get_closed_by_for_closed_and_unmerged_prs(
                worker_count, temp_data_path, worker_index_offset)
            add_closed_by_data_to_prs(worker_count, temp_data_path)
        case _:
            raise ValueError(f"Invalid mode {mode}.")


if __name__ == "__main__":
    get_closed_by_data()
