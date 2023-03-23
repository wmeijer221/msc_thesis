def safe_index(list: list, entry: object) -> int:
    try:
        return list.index(entry)
    except ValueError:
        return -1
