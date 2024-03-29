"""
Implements inclusion criteria for the different projects.
"""

from csv import reader, writer
from datetime import datetime
from os import path, makedirs
import json
import requests
from sys import argv
import random

from python_proj.utils.arg_utils import safe_get_argv
from python_proj.utils.exp_utils import BASE_PATH
from python_proj.utils.util import safe_index

# Dey et al.'s project criteria
# - NPM packages with over 10000 monthly downloads, since January 2018.
#   - i.e., in the past 16 months.
#   - i.e. For us since november 2018
# - Has a github repository
# - Has at least 5 PRs
# - PRs before "April 2019" (for us this is 12 february 2020).
# - PRs are closed.

headers = [
    "ID",
    "Platform",
    "Name",
    "Created Timestamp",
    "Updated Timestamp",
    "Description",
    "Keywords",
    "Homepage URL",
    "Licenses",
    "Repository URL",
    "Versions Count",
    "SourceRank",
    "Latest Release Publish Timestamp",
    "Latest Release Number",
    "Package Manager ID",
    "Dependent Projects Count",
    "Language",
    "Status",
    "Last synced Timestamp",
    "Dependent Repositories Count",
    "Repository ID",
    "Repository Host Type",
    "Repository Name with Owner",
    "Repository Description",
    "Repository Fork?",
    "Repository Created Timestamp",
    "Repository Updated Timestamp",
    "Repository Last pushed Timestamp",
    "Repository Homepage URL",
    "Repository Size",
    "Repository Stars Count",
    "Repository Language",
    "Repository Issues enabled?",
    "Repository Wiki enabled?",
    "Repository Pages enabled?",
    "Repository Forks Count",
    "Repository Mirror URL",
    "Repository Open Issues Count",
    "Repository Default branch",
    "Repository Watchers Count",
    "Repository UUID",
    "Repository Fork Source Name with Owner",
    "Repository License",
    "Repository Contributors Count",
    "Repository Readme filename",
    "Repository Changelog filename",
    "Repository Contributing guidelines filename",
    "Repository License filename",
    "Repository Code of Conduct filename",
    "Repository Security Threat Model filename",
    "Repository Security Audit filename",
    "Repository Status",
    "Repository Last Synced Timestamp",
    "Repository SourceRank",
    "Repository Display Name",
    "Repository SCM type",
    "Repository Pull requests enabled?",
    "Repository Logo URL",
    "Repository Keywords",
]

repo_host_type_index = headers.index("Repository Host Type")
repo_name_index = headers.index("Repository Name with Owner")
proj_name_index = headers.index("Name")

input_path = (
    BASE_PATH
    + "libraries/npm-libraries-1.6.0-2020-01-12/projects_with_repository_fields-1.6.0-2020-01-12.csv"
)
lib_output_path = (
    BASE_PATH
    + "libraries/npm-libraries-1.6.0-2020-01-12/projects_with_repository_fields-1.6.0-2020-01-12_filtered{filter_ext}.csv"
)
input_file = open(input_path, "r", encoding="utf-8")
csv_reader = reader(input_file, quotechar='"')

# boundary dates for the downloads per month requirement.
# Dey et al. (2020) observed up to 16 months prior.
# 16 months is an arbitrary number (confirmed by the author).
download_end_date = datetime(2019, 12, 31)
download_start_date = datetime(2018, 11, 1)

# The final date by which the PR can be submitted.
max_pr_date = datetime(2020, 1, 12)

source_file = (
    BASE_PATH
    + "libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/{owner}--{repo_name}{ext}.json"
)

# HACK: this is only written here to supress linter warnings; it's immediately overwritten in `__main__`.
min_prs = 0

def has_pr_file(owner, repo_name, ext) -> bool:
    pr_file_name = source_file.format(owner=owner, repo_name=repo_name, ext=ext)
    return path.exists(pr_file_name)


