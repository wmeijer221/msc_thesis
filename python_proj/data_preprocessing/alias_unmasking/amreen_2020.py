from dataclasses import dataclass
from typing import Tuple

# Copied jaro-winkler similarity from: https://www.geeksforgeeks.org/jaro-and-jaro-winkler-similarity/
from math import floor

def jaro_distance(s1, s2):

    # If the strings are equal
    if (s1 == s2):
        return 1.0

    # Length of two strings
    len1 = len(s1)
    len2 = len(s2)

    if (len1 == 0 or len2 == 0):
        return 0.0

    # Maximum distance upto which matching
    # is allowed
    max_dist = (max(len(s1), len(s2)) // 2) - 1

    # Count of matches
    match = 0

    # Hash for matches
    hash_s1 = [0] * len(s1)
    hash_s2 = [0] * len(s2)

    # Traverse through the first string
    for i in range(len1):

        # Check if there is any matches
        for j in range(max(0, i - max_dist),
                       min(len2, i + max_dist + 1)):

            # If there is a match
            if (s1[i] == s2[j] and hash_s2[j] == 0):
                hash_s1[i] = 1
                hash_s2[j] = 1
                match += 1
                break

    # If there is no match
    if (match == 0):
        return 0.0

    # Number of transpositions
    t = 0

    point = 0

    # Count number of occurrences
    # where two characters match but
    # there is a third matched character
    # in between the indices
    for i in range(len1):
        if (hash_s1[i]):

            # Find the next matched character
            # in second string
            while (hash_s2[point] == 0):
                point += 1

            if (s1[i] != s2[point]):
                point += 1
                t += 1
            else:
                point += 1

        t /= 2

    # Return the Jaro Similarity
    return ((match / len1 + match / len2 +
            (match - t) / match) / 3.0)

# Jaro Winkler Similarity


def jaro_winkler(s1, s2):

    jaro_dist = jaro_distance(s1, s2)

    # If the jaro Similarity is above a threshold
    if (jaro_dist > 0.7):

        # Find the length of common prefix
        prefix = 0

        for i in range(min(len(s1), len(s2))):

            # If the characters match
            if (s1[i] == s2[i]):
                prefix += 1

            # Else break
            else:
                break

        # Maximum of 4 characters are allowed in prefix
        prefix = min(4, prefix)

        # Calculate jaro winkler Similarity
        jaro_dist += 0.1 * prefix * (1 - jaro_dist)

    return jaro_dist


@dataclass
class Author:
    name: str
    email: str
    first_name: str
    last_name: str
    user_name: str


@dataclass(init=False)
class AuthorSimilarity:
    author_a: Author
    author_b: Author

    name: float
    email: float
    first_name: float
    last_name: float
    user_name: float
    inverse_first_name: float

    def __init__(self, author_a: Author, author_b: Author) -> None:
        self.author_a = author_a
        self.author_b = author_b
        self.name = jaro_winkler(author_a.name, author_b.name)
        self.email = jaro_winkler(author_a.email, author_b.email)
        self.first_name = jaro_winkler(
            author_a.first_name, author_b.first_name)
        self.last_name = jaro_winkler(author_a.last_name, author_b.last_name)
        self.user_name = jaro_winkler(author_a.user_name, author_b.user_name)
        self.inverse_first_name = jaro_winkler(
            author_a.first_name, author_b.last_name)


def get_first_and_last_name(author: str) -> Tuple[str, str]:
    first_name = author
    last_name = author
    for index, letter in enumerate(author):
        if letter in ["+", "-", "_", ",", "."]:
            last_name = author[index + 1:]
            if not first_name:
                first_name = author[:index]
        elif letter.isupper():
            last_name = author[index:]
            if not first_name:
                first_name = author[:index]
    return (first_name.strip(), last_name.strip())


def extract_name_attributes_from_author(author: str) -> Author:
    name = author.split("<")[0].strip()
    email = author.split("<")[1].split(">")[0].strip()
    first_name, last_name = get_first_and_last_name(name)
    user_name = email.split("@")[0].strip()
    return Author(name, email, first_name, last_name, user_name)


def generate_author_list(input_file_path: str) -> list[Author]:
    with open(input_file_path, "r") as input_file:
        authors = [extract_name_attributes_from_author(line.strip())
                   for line in input_file]
        return list(authors)


if __name__ == "__main__":
    author_a = extract_name_attributes_from_author(
        "John Hopkins <j.hopkins@hospitals.com>")
    author_b = extract_name_attributes_from_author(
        "J.H. Hopkins <hopkins@jh.hospitals.com>")
    similarities = AuthorSimilarity(author_a, author_b)
    print(f'{similarities=}')
