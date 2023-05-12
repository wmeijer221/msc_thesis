
# Replication Guide

Try not to make sense too much of the code. 
It's all over the place and probably unclear, so I suggest just following the steps below.

## General Instructions
In general, it's recommended to execute them using a ``devcontainer`` (that's all they're tested in anyways).
Don't forget to run ``export PYTHONPATH=/workspaces/msc_thesis/`` as the code will probably throw an error without it.
All python filters will have to be ran in the ``/workspaces/msc_thesis/`` folder; i.e., running e.g. ``pre_sort_filters.py`` will be done using ``python3 ./python_proj/experiments/replication_study/pre_sort_filters.py``.
In general, don't delete any of the generated files while running this experiment (unless explicitly stated otherwise in the replication steps instructions).

## Replication Steps

To replicate the study, follow these steps.
For details on what each script does, please refer to the respective script.
Some of the variables passed as command line arguments can be changed according to your needs (e.g., the number of used API keys and threads.)

### Stage 1: Collecting Core Projects

This stage filters the libraries.io dataset using part of the inclusion criteria, collects the PR and issue data for the selected projects, filters these projects based on different inclusion criteria, and stores their outcomes in separate ``json`` files.

1. Download data (v1.6.0 was used in this study) from [libraries.io](libraries.io/data) and store it (unzip it) into ``./data/libraries/`` (don't rename anything).
2. Run ``../libraries_filter.py`` which separates NPM projects.
3. Run ``pre_sort_filters_mt.py -m r -t 16 -j`` which applies inclusion criteria on projects using downloads.
4. Run ``retrieve_pull_requests.py -f dl -t 3 -m s`` which retrieves PR data for projects matching the prior inclusion criteria. Put your GitHub API keys in ``.env`` as described in ``.env-example``. Interrupting the process will most likely cause half-finished output files.
5. Run ``pre_sort_filters.py -m p`` which applies inclusion criteria on projects using minimum pull request count (5).
6. Run ``pre_sort_filters.py -m m`` which merges the results of the previous two ``pre_sort_filters.py`` runs.
7. Run ``retrieve_issues.py`` to retrieve the issues of the selected projects using the filter list of the previous step.
8. Run ``merge_issue_pr_data.py -d``, which merges the PR and issue data of corresponding entries and removes all of these PR-issues from the list of issues (in GitHub, a PR is simply an issue with extra fields, but the standard issue fields are not pulled with GrimoireLab by default). If a PR has no corresponding issue (which happens for magical reasons), it is removed from the data set.

### Stage 2: Collecting Periphery Projects

This stage selects periphery projects using the projects selected in stage 1.
It identifies the dependencies of these projects and pulls the PR and issue data of these projects, and filters these using the same methods as in stage 1.

1. Run ``get_dependency_periphery.py`` to generate two lists of periphery projects identified using dependencies to and from the core projects (those that have been retrieved up until now).
  The output is a list of projects that the core projects depend on, a list of projects that depend on the core projects, and a json document storing the dependencies relevant to this study (as the libraries.io dependency file is too large to conveniently work with).
2. Run ``pre_sort_filters.py -m s other_to_focal_without_core 12566`` to subsample the list of projects that depend on the core projects as this list is very, very large. The sample size 12566 is picked because that's the size of ``focal_to_other_without_core`` dependency list.
3. Run ``retrieve_pull_requests.py -f focal_to_other -t 4 -m s`` which retrieves pull request data for the periphery projects that the core depends on.
4. Run ``retrieve_pull_requests.py -f other_to_focal_sampled -t 4 -m s`` which retrieves pull requests data for the periphery projects.
5. Run ``retrieve_issues.py -f _other_to_focal_sampled -t 3``

5. Run ``data_sorter.py -k closed_at -d ./data/libraries/npm-libraries-1.6.0-2020-01-12/predictors/included_projects.csv -e npm -f pull-requests -t 4``
- Run ``post_sort_filters.py -i ./data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/sorted.json -o ./data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/sorted_filtered.json -m pcuadgb`` to filter data based on platform and pull request close time and whether the user is a bot or a deleted account.

### Stage 3: Data processing and Modeling

- Run ``demographics.py -i sorted_filtered`` to plot some basic figures describing the data.
- Run ``sliding_window.py`` to generate various datasets.
- Run ``modelling.py`` to generate basic distribution data for the dataset.
