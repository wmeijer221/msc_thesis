from python_proj.experiment.replication_study.retrieve_pull_requests import end_date
import json
from sys import argv
from datetime import datetime
import re
from csv import reader

input_path = './data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/sorted.json'
output_path = './data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/sorted_filtered.json'


def load_data():
    data = []
    with open(input_path, "r") as input_data:
        for line in input_data:
            line = line.strip()
            j_entry = json.loads(line)
            data.append(j_entry)
    return data


def build_filters(filter_keys: str):
    # Standard filter: pcuadgb
    filters = {
        'p': filter_for_github,
        'c': filter_by_close_date,
        'u': filter_for_bots_by_user_type,
        'a': filter_for_deleted_accounts,
        'd': filter_bots_dey_2020,
        'g': filter_bots_golzadeh_2021,
        'b': filter_for_blacklist,  # Add self-identified bots to this list.
        'r': filter_for_bots_primitive_regex,  # We should not use this.
    }
    filters = [filters[key] for key in filter_keys]
    return filters


def filter_by_close_date(entry):
    closed_at_key = 'closed_at'
    if not closed_at_key in entry:
        return False
    closed_date = entry[closed_at_key]
    closed_at_dt = datetime.strptime(closed_date, "%Y-%m-%dT%H:%M:%SZ")
    return closed_at_dt <= end_date


def filter_for_github(entry):
    created_at_key = 'created_at'
    created_date = entry[created_at_key]
    # HACK: GitLab uses a different time format. I've got no better way to test for GH PRs, though.
    try:
        dt = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%SZ")
    except:
        dt = None
    finally:
        return not dt is None


def filter_for_bots_by_user_type(entry):
    user_data = entry['user_data']
    user_type = user_data['type']
    return user_type.lower() != 'bot'


dey_bots_names = None
dey_bots_emails = None


def filter_bots_dey_2020(entry):
    global dey_bots_emails, dey_bots_names

    # HACK: make-shift init function for the filter.
    if dey_bots_emails is None or dey_bots_emails is None:
        filter_path = "./data/bot_data/dey_2020_bots.json"
        with open(filter_path, "r") as input_file:
            j_data = json.loads(input_file.read())
            dey_bots_emails = set()
            dey_bots_names = set()
            for entry in j_data:
                dey_bots_emails.add(entry['email'])
                dey_bots_names.add(entry['name'].lower())

    # Actual filter
    user_data = entry["user_data"]
    if user_data["email"] in dey_bots_emails \
        or user_data["login"].lower() in dey_bots_names \
            or user_data["name"].lower() in dey_bots_names:
        return False

    return True


golzadeh_bots_names = None


def filter_bots_golzadeh_2021(entry):
    global golzadeh_bots_names

    # HACK: make-shift init function.
    if golzadeh_bots_names is None:
        filter_path = "./data/bot_data/golzadeh_2021_bots.csv"
        with open(filter_path, "r") as filter_file:
            filter_reader = reader(filter_file, quotechar='"')
            _ = next(filter_reader)  # Skips header
            golzadeh_bots_names = {entry[0].lower() for entry in filter_reader}

    # actual filter
    user_data = entry["user_data"]
    if user_data["login"].lower() in golzadeh_bots_names:
        return False

    return True


def filter_for_bots_primitive_regex(entry):
    user_data = entry['user_data']
    user_login = user_data["login"].lower()
    contains_bot = r'.*bot.*'

    bot_match = re.match(contains_bot, re.escape(user_login))
    if not bot_match is None:
        return False

    if not 'name' in user_data:
        return True

    user_name = user_data['name'].lower()
    bot_match = re.match(contains_bot, re.escape(user_name))
    if not bot_match is None:
        return False

    return True


def filter_for_deleted_accounts(entry):
    user_data = entry['user_data']
    user_login = user_data['login'].lower()
    # Accounts that are deleted are represented by the 'ghost' account. See https://github.com/ghost
    return user_login != 'ghost'


def filter_for_blacklist(entry):
    user_data = entry['user_data']
    user_login = user_data['login'].lower()
    return not user_login in ["fabric8cd", "mrsflux"]


def filter_data(data: list, filters: list) -> list:
    filtered_data = []
    filtered_by = [0] * len(filters)
    for entry in data:
        is_included = True
        for index, filter in enumerate(filters):
            if not filter(entry):
                filtered_by[index] += 1
                is_included = False
                break
        if is_included:
            filtered_data.append(entry)
    print(filtered_by)
    return filtered_data


def write_data(data: list):
    with open(output_path, "w+") as output_file:
        for entry in data:
            output_file.write(f'{json.dumps(entry)}\n')


if __name__ == "__main__":
    if (idx := argv.index('-i')) > -1:
        input_path = argv[idx + 1]
    if (idx := argv.index('-o')) > -1:
        output_path = argv[idx + 1]

    mode = argv[argv.index('-m') + 1]

    filters = build_filters(mode)
    data = load_data()
    print(f'Start size: {len(data)}.')

    filtered_data = filter_data(data, filters)
    print(f'Filtered size: {len(filtered_data)}.')
    write_data(filtered_data)
