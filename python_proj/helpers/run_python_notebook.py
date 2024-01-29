import sys
import os
import json
import subprocess
from typing import List


def __get_file_name_without_extension(file_name: str) -> str:
    return ".".join(file_name.split(".")[:-1])


def transpile_notebook_to_python(notebook_path: str) -> str:
    """
    Transpiles the jupyter notebook to python code.

    :param notebook_path: The path to the notebook that's transpiled.
    """

    python_path = __get_file_name_without_extension(notebook_path) + ".py"
    print(f'Storing temporary python file at "{python_path}".')

    with open(notebook_path, "r", encoding="utf-8") as notebook_file:
        notebook = json.loads(notebook_file.read())
        cells = notebook["cells"]

        with open(python_path, "w+", encoding="utf-8") as python_file:
            for cell in cells:
                if cell["cell_type"] != "code":
                    continue
                valid_lines = [line for line in cell['source'] if not line.startswith("%")]
                python_file.writelines(valid_lines)
                python_file.write("\n\n")

    return python_path


def run_notebook(python_path: str):
    """
    Runs a python script.
    """

    args = ["python3", python_path]
    popen = subprocess.Popen(args, stdout=subprocess.PIPE, universal_newlines=True)
    output_path = __get_file_name_without_extension(python_path) + ".out"

    print(f'\nRunning "{python_path}".')
    print(f'Storing output at "{output_path}".')
    print(("#" * 10) + " [ LOGS START ] " + ("#" * 10))

    with open(output_path, "w+", encoding="utf-8") as output_file:
        for stdout_line in iter(popen.stdout.readline, ""):
            print(stdout_line, end="")
            output_file.write(stdout_line)

    print(("#" * 10) + " [  LOGS END  ] " + ("#" * 10) + "\n")

    popen.wait()
    if popen.returncode != 0:
        raise RuntimeError(
            f"Subprocess completed with non-zero return code: {popen.returncode}"
        )


def execute_notebooks(notebook_paths: "List[str] | str"):
    """
    Transpiles jupyter notebook files to a
    temporary python script and executes them.

    :param notebook_paths: The path(s) to the notebook file(s) that is (are) executed.
    """

    if isinstance(notebook_paths, str):
        notebook_paths = [notebook_paths]

    for notebook_path in notebook_paths:
        if not os.path.exists(notebook_path):
            raise FileNotFoundError(f"Notebook file doesn't exist: '{notebook_path}'.")

    # Transpiles files.
    python_paths = [
        transpile_notebook_to_python(notebook_path) for notebook_path in notebook_paths
    ]
    python_paths = list(python_paths)

    # Runs files.
    try:
        for python_path in python_paths:
            run_notebook(python_path)
    finally:
        for python_path in python_paths:
            os.remove(python_path)


if __name__ == "__main__":
    __notebook_paths = sys.argv[1:]
    execute_notebooks(__notebook_paths)
    