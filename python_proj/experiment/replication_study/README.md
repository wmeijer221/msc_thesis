
# Replication Guide

## Steps
- Download data (v1.6) from [Libraries](libraries.io/data) and store it (unzip it) into ``./data/libraries/`` (don't rename anything).
- Run ``../libraries_filter.py`` which separates NPM projects.
- Run ``retrieve_pull_requests.py`` which retrieves PR data for projects.
- Run ``filter_projects.py`` which applies inclusion criteria on projects.

