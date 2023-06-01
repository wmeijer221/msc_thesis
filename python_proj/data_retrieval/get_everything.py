"""
Merges the ``retrieve_pull_requests``, ``retrieve_issues``,
and ``get_closed_by_data`` scripts into one.
"""

from subprocess import Popen

from python_proj.utils.arg_utils import *
from python_proj.utils.exp_utils import get_file_name


def get_all(filter_type: str):
    # print(f'Starting with PRs for: {filter_type}.')
    # pr_argv = ["python3", "./python_proj/data_retrieval/retrieve_pull_requests.py",
    #            "-m", "s",
    #            "-t", "3",
    #            "-f", filter_type]
    # try:
    #     Popen(pr_argv).wait()
    # except:
    #     print("FAILED")
    #     return 
    
    print(f'Starting with issues for: {filter_type}.')
    iss_argv = ["python3", "./python_proj/data_retrieval/retrieve_issues.py",
                "-a", "3",
                '-t', "3",
                "-f", f'_{filter_type}']
    try:
        Popen(iss_argv).wait()
    except:
        print("FAILED")
        return 
    
    print(f'Starting to merge PRs and issues for: {filter_type}.')
    merge_argv = ["python3" "./python_proj/data_preprocessing/merge_issue_pr_data.py",
                  "-d", "-w",
                  "-f", f'_{filter_type}']
    try:
        Popen(merge_argv).wait()
    except:
        print("FAILED")
        return 
    
    print("Done!")


if __name__ == "__main__":
    filter_name = get_file_name()
    get_all(filter_name)
