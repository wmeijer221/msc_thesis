# Ecosystem-wide experience / collaboration and pull request acceptance.

This repository contains all of the code used to produce the master's thesis work: Willem Meijer. 2023. _The Influence of Ecosystem-Wide Experience and Collaboration on Pull Request Acceptance in Open-Source Software Ecosystems._ Master’s thesis. University of Groningen. [https://fse.studenttheses.ub.rug.nl/31331/](https://fse.studenttheses.ub.rug.nl/31331/).

This repository acts as a _replication package_ to this study, providing little to no explicit information regarding design decisions.
For that type of information and any other unclarities, refer to the paper; specifically the data collection / methodology section.
Figure 1 in the thesis provides a high-level overview of the data collection process, which might help contextualize the different replication steps / scripts in this repository.


## Contents

- [Ecosystem-wide experience / collaboration and pull request acceptance.](#ecosystem-wide-experience--collaboration-and-pull-request-acceptance)
  - [Contents](#contents)
  - [Notable Terminology Differences](#notable-terminology-differences)
  - [Installation and set-up](#installation-and-set-up)
    - [Preliminary data](#preliminary-data)
  - [Replication Steps](#replication-steps)
    - [Raw Data Retrieval](#raw-data-retrieval)
    - [Data Parsing](#data-parsing)
    - [Dataset Generation](#dataset-generation)
    - [Modelling](#modelling)
  - [Repository Contents](#repository-contents)
    - [Data Retrieval](#data-retrieval)
    - [Data Filters](#data-filters)
    - [Data Preprocessing](#data-preprocessing)
    - [Modelling](#modelling-1)
    - [Other Code](#other-code)
    - [The data folder](#the-data-folder)

## Notable Terminology Differences

In a number of cases does the terminology used in the papers differ from the terminology used in this code.
This is due to the co-evolution of both ends, which was not entirely synchronous; i.e., the terminology might have changed in the text long after the code was written.
This holds for the following terms (this list might not be exhaustive):

- _Second-order degree centrality:_ For the most part, the code refers to _first-order degree centrality_. This has been renamed in the paper because it's simply the incorrect term. It has been to _second-order degree centrality_, which is accurate. The thesis does still use the old term.
- _Downstream dependencies:_ This term has been updated twice. In the code, it's referred to as _dependencies_ (e.g., `DependencyEcosystemExperience`), in the thesis it's referred to as _incoming dependencies_ (or _in-dependencies_), and in the paper it's referred to as _downstream dependencies_. The first update was simply for clarity, and the second to conform with professional jargon. Developer experience of this kind refers to the experience acquired in projects that implement the focal project.
- _Upstream dependencies:_ This term was updated in the same fashion and for the same reasons as upstream dependencies. In the code, it is called _reverse dependencies_ (e.g., `InverseDependencyEcosystemExperience`), in the thesis it's referred to as _outgoing dependencies_, and in the paper as _upstream dependencies_. Developer experience of this kind refers to the experience acquired in projects that are implemented by the focal project.

The code has NOT been fully updated to reflect these changes in an attempt to avoid accidental errors.
Therefore, take the differences in terminology in mind when interpreting the results.

## Installation and set-up

Before trying anything in this project, you should do the following:

- All of the experiments were ran using `python 3.11-bullseye`, and used this inside a VS Code `devcontainer`. In case you want to run the notebooks some version of Jupyter notebooks should be installed, we used Client version `8.2.0`.
- If you want to store persistent data in a different location than `./data/` (i.e., in the repostory root folder), the environment variable `EXPERIMENT_BASE_PATH` should be set.
- Usually, when pulling the repository, the `PYTHONPATH` variable isn't set properly. Make sure to update this by installing the project in a container and setting it on startup (like we did), by configuring your venv, or simply by overwriting the variable on your machine (though, this will probably break other projects).
- Make sure to install the Python requirements prior to running any code, by using `pip install -r ./python_proj/requirements.txt`.

### Preliminary data

This experiment depends, in part, on the data of others.
You need this data for the [data retrieval](#data-retrieval) and [data preprocessing](#data-preprocessing) steps.
You don't need them for the [modelling](#modelling) steps.

- Download [Katz dataset](https://doi.org/10.5281/zenodo.3626071) and extract it into the `./data/libraries/` folder.
- Download the [Golzadeh bot dataset](https://zenodo.org/records/4000388) and extract it at `./data/bot_data/`, s.t. the folder contains the `.csv` file.
- Download the [Dey bot dataset](https://zenodo.org/records/3694401) and extract it at `./data/bot_data/`.
- Run `./helpers/filter_dey_2019_botlist.py` which extracts the bot IDs from Dey's dataset into a much smaller `.json` file.
- Run `libraries_filter.py` and delete all non-NPM data.

## Replication Steps

The following steps are necessary to replicate this study.
You can skip steps in case you have access to raw or processed data.


Some of the steps use multithreaded solutions and allow you to specify the number of used threads. 
This can most commonly be done using the `-t` commandline parameter, such that `-t 4` runs the process with four threads. 
Different scripts make different assumptions about thread usage (specifically `retrieve_pull_requests`  and `retrieve_issues`), so refer to [Repository Contents](#repository-contents) for reference.

Note that collecting issue and pull request data are long-running processes.
It took us multiple months to collect the data for our study.
Related to that, the data collection process was much less structured than the following steps suggest and each of the scripts was updated through the entire period.
Consequently, there is a possibiblity that the itinerary does not perfectly reflect the process.
However, we feel confident that the steps approximate it closely enough to be representative for our work.

Make sure you have a sufficient amount of storage available as the raw data and the Katz dataset, commbined use a substantial amount of storage.
Anything over 300GB should work, but we recommend more.
If you want to preserve storage, make sure to delete the Katz dataset after you have extracted all of the NPM data with `libraries_filter.py`.
For reference, we initially used a 100GB drive, which didn't work, and then swapped to a 4TB drive, which did.
The compute node used a 32 core CPU and +-230 GB RAM.


### Raw Data Retrieval

- Run `pre_sort_filters_mt.py -m r -t 8 -j` which filters projects using downloads.
- Run `retrieve_pull_requests.py -f dl -t 3 -a 3` which collects pull request data of the popular projects.
- Run `pre_sort_filters.py -m p -pr 5` which generates a list of projects with sufficient pull requests.
- Run `retrieve_issues.py -f pr -t 3 -a 3` which collects issue data of the popular projects.
- Run `pre_sort_filters.py -m m` which intersects the `pr` and `dl` project lists. Alternatively, you could rename the `pr` file as that's a strict subset of the `dl` file.
- Run `get_dependency_periphery.py -r` which generates two lists, one for incoming dependencies and one for outgoing dependencies. It also removes the popular projects (i.e., those that were downloaded before) from these lists.
- Run `get_dependency_periphery.py -m r -s 26376 -q other_to_focal_without_core` which performs a random subsample of the incoming dependency projects. _Doing this cannot not guarantee that you get exactly the same dataset (both, in terms of the number of projects and the exact projects)._ The original experiment also performed this sampling strategy in two steps; first, sampling the exact same number of projects to the outgoing dependencies, and second, accounting for the difference in valid projects. These results were later merged into one. Although we did not seed the random selection, the inclusion lists have been made available in the replication data package.
- Run `rn ./data/libraries/npm-libraries-1.6.0-2020-01-12/predictors/included_projects_other_to_focal_without_core.csv.tmp ./data/libraries/npm-libraries-1.6.0-2020-01-12/predictors/included_projects_other_to_focal_without_core_subsampled.csv` to make the output file usable by the next script.
- Run `retrieve_pull_requests.py -f other_to_focal_without_core_subsampled -t 3 -a 3` which collects pull request data of the incoming dependency projects. (note, you could filter the output of this again based on PRs like was done in the first data collection step, however, collecting this data is substantially faster, for which we deemed it unnecessary.)
- Run `retrieve_issues.py -f other_to_focal_without_core_subsampled -t 3 -a 3` which collects issue data of the incoming dependency projects.
- Run `retrieve_pull_requests.py -f focal_to_other_without_core -t 3 -a 3` which collects pull request data of the outgoing dependency projects.
- Run `retrieve_issues.py -f focal_to_other_without_core -t 3 -a 3` which collects issue data of the outgoing dependency projects. 

The output of this process will be a database of over 20K GitHub projects (we had data for over 40K projects, many of which did not pass inclusion criteria), each of which has two respective `.json` files somewhere in the `./data/` folder storing the issues and pull request data.

### Data Parsing

- Run `pre_sort_filters.py -m mc pr other_to_focal_without_core_subsampled temp` to merge inclusion lists.
- Run `pre_sort_filters.py -m mc focal_to_other_without_core temp merged` to merge inclusion lists a little more.
- Run `merge_issue_pr_data.py -d -w -f merged` which adds issue data to pull requests, and removes these issues to prevent double counting them during the analysis. This creates new data files and removes old ones. If you don't want old data to be removed, don't use the `-d` flag.
- Run `data_sorter.py -t 16 -q merged -d pull-requests -k closed_at -x --with-issue-data`to sort all of the pull request data into one file sorted by closing date.
- Run `data_sorter.py -t 16 -q merged -d issues -k closed_at -x --no-prs` to sort all of the issue data into one file sorted by closing date.
- Run `post_sort_filter_everything.py --chron_in_pr sorted --chron_in_issue sorted --filter_mode pcuadgbn --min_prs 5 --tag filtered`: to apply the final few inclusion criteria onto the collected data. The data is outputted into a (still chronological) file `sorted_filtered_min_5_prs_no_dupes`.
- Run `sliding_window_2.py -m r -pd sorted_filtered_min_5_prs_no_dupes -id sorted_filtered_min_5_prs_no_dupes` which removes invalid entries from the datasets, outputting them in separate `sorted_filtered_min_5_prs_no_dupes_no_invalid` files.

The output of this will be two data files, both called `sorted_filtered_min_5_prs_no_dupes_no_invalid.csv` in the `pull-requests` and `issues` folders, containing all of the data that is used for inference.

### Dataset Generation

- Run `sliding_window_2.py -m s -pd sorted_filtered_min_5_prs_no_dupes_no_invalid -id sorted_filtered_min_5_prs_no_dupes_no_invalid -o ftc_data -w 90` which generates a dataset that only contains the independent variable "is first time contributor". This is done separately as `sliding_window_3` is multithreaded and can't calculate this correctly. It stores the output at `ftc_data.csv`.
- Run `sliding_window_3.py -pd sorted_filtered_min_5_prs_no_dupes_no_invalid -id sorted_filtered_min_5_prs_no_dupes_no_invalid -o non_ftc_data -w 90 -t 8` which generates the rest of the features multithreadedly (this is quite memory intensive, so you probably can't just max out the number of threads). The generated dataset is stored at `non_ftc_data.csv`.

The output of this is two datasets `ftc_data.csv` and `non_ftc_data.csv`, which are input for the data modelling / inference process.

### Modelling

Each of the modelling scripts can be found in the `/modelling/notebooks` folder.
Run the preprocessing steps in the following order: 
- `feature_construction.ipynb` which constructs the `IsFirstTimeContributor`, `SecondDegreeCentrality`, and `LinkIntensity` fields.
- `subsampling.ipynb` which subsamples the PRs based on project size.
- `feature_transformation.ipynb` which applies log-transform and feature scaling.

Afterwards, each of the analysis scripts contained in the `random_forest` and `logistic_regression` folders can be ran in any order.
To then generate the feature importance plots, run `feature_importance`, which is located in the `random_forest` folder.

Alternatively, you can run `run_all_notebooks.py` which runs all of the above as plain Python code by transpiling the notebooks and executing them.
The output of each file is not contained in the `.ipynb` file, however, is stored in an `.out` file that's automatically generated.

## Repository Contents

All of the used code can be found in [`python_proj`](./python_proj/).
The code is NOT structured chronologically but semantically (sort of).
This section simply provides an overview of "what is where" and "what does what" of the most important files.
There are more scripts in the repository, but they are not relevant to understanding this repository and served an auxiliary purpose at some point.

Refer to [Replication Steps](#replication-steps) for the chronological replication flow.

When executing any of this code, DON'T rely on the defaults we specified.
We won't vouch for them and they are most likely outdated.

### Data Retrieval

- [`retrieve_pull_requests`](./python_proj/data_retrieval/retrieve_pull_requests.py): Retrieves projects from a sample of projects. It implements a couple of relevant filters as well: 1) only GitHub projects, 2) projects with working URL, 3) only non-forks. You can run it in two modes, specified with the `-m` parameter: `r` which simply retrieves data, and `s` which does the same but skips projects of which the data is already received (in case the process is killed; It is super, super slow. We ran it for multiple months). This script assumes that the environment variable `GITHUB_TOKEN_1` is set to a GitHub API key. You can add arbitrarily many (so `GITHUB_TOKEN_2`, `GITHUB_TOKEN_3`, etc.), which speeds up the process but GH might flag the accounts as bots and revoke the API tokens. Specify the number of tokens with the flag `-a`, the default is 3. It can be used multithreaded, and you can specify the number of threads using the `-t` parameter; the default is 1. It's recommended that the number of API keys either equals the number of threads or that it is some multiple of the number of threads (e.g., 2 API keys per thread). It probably works with an unbalanced number, but we didn't use it that way. You need to specify a project filter, which can be done using the flag `-f`, which represents the the filter filename's suffix. Using the output of `pre_sort_filters_mt`, this would be `dl`.
- [`retrieve_issues`](./python_proj/data_retrieval/retrieve_issues.py): Retrieves GitHub issues. It works exactly the same as `retrieve_pull_requests`, so you have to specify a filter `-f`, a number of threads `-t`, and a number of API keys `-a`. You can run the two processes in parallel, but in the end, they would both be waiting due to GitHub's API rate limit.
- [`get_dependency_periphery`](./python_proj/data_retrieval/get_dependency_periphery.py): Generates a list of periphery projects; i.e., given a list of projects as input, it outputs a list of projects that has a dependency on those projects or that those projects depend on. It can also randomly sample a list of projects and take the difference between two sets (i.e., O = A \ B). To use these different functionalities, set the mode `-m`. Respectively to `r`, `s`, or `i`. It outputs two sets of project names `focal_to_other` and `other_to_focal`, specifying the direction of the dependency. When using `-m r` it will remove the 'default' project list (generally the popular projects), outputting another two project files with the suffix `_without_core` added to their previous suffix; e.g., `other_to_focal_without_core`.

### Data Filters

This folder largely contains code that either filters the projects sampled from, or the development activities that are used in the study.
Of these, `libraries_filter` and `pre_sort_filters_mt` are ran prior to data collection.
The rest is used after data collection.
- [`libraries_filter`](./python_proj/data_filters/libraries_filter.py): Splits the [Katz dataset](https://libraries.io/data/) into separate files for each of the ecosystem included. This is necessary as we only address NPM projects. It also allows us to reduce the storage requirement quite substantially.
- [`pre_sort_filters_mt`](./python_proj/data_filters/pre_sort_filters_mt.py): Filters projects based on their monthly downloads. To work properly, you have to run it with the commandline argument `-m r`, and specify a number of threads you want to use with the parameter `-t`. It will output results per thread, which can be merged together by running it with the flag `-j` as well.
- [`pre_sort_filters`](./python_proj/data_filters/pre_sort_filters.py): Implements a lot of (obsolete) things. It's intended to be used to filter projects with an insufficient number of PRs. It does this naively; i.e., it does not account for PRs submitted by bots. A proper filter is applied at a later stage of the process. You can run it in mode `-m p`, specify the minimum number of PRs using `-pr` and provide a file suffix for the considered PR data files using `-x` (you probably won't use this).
- [`post_sort_filter_everything`](./python_proj/data_filters/post_sort_filter_everything.py): Applies the used project / activity filters on the collected PR / Issue data. It aplies multiple sub-filters that are stored in separate files. These sub-filters are not intended to be executed separately. The commandline parameters written about should therefore be used when executing `post_sort_filter_everything`. This script performs a number of steps: 1) runs `post_sort_filters`, 2) runs `post_sort_filter_for_pr_count`, 3) generates a remaining project list using [`post_sort_filter_for_pr_count`](./python_proj/helpers/create_project_user_list.py), 4) filters issues with the project list, 5) runs `post_sort_filter_for_projects`, 6) it removes invalid data entries, it removes duplicate entries. This script expects a list of CHRONOLOGICAL input PR datasets, which is a comma-separated list of names specified through `--chron_in_pr`. Similarly, it expects a list of comma-separated issue datasets, specified through `--chron_in_issue`. The following are the used sub-filters:
  - [`post_sort_filters`](./python_proj/data_filters/post_sort_filters.py): Implements simple "post-sort" filters (i.e., filters that assume the input data is sorted chronologically), filtering various things. Not all of these are used in this study. The default filters are of config `pcuadgbn`, which applies the following rules: 1) it must be on GitHub, 2) can't be newer than the Katz dataset, 3) can't be a GH bot user, 4) can't be deleted account, 5) can't be a bot according to Dey et al., 2020, 6) can't be a bot according to Golzadeh et al., 2021, 7) can't be a bot according to the custom blacklist, 8) it can't have "[bot]" in its name. To specify the filter mode, use the commandline argument `--filter_mode`.
  - [`post_sort_filter_for_pr_count`](./python_proj/data_filters/post_sort_filter_for_pr_count.py): Filters _pull requests_ (not issues, this is done separately) from projects that have an insufficient number of pull requests. You can specify the minimum number of PRs by using the commandline parameter `--min_prs`. The experiment used 5 PRs.
  - [`post_sort_filter_for_projects`](./python_proj/data_filters/post_sort_filter_for_projects.py): Filters all entries of a chronological input dataset according to a list of projects.

### Data Preprocessing

- [`data_sorter`](./python_proj/data_preprocessing/data_sorter.py): Using a project name list as input file, specified using `-q`, it merges the `.json` pull request / issue data of all projects into one file containing all the activities in chronological order. Processing a file as a whole instead of many separate files is substantially faster. In addition, sorting the data makes it possible to make some assumptions in the later analyses phases. Specify the output file name using `-n`, specify the used sorting key with `-k` (we used `closed_at`), and specify the number of used threads using `-t` as it's multiprocessed. It does not handle issue and pull request data simultaneously, so specify this with `-d` to either `issues` or `pull-requests`.
- [`merge_issue_pr_data`](./python_proj/data_preprocessing/merge_issue_pr_data.py): Adds issue data to pull requests. This is necessary as in GitHub, the pull request data structure inherits the issue datastructure (e.g., the submission message, comments, etc. are all issue components, whereas the changes etc. are PR data). As-is the PR data does not contain any of the issue information, for which it must be added. As input, it uses a list of projects, which can be specified using `-f`. The updated pull requests are written to a file with the extention `--with-issue-data` and that the filtered issues are written to a file with the extention `--no-prs`. Because this script is a little scary, because it writes new data files and deletes old issue and pr data, it makes overwriting and deleting the data optional using the `-w` and `-d` flags, respectively, allowing you to do a dry run. (Such that if you add these flags when executing the code, will overwrite and delete entries.)
- [`sliding_window_3`](./python_proj/data_preprocessing/sliding_window_3.py): Version 3 of the sliding window algorithm. The first one grew obsolete, the second worked well but was single-threaded, and the third a multithreaded one to speed up the dataset generation process substantially (it speeds up from multiple days to a couple of hours). You can specify the input issue and PR datasets using `-pd` and `-id`, respectively. Specify the output file name using `-o`, and the window size with `-w`. You can specify the used threads with `-t`, however, don't set this too high as it's a memory bound process and the process will fail if it runs out of memory. You could use the `--no-sna` flag if you want to disable calculating the social network analysis variables. This will reduce the memory footprint substantially.
- [`sliding_window_2`](./python_proj/data_preprocessing/sliding_window_2.py): The old version of `sliding_window_3`, and does exactly the same job as the upgraded version. It's largely obsolete, but still used to calculate the "is first time contributor" field. The `-pd`, `-id`, `-o`, and `-w` parameters work exactly the same. All of the variables that can be calculated with `sliding_window_3` have been disabled in this script.


### Modelling

Contains all of the Python notebooks contained in this study.

- `preprocessing`: Contains the various data preprocessing scripts, doing feature construction, transformation, and data sampling.
  - [`feature_construction`](./python_proj/modelling/notebooks/preprocessing/feature_construction.ipynb): Does feature construction, updating the `IsFirstTimeContributor` field, aggregating the `SecondOrderDegree` fields into one, and aggregating the `LinkIntensity` fields.
  - [`subsampling`](./python_proj/modelling/notebooks/preprocessing/subsampling.ipynb): Subsamples the data points based on the size of projects.
  - [`feature_transformation`](./python_proj/modelling/notebooks/preprocessing/feature_transformation.ipynb): Applies one-off log-transform to the data and min-max feature scaling.
  - [`visualization`](./python_proj/modelling/notebooks/preprocessing/visualization.ipynb): Generates histograms for the different features.
- `logistic_regression`: Contains all of the logistic regression scripts. It has a subfolder per experiment that is performed: the general case, the first-time contributor case, and the non-first-time contributor case. In turn, each folder contains three notebooks, one for the full model, one for the collaboration model, and one for the dependency model.
- `random_forest`: Contains he random forest model scripts. It contains three models, a full model, a first-time contributor model, and a non-first-time contributor model.
- [`run_all_notebooks`](./python_proj/modelling/notebooks/run_all_notebooks.py): Runs all of the notebooks included in this project and outputs their results in corresponding `.out` files.

### Other Code

The rest of the code is not integral to the study.
It contains a bunch of utility files that implement helper functions.
Of these, [`exp_utils`](./python_proj/utils/exp_utils.py) is the most relevant, specifying storage paths as well as standardized commandline parameters.

### The data folder

The code makes all kinds of assumptions about the used data folder.
By default its root folder is `./data/`, however, this can be changed by setting the `EXPERIMENT_BASE_PATH` environment variable.

When downloading the Katz dataset, it should be stored inside the `./data/libraries/` folder, such that all the `.csv` files are stored at `./data/libraries/libraries-1.6.0-2020-01-12/.`

When downloading the bot datasets of Dey and Golzadeh, they should be stored at `./data/bot_data/`.

All of the experimental data is stored in the subfolder `libraries/npm-libraries-1.6.0-2020-01-12/`.
This folder is automatically generated after running `libraries_filter.py`.
For the majority of the code to work, this script must be ran as Katz' data is used throughout the experiment.

This folder will get a number of subfolders throughout the experiment: `issues` and `pull-requests`, containing all issue and pull request data.
This contains the raw `json` files as well as the merged / chronological files that are generated throughout the process.
The subfolder `predictors` has a misleading name as it does not contain predictors of any kind.
Instead, it's used to store the lists of included projects in the experiment.

Some scripts use the `temp` folder located at the root data folder.
The files in here should be cleaned up automatically (unless processes are interrupted somehow).
This folder is mostly used by the multithreaded scripts to store their intermediary results.
