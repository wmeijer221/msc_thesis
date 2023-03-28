"""
Retrieves pull request and issue data from 
the GHArchive: https://www.gharchive.org/.
"""

import json
import requests
import gzip
import zlib
from datetime import datetime, timedelta
from typing import Generator, Callable, Dict, Tuple
import base64


COMMIT_COMMENT_EVENT = "CommitCommentEvent"
CREATE_EVENT = "CreateEvent"
DELETE_EVENT = "DeleteEvent"
FORK_EVENT = "ForkEvent"
GOLLUM_EVENT = "GollumEvent"
ISSUE_COMMENT_EVENT = "IssueCommentEvent"
ISSUES_EVENT = "IssuesEvent"
MEMBER_EVENT = "MemberEvent"
PUBLIC_EVENT = "PublicEvent"
PULL_REQUEST_EVENT = "PullRequestEvent"
PULL_REQUEST_REVIEW_EVENT = "PullRequestReviewEvent"
PULL_REQUEST_REVIEW_COMMENT_EVENT = "PullRequestReviewCommentEvent"
PULL_REQUEST_REVIEW_THREAD_EVENT = "PullRequestReviewThreadEvent"
PUSH_EVENT = "PushEvent"
RELEASE_EVENT = "ReleaseEvent"
SPONSORSHIP_EVENT = "SponsorshipEvent"
WATCH_EVENT = "WatchEvent"


def get_archive_entry(timestamp: datetime) -> dict:
    """
    Retrieves a single GH Archive data entry.
    """

    year = timestamp.year
    month = timestamp.month
    day = timestamp.day
    hour = timestamp.hour
    url = f"http://data.gharchive.org/{year}-{month:02d}-{day:02d}-{hour:02d}.json.gz"
    print(f'Contacting "{url}"')
    response = requests.get(url)
    if response.status_code // 100 != 2:
        print(f"Failed with status code {response.status_code}.")
        return
    data = gzip.decompress(bytearray(response.content)).decode('utf-8')
    iterable_data = [entry.strip()
                     for entry in data.split("\n") if entry.strip() != ""]
    return iterable_data


def get_data_iterator(start_date: datetime, end_date: datetime) -> Generator[Tuple[datetime, Dict], None, None]:
    """
    Returns generator object for iterating
    through GH Archive data entries.
    """

    delta_time = end_date - start_date
    total_hours = int(delta_time.total_seconds() / 3600)

    generator = (
        (start_date + timedelta(hours=hours),
         get_archive_entry(start_date + timedelta(hours=hours)))
        for hours in range(total_hours)
        if not get_archive_entry(start_date + timedelta(hours=hours)) is None)

    return generator


def get_all_data_of_types(event_types: set[str], on_event_found: Callable[[Dict], None], start_date: datetime, end_date: datetime):
    """
    Retrieves all data from the GH Archive.
    """

    data = get_data_iterator(start_date, end_date)
    for timestamp, entry in data:
        count = 0
        for line in entry:
            j_entry = json.loads(line)
            if j_entry["type"] in event_types:
                on_event_found(j_entry)
                count += 1
        print(f'Found {count} events at {timestamp}.')


def on_event_found(file, included_projects: set, entry: dict):
    """
    Stores entries that are indcluded,
    prunes their URLs and compresses the data.
    """

    if not entry["repo"]["name"] in included_projects:
        return
    entry = prune_url_fields(entry)
    data = json.dumps(entry, separators=(',', ':'))
    data = zlib.compress(base64.b64encode(data.encode("utf-8")))
    # To read the data use:
    # data = base64.b64decode(zlib.decompress(data)).decode("utf-8")
    file.write(data)


def prune_url_fields(entry: dict):
    """
    Prunes all URL fields from the entry.
    """

    pruned_entry = {}
    for key, value in entry.items():
        if key.endswith("url"):
            continue
        if isinstance(value, dict):
            pruned_entry[key] = prune_url_fields(value)
        elif isinstance(value, list):
            pruned_list = []
            for element in value:
                pruned_list.append(prune_url_fields(element))
            pruned_entry[key] = pruned_list
        else:
            pruned_entry[key] = value
    return pruned_entry


if __name__ == "__main__":
    interesting_events = {ISSUE_COMMENT_EVENT, ISSUES_EVENT, PULL_REQUEST_EVENT, PULL_REQUEST_REVIEW_EVENT,
                          PULL_REQUEST_REVIEW_COMMENT_EVENT, PULL_REQUEST_REVIEW_THREAD_EVENT, PUSH_EVENT}
    start_date = datetime(2015, 1, 1, 0)
    end_date = datetime(2020, 4, 19, 23)

    included_projects_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/predictors/included_projects_dl.csv"
    with open(included_projects_path, "r") as included_projects_file:
        included_projects = {entry.strip() for entry in included_projects_file}

    output_path = "./data/retrieve_gharchive.json"

    with open(output_path, "wb+") as output_file:
        get_all_data_of_types(interesting_events,
                              lambda entry: on_event_found(
                                  output_file, included_projects, entry),
                              start_date, end_date)
