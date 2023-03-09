import json
from os import getenv
import dotenv

from perceval.backends.core.github import GitHub, CATEGORY_PULL_REQUEST, CATEGORY_ISSUE
from watchdog.events import FileSystemEventHandler, FileClosedEvent
from watchdog.observers import Observer

dotenv.load_dotenv()
github_token = getenv("GITHUB_TOKEN")
github_token_2 = getenv("GITHUB_TOKEN_2")


class NewNPMProjHandler(FileSystemEventHandler):
    def __init__(self, output_path: str):
        self.output_path = output_path

    def on_closed(self, event: FileClosedEvent):
        src_path = event.src_path

        with open(src_path, "r", encoding="utf-8") as input_file:
            entry = json.loads(input_file.read())
            print('Getting PRs and issues for {name}'.format(name=entry['id']))
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
        # TODO: filter using this: curl https://api.github.com/repos/OWNER/REPO/pulls | jq length this will save a lot of time.
        try:
            output_path = self.output_path.format(type="pr", name=entry["id"])

            with open(output_path, "w+", encoding="utf-8") as output_file:

                for count, pr in enumerate(repo.fetch(category=CATEGORY_PULL_REQUEST)):
                    output_file.write(json.dumps(pr) + "\n")

                print("Collected {count} PRs for {name}.".format(
                    name=entry['id'], count=count))
        except:
            print("Could not get PRs for {name}.".format(name=entry['id']))

    def grab_issues(self, entry: str, repo: GitHub):
        try:
            output_path = self.output_path.format(
                type="issue", name=entry["id"])
            with open(output_path, "w+", encoding="utf-8") as output_file:

                for count, issue in enumerate(repo.fetch(category=CATEGORY_ISSUE)):
                    output_file.write(json.dumps(issue) + "\n")

            print("Collected {count} issues for {name}.".format(
                name=entry['id'], count=count))
        except:
            print("Could not get issues for {name}.".format(name=entry['id']))


print("Starting with PR/issue collecting.")

watch_path = "./data/npm/"
output_path = "./data/{type}/{name}.json"

proj_handler = NewNPMProjHandler(output_path)
observer = Observer()
observer.schedule(proj_handler, path=watch_path, recursive=False)
observer.start()

while True:
    try:
        pass
    except KeyboardInterrupt:
        observer.stop()
