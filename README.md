# Ecosystem-wide experience / collaboration and pull request acceptance.

This repository contains all of the code used to produce the master's thesis work: Willem Meijer. 2023. _The Influence of Ecosystem-Wide Experience and Collaboration on Pull Request Acceptance in Open-Source Software Ecosystems._ Master’s thesis. University of Groningen. [https://fse.studenttheses.ub.rug.nl/31331/](https://fse.studenttheses.ub.rug.nl/31331/).

This repository acts as a _replication package_ to this study, providing little to no explicit information regarding design decisions.
For that type of information and any other unclarities, refer to the paper; specifically the data collection / methodology section.

## Set-up

...

- If you want to store persistent data in a different location than `./data/` (i.e., in the repostory root folder), the environment variable `EXPERIMENT_BASE_PATH` should be set.

## Replication Steps

The following steps are necessary to replicate this study.
You can skip steps in case you have access to raw or processed data.

Some of the steps use multithreaded solutions and allow you to specify the number of used threads. 
This can most commonly be done using the `-t` commandline parameter, such that `-t 4` runs the process with four threads. 
Different scripts make different assumptions about thread usage (specifically `retrieve_pull_requests`  and `retrieve_issues`), so refer to [Repository Contents](#repository-contents) for reference.

_Note that collecting issue and pull request data are long-running processes. It took us multiple months to collect the data for our study._

- Download katz dataset.
- Run `libraries_filter` and delete all non-NPM data.
- Run `pre_sort_filters_mt -m r -t 8 -j` which filters projects using downloads.
- Run `retrieve_pull_requests -f dl -t 3 -a 3` which collects pull request data of the popular projects.

TODO: Continue here. Find a way to filter the project list based on PR count, generate a filter file for that, and intersect that with the `dl` filter file. This should be possible with the `pre_sort_filters` script.

- Run `retrieve_issues -f dl -t 3 -a 3` which collects issue data of the popular projects.

## Repository Contents

All of the used code can be found in [`python_proj`](./python_proj/).
The code is NOT structured chronologically but semantically (sort of).
This section simply provides an overview of "what is where" and "what does what".
Refer to [Replication Steps](#replication-steps) for the chronological replication flow.
When executing any of this code, DON'T rely on the defaults I specified. I won't vouch for them and they are most likely outdated.

### Data Retrieval

- [`retrieve_pull_requests`](./python_proj/data_retrieval/retrieve_pull_requests.py): Retrieves projects from a sample of projects. It implements a couple of relevant filters as well: 1) only GitHub projects, 2) projects with working URL, 3) only non-forks. You can run it in two modes, specified with the `-m` parameter: `r` which simply retrieves data, and `s` which does the same but skips projects of which the data is already received (in case the process is killed; It is super, super slow. We ran it for multiple months). This script assumes that the environment variable `GITHUB_TOKEN_1` is set to a GitHub API key. You can add arbitrarily many (so `GITHUB_TOKEN_2`, `GITHUB_TOKEN_3`, etc.), which speeds up the process but GH might flag the accounts as bots and revoke the API tokens. Specify the number of tokens with the flag `-a`, the default is 3. It can be used multithreaded, and you can specify the number of threads using the `-t` parameter; the default is 1. It's recommended that the number of API keys either equals the number of threads or that it is some multiple of the number of threads (e.g., 2 API keys per thread). It probably works with an unbalanced number, but we didn't use it that way. You need to specify a project filter, which can be done using the flag `-f`, which represents the the filter filename's suffix. Using the output of `pre_sort_filters_mt`, this would be `dl`.
- [`retrieve_issues`](./python_proj/data_retrieval/retrieve_issues.py): Retrieves GitHub issues. It works exactly the same as `retrieve_pull_requests`, so you have to specify a filter `-f`, a number of threads `-t`, and a number of API keys `-a`. You can run the two processes in parallel, but in the end, they would both be waiting due to GitHub's API rate limit.
- [`get_dependency_periphery`](./python_proj/data_retrieval/get_dependency_periphery.py): Generates a list of periphery projects; i.e., given a list of projects as input, it outputs a list of projects that has a dependency on those projects or that those projects depend on. It can also randomly sample a list of projects and take the difference between two sets (i.e., O = A \ B). To use these different functionalities, set the mode `-m`. Respectively to `r`, `s`, or `i`. The output files of these are 

