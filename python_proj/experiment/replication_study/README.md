
# Replication Guide

Try not to make sense too much of the code. 
It's all over the place and probably unclear, so I suggest just following the steps below.

## General Instructions
In general, it's recommended to execute them using a ``devcontainer`` (that's all they're tested in anyways).
Don't forget to run ``export PYTHONPATH=/workspaces/msc_thesis/`` as the code will probably throw an error without it.
All python filters will have to be ran in the ``/workspaces/msc_thesis/`` folder; i.e., running e.g. ``filter_projects.py`` will be done using ``python3 ./python_proj/experiments/replication_study/filter_projects.py``.
In general, don't delete any of the generated files while running this experiment (unless explicitly stated otherwise in the replication steps instructions).

## Replication Steps
- Download data (v1.6.0 was used in this study) from [libraries.io](libraries.io/data) and store it (unzip it) into ``./data/libraries/`` (don't rename anything).
- Run ``../libraries_filter.py`` which separates NPM projects.
- Run ``faster_filter.py -m r -t 16 -j`` which applies inclusion criteria on projects using downloads.
  Here ``-t`` indicates the number of threads used as multithreading speeds up the process significantly. 
  Using 16 threads might not be the right number for you, though.
  To experiment what works well, use ``faster_filter -m -t -t 1,2,4,8 -c 512`` (where ``-t`` indicates the to-be-tested threads).
  When it's done, this process outputs the rutimes per thread.
- Run ``retrieve_pull_requests.py -f dl -t 2 -m s`` which retrieves PR data for projects matching the prior inclusion criteria.
  Note that the process expects various API keys to be set as environment variables, so check ``.env-example`` for an example of the expected ``.env`` file.
  This process takes a long time to run (multiple days).
  If you want to interrupt it, you can; just make sure the ``-m s`` argument is there when launching, else your progress will be deleted.
  If you do this, though, do make sure to delete the lastly added ``.json`` file(s) in the ``./data/libraries/xxx-libraries-xxx/pull-requests`` folder as it's quite likely the process was killed while extracting data from said file/repository.
  _Note that the ``error.csv``, ``pr-count.csv`` and ``repo-count.csv`` files will no longer be complete when you do this as they're cleared every time you re-run the program (they're not used for anything beyond giving an intuition for the shape of the data, so it doesn't really matter)._
  _Also note that all projects that had 0 PRs in the past will not be skipped as their output files are deleted; rerunning will therefore cost you some extra time still._
- Run ``filter_projects.py -m p`` which applies inclusion criteria on projects using pull request count.
- Run ``filter_projects.py -m m`` which merges the results of the previous two ``filter_projects.py`` runs.
- Run ``retrieve_issues.py`` to retrieve the issues of the selected projects (this can be ran later as well).
- Run ``merge_issue_pr_data.py -d``

- Run ``get_dependency_periphery.py`` to generate two lists of periphery projects identified using dependencies to and from the core projects (those that have been retrieved up until now).
  The output is a list of projects that the core projects depend on, a list of projects that depend on the core projects, and a json document storing the dependencies relevant to this study (as the libraries.io dependency file is too large to conveniently work with).
- Run ``filter_projects.py -m s other_to_focal_without_core 12566`` to subsample the list of projects that depend on the core projects as this list is very, very large.
  The number 12566 (the subsample size) is semi-arbitrary picked.
  It's the number of entries in the ``focal_to_other_without_core`` file, making sure they're equally represented.
  You can change it if you think that's necessary.
- Run ``retrieve_pull_requests.py -f focal_to_other -t 4 -m s`` which retrieves pull request data for the periphery projects that the core depends on.
- Run ``retrieve_pull_requests.py -f other_to_focal_sampled -t 4 -m s`` which retrieves pull requests data for the periphery projects.

- Run ``data_sorter.py -k closed_at -d ./data/libraries/npm-libraries-1.6.0-2020-01-12/predictors/included_projects.csv -e npm -f pull-requests -t 4``
- Run ``data_filters.py -m pdalbc`` to filter data based on platform and pull request close time and whether the user is a bot.
- Run ``demographics.py -i sorted_filtered`` to plot some basic figures describing the data.
- Run ``sliding_window.py`` to generate various datasets.
- Run ``modelling.py`` to generate basic distribution data for the dataset.

