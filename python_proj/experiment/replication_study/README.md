
# Replication Guide

Try not to make sense too much of the code. 
It's all over the place and probably unclear, so I suggest just following the steps below.

## General Instructions
In general, it's recommended to execute them using a ``devcontainer`` (that's all they're tested in anyways).
Don't forget to run ``export PYTHONPATH=/workspaces/msc_thesis/`` as the code will probably throw an error without it.
All python filters will have to be ran in the ``/workspaces/msc_thesis/`` folder; i.e., running e.g. ``filter_projects.py`` will be done using ``python3 ./python_proj/experiments/replication_study/filter_projects.py``.
In general, don't delete any of the generated files while running this experiment (unless explicitly stated otherwise in the replication steps instructions).

## Replication Steps
- Download data (v1.6.0) from [libraries.io](libraries.io/data) and store it (unzip it) into ``./data/libraries/`` (don't rename anything).
- Run ``../libraries_filter.py`` which separates NPM projects.
- Run ``filter_projects.py -m d`` which applies inclusion criteria on projects using downloads.
- Run ``retrieve_pull_requests.py`` which retrieves PR data for projects matching the prior inclusion criteria.
  This process takes a long time to run (multiple days), therefore, if you want to interrupt the process and restart it later, run it as ``retrieve_pull_requests.py -m s`` the next time; this will make it skip already processed repositories.
  If you do this, though, do make sure to delete the lastly added ``.json`` file in the ``./data/libraries/xxx-libraries-xxx/pull-requests`` folder as it's quite likely the process was killed while extracting data from said file/repository.
  _Note that the ``error.csv``, ``pr-count.csv`` and ``repo-count.csv`` files will no longer be complete when you do this as they're cleared every time you re-run the program (they're not used for anything beyond giving an intuition for the shape of the data, so it doesn't really matter)._
  _Also note that all projects that had 0 PRs in the past will not be skipped as their output files are deleted; rerunning will therefore cost you some extra time still._
- Run ``filter_projects.py -m p`` which applies inclusion criteria on projects using pull request count.
- Run ``filter_projects.py -m m`` which merges the results of the previous two ``filter_projects.py`` runs.
