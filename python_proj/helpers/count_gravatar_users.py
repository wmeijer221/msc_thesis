import python_proj.utils.exp_utils as exp_utils


def count_gravater_users() -> int:
    unique_users = set()
    users_with_gravatar = 0

    def __account_for_user(user: dict):
        if user["id"] in unique_users:
            return
        unique_users.add(user["id"])
        if "gravatar_id" in entry and entry["gravatar_id"] != "":
            users_with_gravatar += 1

    for entry in exp_utils.iterate_through_chronological_data():
        __account_for_user(entry["user_data"])
        if "closed_by" in entry:
            __account_for_user(entry["closed_by"])
        if "merged_by" in entry:
            __account_for_user(entry["merged_by"])

    print(f'{users_with_gravatar} out of {len(unique_users)} have a Gravatar ID.')


if __name__ == "__main__":
    exp_utils.load_paths_for_all_argv()
    count_gravater_users()