def has_sufficient_closed_prs(
    owner, repo_name, threshold: int, host_type: str, ext: str
) -> bool:
    pr_file_name = source_file.format(owner=owner, repo_name=repo_name, ext=ext)
    count = 0
    with open(pr_file_name, "r", encoding="utf-8") as input_file:
        input = input_file.read()
        pull_requests = json.loads(input)

        if host_type.lower() == "github":
            for pr in pull_requests:
                # PR has to be closed.
                if pr["state"] != "closed":
                    continue
                # We don't have to filter for date,
                # as that's been done by GrimoireLab.
                count += 1
        elif host_type.lower() == "gitlab":
            for pr in pull_requests:
                # PR has to be closed.
                if pr["state"] == "opened":
                    continue
                # Perceval's Gitlab backend can't filter on date.
                # Therefore it has to be done here.
                try:
                    tformat = "%Y-%m-%dT%H:%M:%S.%fZ"
                    updated_at = datetime.strptime(pr["updated_at"], tformat)
                    created_at = datetime.strptime(pr["created_at"], tformat)
                except:
                    tformat = "%Y-%m-%dT%H:%M:%SZ"
                    updated_at = datetime.strptime(pr["updated_at"], tformat)
                    created_at = datetime.strptime(pr["created_at"], tformat)
                if created_at > max_pr_date or updated_at > max_pr_date:
                    continue
                count += 1
        else:
            # Others are unsupported.
            count = 0
    return count >= threshold


def has_sufficient_monthly_downloads(
    d_start_date: datetime, d_end_date: datetime, project_name: str, threshold: int
) -> bool:
    # dates are: YYYY-MM-DD
    start_date = d_start_date.strftime("%Y-%m-%d")
    end_date = d_end_date.strftime("%Y-%m-%d")
    url = (
        f"https://api.npmjs.org/downloads/range/{start_date}:{end_date}/{project_name}"
    )

    response: requests.Response = requests.get(url)

    if response.status_code // 100 != 2:
        print(f"Can't get downloads data for {project_name}.")
        return False

    reponse_string = response.content.decode("utf-8")
    content = json.loads(reponse_string)

    downloads_per_month = {}
    for dl in content["downloads"]:
        downloads = dl["downloads"]
        day = datetime.strptime(dl["day"], "%Y-%m-%d")
        my = f"{day.month}-{day.year}"
        if my not in downloads_per_month:
            downloads_per_month[my] = downloads
        else:
            downloads_per_month[my] += downloads

    # This tests if ANY month has passes the threshold.
    # (I confirmed this with the author.)
    enough_downloads = any(
        [value >= threshold for value in downloads_per_month.values()]
    )

    return enough_downloads


output_path = BASE_PATH + "libraries/npm-libraries-1.6.0-2020-01-12/predictors/"
output_valid_entries_path = output_path + "included_projects{key}.csv"


# TODO: Rename this to something more explicit.
def generate(exlusion_criteria: callable, output_key: str = "", ext: str = ""):
    """
    Generates a list of projects that don't
    match the exclusion criteria; i.e., a list
    of 'valid' projects.
    :param exclusion_criteria: projects are filtered using this callable.
    A row in the Katz dataset is passed onto this method for analysis.
    :param output_key: the suffix applied to the output file containing
    'valid' projects.
    """

    if not path.exists(output_path):
        makedirs(output_path)
    r_output_valid_entries_path = output_valid_entries_path.format(key=output_key)
    output_valid_entries = open(r_output_valid_entries_path, "w+", encoding="utf-8")

    passed_valid = set()
    passed_invalid = set()

    # Iterate through all entries in npm-libraries.
    for entry in csv_reader:
        repo_name = entry[repo_name_index]
        print(f"Starting with: {repo_name}")
        # projects without a repo are ignored by default.
        if repo_name == "":
            continue

        try:
            # Skips already blocked invalid projects,
            # Applies exclusion criteria.
            if not repo_name in passed_valid and (
                repo_name in passed_invalid or exlusion_criteria(entry, ext)
            ):
                passed_invalid.add(repo_name)
                continue
        except json.decoder.JSONDecodeError:
            # catches broken data files.
            # mostly here for debugging.
            print(f"Failed decoding JSON for {repo_name}.")
            continue
        except Exception as e:
            print(f"Failed with: {repo_name}")
            print(entry)
            raise e

        # Adds project to included projects when the criteria do not apply.
        passed_valid.add(repo_name)
        output_valid_entries.write(repo_name + "\n")
        output_valid_entries.flush()