### Data Filters

This folder largely contains code that either filters the projects sampled from, or the development activities that are used in the study.
Of these, `libraries_filter` and `pre_sort_filters_mt` are ran prior to data collection.
The rest is used after data collection.
- [`libraries_filter`](./python_proj/data_filters/libraries_filter.py): Splits the [Katz dataset](https://libraries.io/data/) into separate files for each of the ecosystem included. This is necessary as we only address NPM projects. It also allows us to reduce the storage requirement quite substantially.
- [`pre_sort_filters_mt`](./python_proj/data_filters/pre_sort_filters_mt.py): Filters projects based on their monthly downloads. To work properly, you have to run it with the commandline argument `-m r`, and specify a number of threads you want to use with the parameter `-t`. It will output results per thread, which can be merged together by running it with the flag `-j` as well. This script serves the same purpose as `pre_sort_filters`.
- [`post_sort_filter_everything`](./python_proj/data_filters/post_sort_filter_everything.py): Applies the used project / activity filters on the collected PR / Issue data. It aplies multiple sub-filters that are stored in separate files. These sub-filters are not intended to be executed separately. The commandline parameters written about should therefore be used when executing `post_sort_filter_everything`. This script performs a number of steps: 1) runs `post_sort_filters`, 2) runs `post_sort_filter_for_pr_count`, 3) generates a remaining project list using [`post_sort_filter_for_pr_count`](./python_proj/helpers/create_project_user_list.py), 4) filters issues with the project list, 5) runs `post_sort_filter_for_projects`, 6) it removes invalid data entries, it removes duplicate entries. This script expects a list of CHRONOLOGICAL input PR datasets, which is a comma-separated list of names specified through `--chron_in_pr`. Similarly, it expects a list of comma-separated issue datasets, specified through `--chron_in_issue`. The following are the used sub-filters:
  - [`post_sort_filters`](./python_proj/data_filters/post_sort_filters.py): Implements simple "post-sort" filters (i.e., filters that assume the input data is sorted chronologically), filtering various things. Not all of these are used in this study. The default filters are of config `pcuadgbn`, which applies the following rules: 1) it must be on GitHub, 2) can't be newer than the Katz dataset, 3) can't be a GH bot user, 4) can't be deleted account, 5) can't be a bot according to Dey et al., 2020, 6) can't be a bot according to Golzadeh et al., 2021, 7) can't be a bot according to the custom blacklist, 8) it can't have "[bot]" in its name. To specify the filter mode, use the commandline argument `--filter_mode`.
  - [`post_sort_filter_for_pr_count`](./python_proj/data_filters/post_sort_filter_for_pr_count.py): Filters _pull requests_ (not issues, this is done separately) from projects that have an insufficient number of pull requests. You can specify the minimum number of PRs by using the commandline parameter `--min_prs`. The experiment used 5 PRs.
  - [`post_sort_filter_for_projects`](./python_proj/data_filters/post_sort_filter_for_projects.py): Filters all entries of a chronological input dataset according to a list of projects.

### Data Preprocessing

...

### Modelling

...

### Other Code

The rest of the code is not integral to the study.
It contains a bunch of utility files that implement helper functions.
Of these, [`exp_utils`](./python_proj/utils/exp_utils.py) is the most relevant, specifying storage paths as well as standardized commandline parameters.

### The data folder

The code makes all kinds of assumptions about the used data folder.
By default its root folder is `./data/`, however, this can be changed by setting the `EXPERIMENT_BASE_PATH` environment variable.
