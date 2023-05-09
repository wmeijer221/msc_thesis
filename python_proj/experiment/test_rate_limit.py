"""
Tests the current status of the GitHub API tokens;
i.e., how many requests they can make in total and 
how many they have left.
"""

import dotenv
from os import getenv
import requests
import json


def test_progress():
    dotenv.load_dotenv()

    all_gh_tokens = [getenv(f"GITHUB_TOKEN_{i}") for i in range(1, 21)]

    for index, token in enumerate(all_gh_tokens, start=1):
        url = "https://api.github.com/rate_limit"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f'Bearer {token}',
            "X-GitHub-Api-Version": "2022-11-28"
        }

        response = requests.get(url, headers=headers)
        j_response = json.loads(response.text)
        try:
            rate = j_response["rate"]

            print(
                f'Token {index}: used {rate["used"]} of {rate["limit"]} requests.')
        except KeyError:
            print(f"Token {index} is invalid.")

if __name__ == "__main__":
    test_progress()
