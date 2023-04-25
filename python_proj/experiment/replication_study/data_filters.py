from python_proj.experiment.replication_study.retrieve_pull_requests import end_date
import json
from sys import argv
from datetime import datetime
import re

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
    filters = {
        'p': filter_for_github,
        'd': filter_by_close_date,
        'b': filter_for_bots_a,
        'c': filter_for_bots_b,
        'a': filter_for_deleted_accounts,
        'l': filter_for_blacklist,
        # 'm': filter_for_bots_bodegha # TODO: Implement the BoDeGHa classifier.
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


def filter_for_bots_a(entry):
    user_data = entry['user_data']
    user_type = user_data['type'].lower()
    if user_type == 'bot':
        return False
    return True


def filter_for_bots_b(entry):
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