def exclusion_prs(entry, ext: str):
    """
    Applies exclusion criteria for PR count.
    It also ignores projects without a PR file.
    :param entry: csv row of Katz dataset.
    :param ext: PR file extention.
    """

    global min_prs
    repo_name = entry[repo_name_index]
    name_split = repo_name.split("/")
    owner = name_split[0]
    repo = name_split[-1]
    host_type = entry[repo_host_type_index]
    return not has_pr_file(owner, repo, ext) or not has_sufficient_closed_prs(
        owner, repo, min_prs, host_type, ext
    )


def exclusion_downloads(entry):
    proj_name = entry[proj_name_index]
    print(proj_name)
    return not has_sufficient_monthly_downloads(
        download_start_date, download_end_date, proj_name, 10000
    )

def exclusion_both(entry, ext):
    # TODO: remove this
    return exclusion_prs(entry, ext) or exclusion_downloads(entry)


def merge_inclusion_lists(list_a: str = "pr", list_b: str = "dl", list_out: str = ""):
    """Outputs the intersection between two inclusion lists."""
    with open(
        f"{output_path}included_projects_{list_a}.csv", "r", encoding="utf-8"
    ) as pr_filtered:
        pr_set = set([entry.strip() for entry in pr_filtered.readlines()])

    with open(
        f"{output_path}included_projects_{list_b}.csv", "r", encoding="utf-8"
    ) as dl_filtered:
        dl_set = set([entry.strip() for entry in dl_filtered.readlines()])

    i_set = pr_set.intersection(dl_set)

    with open(
        f"{output_path}included_projects{list_out}.csv", "w+", encoding="utf-8"
    ) as merged_filtered:
        merged_filtered.writelines([f"{entry}\n" for entry in i_set])

    print("Merged results.")


def filter_libraries_data(filter_file_key: str):
    if filter_file_key is None:
        filter_file_key = ""
    project_file = open(input_path, "r")
    project_reader = reader(project_file)
    filter_path = output_valid_entries_path.format(key=filter_file_key)
    filter_file = open(filter_path, "r")
    proj_filter = set(
        [fl.strip() for fl in filter_file.readlines() if fl.strip() != ""]
    )
    output_file = open(lib_output_path.format(filter_ext=filter_file_key), "w+")
    project_writer = writer(output_file)

    for entry in project_reader:
        if entry[repo_name_index] in proj_filter:
            project_writer.writerow(entry)


def sample_list(name: str, sample_size: int):
    with open(f"{output_path}included_projects_{name}.csv", "r") as input_file:
        entries: list = list(input_file.readlines())
        random_order = [random.random() for _ in entries]
        zipped = list(zip(entries, random_order))
        zipped.sort(key=lambda x: x[1])
        sample = [entry[0] for entry in zipped[:sample_size]]

        with open(
            f"{output_path}included_projects_{name}_sampled.csv", "w+"
        ) as output_file:
            for entry in sample:
                output_file.write(f"{entry}")


if __name__ == "__main__":
    # Skip if:
    #   - Has no PR file.
    #   - Number of CLOSED PRs before 12-02-2020 is less than 5.
    #   - Monthly downloads since November 2018

    if (m_index := safe_index(argv, "-m")) != -1:
        mode = argv[argv.index("-m") + 1].lower()
        print(f'Starting in mode "{mode}".')

        if (ext_idx := safe_index(argv, "-x")) >= 0:
            ext = argv[ext_idx + 1]
        else:
            ext = ""

        if mode == "d":
            # TODO: This is done in `pre_sort_filters_mt`, so can be deleted from this script.
            generate(exclusion_downloads, "_dl")
        elif mode == "p":
            min_prs = safe_get_argv("-pr", 5)
            # TODO: this whole `ext` argument passing is super smelly.
            generate(exclusion_prs, "_pr", ext)
        elif mode == "m":
            merge_inclusion_lists()
        elif mode == "mc":
            list_a = argv[-3]
            list_b = argv[-2]
            list_out = argv[-1]
            merge_inclusion_lists(list_a, list_b, f"_{list_out}")
        elif mode == "s":
            list_a = argv[-2]
            sample_size = int(argv[-1])
            sample_list(list_a, sample_size)
        elif mode == "a":
            ext = None
            if (ext_idx := safe_index(argv, "-t")) > 0:
                ext = f"_{argv[ext_idx + 1]}"
            filter_libraries_data(ext)
        else:
            raise ValueError(f'Invalid mode "{mode}".')
    else:
        # TODO: drop support for this.
        generate(exclusion_both)
