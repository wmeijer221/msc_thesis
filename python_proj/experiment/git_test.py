import os
import json
import logging

from dotenv import load_dotenv
from perceval.backends.core.github import GitHub, CATEGORY_PULL_REQUEST, CATEGORY_ISSUE, CATEGORY_REPO


logging.basicConfig(level=logging.DEBUG)

ISSUE_ARCHIVE_PATH = os.path.abspath("./data/is_{project}")
PR_ARCHIVE_PATH = os.path.abspath("./data/pr_{project}")
PROJ_PATH = os.path.abspath("./config/projectlist.txt")

def load_repolist() -> list[str]:
    with open(PROJ_PATH, "r", encoding="utf-8") as input_file: 
        repolist = [repo.strip() 
                    for repo in input_file.read().split("\n") 
                    if repo.strip() != ""]
    return repolist

def pull_repos(repos: list[str]):
    token = os.getenv("GITHUB_TOKEN")
    for repo in repos:
        retrieve_repo(repo, token)

def retrieve_repo(repo: str, token: str):
    (owner, project) = repo.split("/")
    repo: GitHub = GitHub(owner=owner, repository=project, 
                          api_token=[token], sleep_for_rate=True)
    # retrieve_and_store(
    #     repo = repo,
    #     category = CATEGORY_PULL_REQUEST,
    #     archive_path = os.path.abspath(f"./data/pr_{project}.json")
    # )
    # retrieve_and_store(
    #     repo,
    #     category=CATEGORY_ISSUE,
    #     archive_path= os.path.abspath(f"./data/is_{project}.json")
    # )
    # retrieve_and_store(
    #     repo,
    #     category=CATEGORY_REPO,
    #     archive_path= os.path.abspath(f"./rp_{project}.json")
    # )

def retrieve_and_store(repo: GitHub, category: str, archive_path: str):
    with open(archive_path, "w+", encoding="utf-8") as archive_file:
        for item in repo.fetch(category=CATEGORY_PULL_REQUEST):
            archive_file.write(json.dumps(item))

if __name__ == "__main__":
    load_dotenv()
    repos = load_repolist()
    pull_repos(repos)
