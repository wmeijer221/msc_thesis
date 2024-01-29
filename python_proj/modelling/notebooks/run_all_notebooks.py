from python_proj.helpers.run_python_notebook import execute_notebooks
from python_proj.utils.util import iterate_through_files_in_nested_folders

import os


SOME_BIG_NUMBER = 1000


def get_notebooks_in_dir(base_dir: str) -> list[str]:
    return list(
        [
            file
            for file in iterate_through_files_in_nested_folders(
                base_folder=base_dir, max_depth=SOME_BIG_NUMBER
            )
            if file.endswith(".ipynb")
        ]
    )


def get_nth_parent_dir(path: str, n: int):
    for _ in range(n):
        path = os.path.dirname(path)
    return path


# Collects all experimental notebooks.
# The order of these is not relevant.
root = get_nth_parent_dir(__file__, 3)

lr_notebook_dir = f"{root}/modelling/notebooks/logistic_regression/"
lr_notebooks = get_notebooks_in_dir(lr_notebook_dir)

rf_notebook_dir = f"{root}/modelling/notebooks/random_forest/"
rf_notebooks = get_notebooks_in_dir(rf_notebook_dir)


# This is hardcoded as for preprocessing the order matters.
preprocessing_steps = [
    "feature_construction.ipynb",
    "subsampling.ipynb",
    "feature_transformation.ipynb",
]
preprocessing_steps = [
    f"{root}/modelling/notebooks/preprocessing/{file}" for file in preprocessing_steps
]

# Aggregates the notebook files into one list.
notebook_files = [
    *preprocessing_steps,
    *lr_notebooks,
    *rf_notebooks,
]
print(f"Running {len(notebook_files)} notebooks.")

# Runs them.
execute_notebooks(notebook_files)
