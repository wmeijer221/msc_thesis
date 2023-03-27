
import dotenv
from os import getenv
import requests
import json

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

    rate = j_response["rate"]

    print(f'Token {index}: used {rate["used"]} of {rate["limit"]} requests.')
