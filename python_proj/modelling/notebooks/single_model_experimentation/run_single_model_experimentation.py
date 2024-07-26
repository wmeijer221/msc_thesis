"""Runs the notebook as a python script."""

from pathlib import Path
from python_proj.modelling.notebooks.run_all_notebooks import execute_notebooks


nb = Path('./python_proj/modelling/notebooks/single_model_experimentation/single_model_experimentation.ipynb').absolute()
root_path = Path('.').absolute()

execute_notebooks([nb], root_path)
