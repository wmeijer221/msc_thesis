
import sys
import os
import json
import subprocess


def __get_file_name_without_extension(file_name: str) -> str:
    return ".".join(file_name.split(".")[:-1])


def transpile_notebook_to_python(notebook_path: str) -> str:
    """
    Transpiles the jupyter notebook to python code.

    :param notebook_path: The path to the notebook that's transpiled.
    """

    python_path = __get_file_name_without_extension(notebook_path) + ".py"

    with open(notebook_path, "r", encoding='utf-8') as notebook_file:
        notebook = json.loads(notebook_file.read())
        cells = notebook['cells']

        with open(python_path, "w+", encoding='utf-8') as python_file:
            for cell in cells:
                if cell['cell_type'] != 'code':
                    continue
                python_file.writelines(cell['source'])
                python_file.write("\n\n")

    return python_path


def execute_notebook(notebook_path: str):
    """
    Transpiles jupyter notebook file to a 
    temporary python script and executes it.

    :param notebook_path: The path to the notebook file that's executed.
    """

    if not os.path.exists(notebook_path):
        raise FileNotFoundError(
            f"Notebook file doesn't exist: '{notebook_path}'.")

    try:
        # Creates python
        python_path = transpile_notebook_to_python(notebook_path)
        notebook_output = subprocess.check_output(['python3', python_path])
        output_path = __get_file_name_without_extension(notebook_path) + ".out"
        with open(output_path, "bw+") as output_file:
            output_file.write(notebook_output)
        print(f'Stored output at "{output_path}".')
    finally:
        os.remove(python_path)


if __name__ == "__main__":
    NB_PATH = sys.argv[-1].strip()
    execute_notebook(NB_PATH)
