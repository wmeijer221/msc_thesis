
# Replication Guide

Try not to make sense too much of the code. 
It's all over the place and probably unclear, so I suggest just following the steps below.

In general, it's recommended to execute them using a ``devcontainer`` (that's all they're tested in anyways).
Don't forget to run ``export PYTHONPATH=/workspaces/msc_thesis/`` as the code will probably throw an error without it.
All python filters will have to be ran in the ``/workspaces/msc_thesis/`` folder; i.e., running e.g. ``filter_projects.py`` will be done using ``python3 ./python_proj/experiments/replication_study/filter_projects.py``.

## Steps
- Download data (v1.6) from [Libraries](libraries.io/data) and store it (unzip it) into ``./data/libraries/`` (don't rename anything).
- Run ``../libraries_filter.py`` which separates NPM projects.
- Run ``filter_projects.py -m d`` which applies inclusion criteria on projects using downloads.
- Run ``retrieve_pull_requests.py`` which retrieves PR data for projects matching the prior inclusion criteria.
- Run ``filter_projects.py -m p`` which applies inclusion criteria on projects using pull request count.

