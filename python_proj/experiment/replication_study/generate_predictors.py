
from csv import reader, writer
from datetime import datetime
from os import path
import json
import requests

# Dey et al.'s project criteria
# - NPM packages with over 10000 monthly downloads, since January 2018.
#   - i.e., in the past 16 months.
#   - i.e. For us since november 2018
# - Has a github repository
# - Has at least 5 PRs
# - PRs before "April 2019" (for us this is 12 february 2020).
# - PRs are closed.

headers = ['ID', 'Platform', 'Name', 'Created Timestamp', 'Updated Timestamp', 'Description', 'Keywords', 'Homepage URL', 'Licenses', 'Repository URL', 'Versions Count', 'SourceRank', 'Latest Release Publish Timestamp', 'Latest Release Number', 'Package Manager ID', 'Dependent Projects Count', 'Language', 'Status', 'Last synced Timestamp', 'Dependent Repositories Count', 'Repository ID', 'Repository Host Type', 'Repository Name with Owner', 'Repository Description', 'Repository Fork?', 'Repository Created Timestamp', 'Repository Updated Timestamp', 'Repository Last pushed Timestamp', 'Repository Homepage URL', 'Repository Size', 'Repository Stars Count', 'Repository Language', 'Repository Issues enabled?', 'Repository Wiki enabled?',
           'Repository Pages enabled?', 'Repository Forks Count', 'Repository Mirror URL', 'Repository Open Issues Count', 'Repository Default branch', 'Repository Watchers Count', 'Repository UUID', 'Repository Fork Source Name with Owner', 'Repository License', 'Repository Contributors Count', 'Repository Readme filename', 'Repository Changelog filename', 'Repository Contributing guidelines filename', 'Repository License filename', 'Repository Code of Conduct filename', 'Repository Security Threat Model filename', 'Repository Security Audit filename', 'Repository Status', 'Repository Last Synced Timestamp', 'Repository SourceRank', 'Repository Display Name', 'Repository SCM type', 'Repository Pull requests enabled?', 'Repository Logo URL', 'Repository Keywords']

repo_name_index = headers.index("Repository Name with Owner")
proj_name_index = headers.index("Name")

input_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/projects_with_repository_fields-1.6.0-2020-01-12.csv"
input_file = open(input_path, 'r', encoding="utf-8")
csv_reader = reader(input_file, quotechar='"')

# boundary dates for the downloads per month requirement.
# Dey et al. (2020) observed up to 16 months prior.
download_end_date = datetime(2019, 12, 31)
download_start_date = datetime(2018, 11, 1)

source_file = "./data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/{owner}--{repo_name}.json"


def has_pr_file(owner, repo_name) -> bool:
    pr_file_name = source_file.format(owner=owner, repo_name=repo_name)
    return path.exists(pr_file_name)


def has_sufficient_closed_prs(owner, repo_name, threshold: int) -> bool:
    pr_file_name = source_file.format(owner=owner, repo_name=repo_name)
    count = 0
    with open(pr_file_name, "r", encoding="utf-8") as input_file:
        input = input_file.read()
        pull_requests = json.loads(input)
        for pr in pull_requests:
            # PR has to be closed.
            if pr["state"] != "closed":
                continue
            # We don't have to filter for date,
            # as that's been done by GrimoireLab.
            count += 1
    return count >= threshold


def has_sufficient_monthly_downloads(d_start_date: datetime, d_end_date: datetime, project_name: str, threshold: int) -> bool:
    # dates are: YYYY-MM-DD
    start_date = d_start_date.strftime("%Y-%m-%d")
    end_date = d_end_date.strftime("%Y-%m-%d")
    url = f'https://api.npmjs.org/downloads/range/{start_date}:{end_date}/{project_name}'

    response: requests.Response = requests.get(url)
    
    if response.status_code // 100 != 2:
        print(f"Can't get downloads data for {project_name}")
        return False

    reponse_string = response.content.decode("utf-8")
    content = json.loads(reponse_string)
    
    downloads_per_month = {}
    for dl in content["downloads"]:
        downloads = dl["downloads"]
        day = datetime.strptime(dl["day"], "%Y-%m-%d")
        my = f'{day.month}-{day.year}'
        if my not in downloads_per_month:
            downloads_per_month[my] = downloads
        else:
            downloads_per_month[my] += downloads

    # TODO: Figure out how this is calculated.
    # This tests if EACH month has passes the threshold.
    enough_downloads = all([value >= threshold for value
                            in downloads_per_month.values()])

    return enough_downloads


def generate():
    # Iterate through all entries in npm-libraries.
    for entry in csv_reader:
        repo_name = entry[repo_name_index]
        if repo_name == '':
            continue

        try:
            owner, repo = repo_name.split("/")
            proj_name = entry[proj_name_index]
        
            # Skip if:
            #   - Has no PR file.
            #   - Number of CLOSED PRs before 12-02-2020 is less than 5.
            #   - Monthly downloads since November 2018
            if not has_pr_file(owner, repo) or \
                    not has_sufficient_closed_prs(owner, repo, 5) or \
                    not has_sufficient_monthly_downloads(download_start_date, download_end_date, proj_name, 10000):
                continue
        except Exception as e:
            print(f'Failed with: {proj_name}')
            print(entry)
            print(e)
            continue
        print(proj_name)


if __name__ == "__main__":
    generate()
