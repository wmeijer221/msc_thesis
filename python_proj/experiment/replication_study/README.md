
# Replication Guide

Try not to make sense too much of the code. 
It's all over the place and probably unclear, so I suggest just following the steps below.

In general, it's recommended to execute them using a ``devcontainer`` (that's all they're tested in anyways).
Don't forget to run ``export PYTHONPATH=/workspaces/msc_thesis/`` as the code will probably throw an error without it.
All python filters will have to be ran in the ``/workspaces/msc_thesis/`` folder; i.e., running e.g. ``filter_projects.py`` will be done using ``python3 ./python_proj/experiments/replication_study/filter_projects.py``.

## Steps
- Download data (v1.6.0) from [Libraries](libraries.io/data) and store it (unzip it) into ``./data/libraries/`` (don't rename anything).
- Run ``../libraries_filter.py`` which separates NPM projects.
- Run ``filter_projects.py -m d`` which applies inclusion criteria on projects using downloads.
- Run ``retrieve_pull_requests.py`` which retrieves PR data for projects matching the prior inclusion criteria.
  This process takes a long time to run (multiple days), therefore, if you want to interrupt the process and restart it later, run it as ``retrieve_pull_requests.py -m s`` the next time; this will make it skip already processed repositories.
  If you do this, do make sure to delete the lastly added ``.json`` file in the ``./data/libraries/xxx-libraries/pull-requests`` folder as it's quite likely the process was killed whilst extracting data from said file/repository.
  _Note that the ``error.csv``, ``pr-count.csv`` and ``repo-count.csv`` files will no longer be complete when you do this as they're cleared every time you re-run the program._
- Run ``filter_projects.py -m p`` which applies inclusion criteria on projects using pull request count.
