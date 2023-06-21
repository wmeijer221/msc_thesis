"""
Filters datasets based on various criteria (e.g. whether they're bots) 
using the sorted version of the dataset; i.e., the output of the 
``data_sorter`` scriptnot the loose files generated by the retrieval scripts.

Commandline arguments:
-e: the used ecosystem (npm)
-d: the used datasource (pull-requests)
-i: the used input file (sorted)
-o: the used output file (sorted_filtered)
"""


import json
from datetime import datetime
import re
from csv import reader
from typing import Generator

from python_proj.data_retrieval.retrieve_pull_requests import end_date
from python_proj.utils.arg_utils import get_argv
from python_proj.utils.exp_utils import build_data_path_from_argv, BASE_PATH


def load_data(data_input_path: str) -> Generator[dict, None, None]:
    """loads dataset"""
    # j_data = []
    ds_start_size = 0
    with open(data_input_path, "r", encoding='utf-8') as input_data:
        for line in input_data:
            line = line.strip()
            j_entry = json.loads(line)
            yield j_entry
            ds_start_size += 1
            # j_data.append(j_entry)
    # return j_data
    print(f'{ds_start_size=}')


def build_filters(selected_filter_keys: str):
    """Builds a filter for a series of keys."""
    # Standard filter: pcuadgbn
    all_filters = {
        'p': filter_for_github,
        'c': filter_by_close_date,
        'u': filter_for_bots_by_user_type,
        'a': filter_for_deleted_accounts,
        'd': filter_bots_dey_2020,
        'g': filter_bots_golzadeh_2021,
        'b': filter_for_blacklist,  # Add self-identified bots to this list.
        'n': filter_for_bot_in_name,
    }
    selected_filters = [all_filters[key] for key in selected_filter_keys]
    return selected_filters


def filter_by_close_date(entry):
    """
    If it doesn't have a closed_at key it's removed, 
    and if the date is too new, it is removed as well.
    """

    closed_at_key = 'closed_at'
    if not closed_at_key in entry:
        return False
    closed_date = entry[closed_at_key]
    closed_at_dt = datetime.strptime(closed_date, "%Y-%m-%dT%H:%M:%SZ")
    return closed_at_dt <= end_date


def filter_for_github(entry):
    """
    If it's not a github entry, it's removed.
    """

    created_at_key = 'created_at'
    created_date = entry[created_at_key]
    # HACK: GitLab uses a different time format. I've got no better way to test for GH PRs, though.
    try:
        datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except:
        return False


def filter_for_bots_by_user_type(entry):
    """
    If the user type is a bot, it's removed.
    """

    user_data = entry['user_data']
    user_type = user_data['type']
    return user_type.lower() != 'bot'


DEY_BOTS_NAMES = None
DEY_BOTS_EMAILS = None


def filter_bots_dey_2020(entry):
    """
    If Dey's (2020) list includes the submitter, it's removed;
    i.e., when they thin, it's a bot.
    """

    global DEY_BOTS_EMAILS, DEY_BOTS_NAMES

    # HACK: make-shift init function for the filter.
    if DEY_BOTS_EMAILS is None or DEY_BOTS_EMAILS is None:
        filter_path = BASE_PATH + "bot_data/dey_2020_bots.json"
        with open(filter_path, "r", encoding='utf-8') as input_file:
            j_data = json.loads(input_file.read())
            DEY_BOTS_EMAILS = set()
            DEY_BOTS_NAMES = set()
            for bot_entry in j_data:
                DEY_BOTS_EMAILS.add(bot_entry['email'])
                DEY_BOTS_NAMES.add(bot_entry['name'].lower())

    # Actual filter
    user_data = entry["user_data"]
    if ("email" in user_data and user_data["email"] in DEY_BOTS_EMAILS) \
        or user_data["login"].lower() in DEY_BOTS_NAMES \
            or ('name' in user_data and user_data["name"].lower() in DEY_BOTS_NAMES):
        return False

    return True


GOLZADEH_BOTS_NAMES = None


def filter_bots_golzadeh_2021(entry):
    """
    If Golzadeh's (2020) list includes the submitter, it's removed;
    i.e., when they thin, it's a bot.
    """

    global GOLZADEH_BOTS_NAMES

    # HACK: make-shift init function.
    if GOLZADEH_BOTS_NAMES is None:
        filter_path = BASE_PATH + "bot_data/golzadeh_2021_bots.csv"
        with open(filter_path, "r", encoding='utf-8') as filter_file:
            filter_reader = reader(filter_file, quotechar='"')
            _ = next(filter_reader)  # Skips header
            GOLZADEH_BOTS_NAMES = {entry[0].lower() for entry in filter_reader}

    # actual filter
    user_data = entry["user_data"]
    if user_data["login"].lower() in GOLZADEH_BOTS_NAMES:
        return False

    return True


def filter_for_deleted_accounts(entry):
    """
    Filters entries submitted by the ghost user.
    """

    user_data = entry['user_data']
    user_login = user_data['login'].lower()
    # Accounts that are deleted are represented by the 'ghost' account. See https://github.com/ghost
    return user_login != 'ghost'


def filter_for_blacklist(entry):
    """
    Filters if entries are submitted by custom manually found bot.
    """

    user_data = entry['user_data']
    user_login = user_data['login'].lower()
    return not user_login in ["fabric8cd", "mrsflux", "greenkeeperio-bot", "ovh-ux-cds"]


def filter_for_bot_in_name(entry):
    """
    Filters when the name contains [bot]
    """

    user_data = entry['user_data']
    login = user_data['login']
    for _ in re.finditer(r'\[bot\]', login):
        return False
    return True


def filter_data(original_data: Generator, filter_methods: list) -> Generator[dict, None, None]:
    """Iterates through data and applies provided filters."""
    # filtered = []
    filtered_by = [0] * len(filter_methods)
    filtered_ds_size = 0
    for progress, entry in enumerate(original_data):
        if progress % 10000 == 0:
            print(f'{progress=}/{len(original_data)}')
        is_included = True
        for index, filter_method in enumerate(filter_methods):
            try:
                # NOTE: Filters must return False if the entry is taken out.
                if not filter_method(entry):
                    filtered_by[index] += 1
                    is_included = False
                    break
            except:
                print(f'Failed with {entry=} and {filter_method=}.')
                raise
        if is_included:
            # filtered.append(entry)
            filtered_ds_size += 1
            yield entry
    print(filtered_by)
    print(f'{filtered_ds_size=}')
    # return filtered


def write_data(output_data: Generator, output_data_path: str):
    """writes data to file."""
    with open(output_data_path, "w+", encoding='utf-8') as output_file:
        for entry in output_data:
            output_file.write(f'{json.dumps(entry)}\n')


if __name__ == "__main__":
    input_path = build_data_path_from_argv(file_name_key='-i')
    output_path = build_data_path_from_argv(file_name_key='-o')
    mode = get_argv(key="-m")

    filters = build_filters(mode)
    data = load_data(input_path)
    # print(f'Start size: {len(data)}.')

    filtered_data = filter_data(data, filters)
    # print(f'Filtered size: {len(filtered_data)}.')
    write_data(filtered_data, output_path)
