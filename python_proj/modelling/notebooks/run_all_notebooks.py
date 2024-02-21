"""
Executes all of the notebooks relevant to this study in chronological order.
"""

import json
import os
from sys import argv
from typing import List

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from wmutils.file import OpenMany, iterate_through_files_in_nested_folders


def get_notebooks_in_dir(base_dir: str) -> list[str]:
    SOME_BIG_NUMBER = 10_000
    return [
        file
        for file in iterate_through_files_in_nested_folders(
            base_folder=base_dir, max_depth=SOME_BIG_NUMBER
        )
        if file.endswith(".ipynb")
    ]


def get_nth_parent_dir(path: str, n: int):
    for _ in range(n):
        path = os.path.dirname(path)
    return path


def get_notebooks(
    root: str, do_preprocessing: bool, do_logit: bool, do_rf: bool, do_obfuscate: bool
):
    # Collects logistic regression notebooks.
    lr_notebook_dir = f"{root}/python_proj/modelling/notebooks/logistic_regression/"
    lr_notebooks = get_notebooks_in_dir(lr_notebook_dir)

    # Collects random forest notebooks.
    rf_notebook_dir = f"{root}/python_proj/modelling/notebooks/random_forest/"
    rf_notebooks = get_notebooks_in_dir(rf_notebook_dir)

    def __is_not_feature_importance(entry: str) -> bool:
        return not entry.endswith("feature_importance.ipynb")

    rf_notebooks = filter(__is_not_feature_importance, rf_notebooks)
    feature_importance_nb = f"{rf_notebook_dir}/feature_importance.ipynb"
    rf_notebooks = [*rf_notebooks, feature_importance_nb]

    # This is hardcoded as for preprocessing the order matters.
    preproc_notebooks = [
        "feature_construction",
        "subsampling",
        "feature_transformation",
    ]

    if do_obfuscate:
        # If we need to obfuscate, the preprocessing pipeline
        # is prepended with this process.
        preproc_notebooks = [
            "feature_construction",
            "data_obfuscation",
            *preproc_notebooks,
        ]

    preproc_notebooks = [
        f"{root}/python_proj/modelling/notebooks/preprocessing/{file}.ipynb"
        for file in preproc_notebooks
    ]

    # Overwrites the files if they're not needed.
    if not do_preprocessing:
        preproc_notebooks = []
    if not do_logit:
        lr_notebooks = []
    if not do_rf:
        rf_notebooks = []

    # Aggregates the notebook files into one list.
    notebook_files = [
        *preproc_notebooks,
        *lr_notebooks,
        *rf_notebooks,
    ]

    return notebook_files


def execute_notebooks(notebook_files: List[str], root: str):
    with OpenMany(notebook_files, "r+", encoding="utf-8") as nb_file:
        for index, nb_file in enumerate(nb_file):
            print(f'Runing nb #{index}: "{nb_file.name}"')
            nb = nbformat.read(nb_file, as_version=4)
            ep = ExecutePreprocessor(kernel_name="python3")
            ep.preprocess(nb, {"metadata": {"path": root}})
            nb_file.seek(0)
            nbformat.write(nb, nb_file)


if __name__ == "__main__":
    do_obfuscate = "--no-obfuscate" not in argv
    do_preprocessing = "--no-preproc" not in argv
    do_logit = "--no-logit" not in argv
    do_rf = "--no-rf" not in argv
    print(f"{do_obfuscate=}, {do_preprocessing=}, {do_logit=}, {do_rf=}")

    root = os.environ.get("PYTHONPATH")
    print(f"{root=}")

    nbs = get_notebooks(root, do_preprocessing, do_logit, do_rf, do_obfuscate)
    # nbs = [f"{root}/python_proj/modelling/notebooks/test.ipynb", *nbs]
    print(f"Notebooks ({len(nbs)}):", json.dumps(nbs, indent=2))
    execute_notebooks(nbs, root)
