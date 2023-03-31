from datetime import datetime
from csv import reader, writer
import json
from typing import Callable
from os import path
from sortedcontainers import SortedList

from python_proj.experiment.util import safe_add_list_element

headers = ['ID', 'Platform', 'Name', 'Created Timestamp', 'Updated Timestamp', 'Description', 'Keywords', 'Homepage URL', 'Licenses', 'Repository URL', 'Versions Count', 'SourceRank', 'Latest Release Publish Timestamp', 'Latest Release Number', 'Package Manager ID', 'Dependent Projects Count', 'Language', 'Status', 'Last synced Timestamp', 'Dependent Repositories Count', 'Repository ID', 'Repository Host Type', 'Repository Name with Owner', 'Repository Description', 'Repository Fork?', 'Repository Created Timestamp', 'Repository Updated Timestamp', 'Repository Last pushed Timestamp', 'Repository Homepage URL', 'Repository Size', 'Repository Stars Count', 'Repository Language', 'Repository Issues enabled?', 'Repository Wiki enabled?',
           'Repository Pages enabled?', 'Repository Forks Count', 'Repository Mirror URL', 'Repository Open Issues Count', 'Repository Default branch', 'Repository Watchers Count', 'Repository UUID', 'Repository Fork Source Name with Owner', 'Repository License', 'Repository Contributors Count', 'Repository Readme filename', 'Repository Changelog filename', 'Repository Contributing guidelines filename', 'Repository License filename', 'Repository Code of Conduct filename', 'Repository Security Threat Model filename', 'Repository Security Audit filename', 'Repository Status', 'Repository Last Synced Timestamp', 'Repository SourceRank', 'Repository Display Name', 'Repository SCM type', 'Repository Pull requests enabled?', 'Repository Logo URL', 'Repository Keywords']

repo_name_index = headers.index("Repository Name with Owner")


project_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/projects_with_repository_fields-1.6.0-2020-01-12_filtered.csv"
pull_base_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/"


def iterate_through_pulls(on_pull: Callable[[str, dict], None]):
    with open(project_path, "r") as project_file:
        project_reader = reader(project_file)
        for entry in project_reader:
            project_id = entry[0]
            repo_name = entry[repo_name_index]
            repo_split = repo_name.split("/")
            repo_path = f'{pull_base_path}{repo_split[0]}--{repo_split[-1]}.json'
            if not path.exists(repo_path):
                print(f"FILE DOESNT EXIST: {repo_path}")
                continue
            with open(repo_path, "r") as pull_file:
                pulls = json.loads(pull_file.read())
                for pull in pulls:
                    on_pull(repo_name, project_id, pull)


sorted_pulls = SortedList(key=lambda entry: datetime.strptime(
    entry["closed_at"], "%Y-%m-%dT%H:%M:%SZ"))


def sort_pulls_by_date(proj_name, project_id, pull: dict):
    if pull["state"] != "closed":
        return
    pull_id = pull["id"]
    duplicate = False
    duplicate_item = None
    for element in sorted_pulls:
        if element['id'] == pull_id:
            duplicate = True
            duplicate_item = element
            break

    if duplicate:
        duplicate_item["project_ids"].append(project_id)
    else:
        pull['project_ids'] = [project_id]
        pull['proj_name'] = proj_name
        sorted_pulls.add(pull)


iterate_through_pulls(sort_pulls_by_date)

dep_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/repository_dependencies-1.6.0-2020-01-12_filtered.csv"


def map_dependencies():
    dependent_to_dependees = {}
    dependee_to_dependents = {}

    with open(dep_path) as dep_file:
        dep_reader = reader(dep_file)
        for entry in dep_reader:
            dependent_id = entry[0]
            dependee_id = entry[-1]

            safe_add_list_element(dependent_to_dependees,
                                  dependent_id, dependee_id)
            safe_add_list_element(dependee_to_dependents,
                                  dependee_id, dependent_id)

    return dependent_to_dependees, dependee_to_dependents


_, dependee_to_dependents = map_dependencies()
print("Created dependency map")

projs_per_user: dict[int, set[int]] = {}

pull_count = {}
acc_pull_count = {}
rej_pull_count = {}

output_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/extract/dey_factors.csv"
entry_output = open(output_path, "w+")
output_writer = writer(entry_output)
output_writer.writerow(
    ["Project ID", "Pull ID", "PR Count", "Acc Ratio", "Worked on dependent"])


def handle_pull(_: str, __: int, pull: dict):
    if not pull["state"] == "closed":
        return

    subm_id = pull["user_data"]["id"]

    # Number of pulls per submitter.
    pulls = pull_count[subm_id] if subm_id in pull_count else 0

    # Ratio of merged/rejected pulls.
    pulls_acc = acc_pull_count[subm_id] if subm_id in acc_pull_count else 0
    pulls_rej = rej_pull_count[subm_id] if subm_id in rej_pull_count else 0
    acc_rat = pulls_acc / (pulls_acc + pulls_rej) if pulls > 0 else 0

    # Worked on dependent projects.
    projs = projs_per_user[subm_id] if subm_id in projs_per_user else []
    dependents = []
    for project_id in pull["project_ids"]:
        if project_id in dependee_to_dependents:
            dependents.extend(dependee_to_dependents[project_id])
    inter = set(projs).intersection(dependents)
    has_worked_on_dependent = len(inter) > 0

    entry = (pull["id"], pulls, acc_rat, has_worked_on_dependent)
    output_writer.writerow(entry)

    # Adds new user.
    if not subm_id in pull_count:
        pull_count[subm_id] = 0
        acc_pull_count[subm_id] = 0
        rej_pull_count[subm_id] = 0
        projs_per_user[subm_id] = set()

    # Increases pulls
    pull_count[subm_id] += 1

    # Updates odds.
    if pull["merged"] == True:
        acc_pull_count[subm_id] += 1
    else:
        rej_pull_count[subm_id] += 1

    # Adds projects.
    projs_per_user[subm_id].union(pull["project_ids"])


for entry in sorted_pulls:
    handle_pull(None, entry["project_ids"], entry)
