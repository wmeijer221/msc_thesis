import json
from os import getenv
import dotenv
import traceback
from time import sleep
from requests import HTTPError

from perceval.backends.core.github import GitHub, CATEGORY_PULL_REQUEST, CATEGORY_ISSUE
from watchdog.events import FileSystemEventHandler, FileClosedEvent
from watchdog.observers import Observer

from filters.gl_github_filters import IssueFilter, PullFilter

dotenv.load_dotenv()
github_token = getenv("GITHUB_TOKEN")
github_token_2 = getenv("GITHUB_TOKEN_2")

exception_output_file = open(
    "./data/col_exceptions.out", "a+", encoding="utf-8")


class NewNPMProjHandler(FileSystemEventHandler):
    def __init__(self, output_path: str):
        self.output_path = output_path

    def on_closed(self, event: FileClosedEvent):
        src_path = event.src_path

        with open(src_path, "r", encoding="utf-8") as input_file:
            entry = json.loads(input_file.read())
            print('\nGetting PRs and issues for {name}'.format(
                name=entry['id']))
            repo = self.make_repo(entry)
            self.grab_pull_requests(entry, repo)
            self.grab_issues(entry, repo)

    def make_repo(self, package) -> GitHub:
        if package['repo_type'] is None \
                or package['repo_type'] != 'git':
            return None

        (owner, repo) = package['repo_url'].split("/")[3:5]
        repo = repo.split(".")[0]

        repo: GitHub = GitHub(owner=owner, repository=repo,
                              api_token=[github_token, github_token_2], sleep_for_rate=True)

        return repo

    def grab_pull_requests(self, entry: str, repo: GitHub):
        # TODO: Filter PR results; currently way too much is stored.
        try:
            output_path = self.output_path.format(type="pr", name=entry["id"])

            with open(output_path, "w+", encoding="utf-8") as output_file:
                
                pr_count = 0
                pr_filter = PullFilter()
                for count, pr in enumerate(repo.fetch(category=CATEGORY_PULL_REQUEST)):
                    filtered_pr = pr_filter.filter(pr["data"])
                    output_file.write(json.dumps(pr) + "\n")
                    pr_count = count

                print("Collected {count} PRs for {name}.".format(
                    name=entry['id'], count=pr_count))
        except HTTPError as herr:
            if herr.response.status_code == 404:
                print("Couldn't get PRs because repo for {name} doesn't exist.".format(
                    name=entry['id']))
        except Exception as e:
            print("Could not get PRs for {name}.".format(name=entry['id']))
            exception_output_file.write(
                '\n\nPR failure for {name}'.format(name=entry['id']))
            traceback.print_exc(file=exception_output_file)
            exception_output_file.flush()

    def grab_issues(self, entry: str, repo: GitHub):
        # TODO: Filter Issue results; currently way too much is stored.
        try:
            issue_filter = IssueFilter()
            output_path = self.output_path.format(
                type="issue", name=entry["id"])
            with open(output_path, "w+", encoding="utf-8") as output_file:
                iss_count = 0
                for count, issue in enumerate(repo.fetch(category=CATEGORY_ISSUE)):
                    filtered_issue = issue_filter.filter(issue["data"])
                    output_file.write(json.dumps(issue) + "\n")
                    iss_count = count

            print("Collected {count} issues for {name}.".format(
                name=entry['id'], count=iss_count))
        except HTTPError as herr:
            if herr.response.status_code == 404:
                print("Couldn't get issues because repo for {name} doesn't exist.".format(
                    name=entry['id']))
        except Exception as e:
            print("Could not get issues for {name}.".format(name=entry['id']))
            exception_output_file.write(
                '\n\nIssue failure for {name}'.format(name=entry['id']))
            traceback.print_exc(file=exception_output_file)
            exception_output_file.flush()


print("Starting with PR/issue collecting.")

watch_path = "./data/npm/"
output_path = "./data/{type}/{name}.json"


proj_handler = NewNPMProjHandler(output_path)
observer = Observer()
observer.schedule(proj_handler, path=watch_path, recursive=False)
observer.start()

is_running = True
while is_running:
    try:
        sleep(1)
    except KeyboardInterrupt:
        print("Stopping because I was interrupted...")
        is_running = False
        observer.stop()
        exception_output_file.close()
