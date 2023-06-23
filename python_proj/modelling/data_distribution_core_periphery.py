"""
Creates a pie chart showing the distribution of projects
between the core and periphery projects.
"""
import json
import matplotlib.pyplot as plt
import os

import python_proj.utils.exp_utils as exp_utils
from python_proj.utils.arg_utils import get_argv, safe_get_argv
from python_proj.utils.util import OpenMany


def get_distribution(all_path: str, filter_paths: list[str]) -> dict[str, int]:
    """
    Calculates what filters the projects in ``all_path`` come from.
    Returns the result.
    """

    with open(all_path, 'r', encoding='utf-8') as all_file:
        all_projects = [line.strip().lower() for line in all_file]

    with OpenMany(filter_paths, "r", encoding='utf-8') as filter_files:
        filter_to_project = {path: [line.strip().lower() for line in filter_file]
                             for path, filter_file in zip(filter_paths, filter_files)}

    count_per_filter = {filter_path: 0 for filter_path in filter_paths}
    for project in all_projects:
        already_found = False
        for filter_path, filter_projects in filter_to_project.items():
            if project in filter_projects:
                count_per_filter[filter_path] += 1
                if already_found:
                    print(f'Project counted twice: {project}.')
                already_found = True

    print(json.dumps(count_per_filter, indent=4))
    return count_per_filter


def generate_figure(distribution: dict[str, int], output_path: str):
    """
    Generates pie chart for provided distribution.
    """

    # Sample data for the pie chart
    labels = [".".join(os.path.basename(key).split(".")[:-1])
              for key in distribution.keys()]
    sizes = distribution.values()

    # Create a pie chart
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)

    # Add title
    plt.title('Project Distribution Across Filters')

    # Set aspect ratio to be equal to make the pie circular
    plt.axis('equal')

    # Stores the chart
    plt.savefig(output_path)


if __name__ == "__main__":
    exp_utils.load_paths_for_eco()
    all_projects_file = safe_get_argv(key='-a', default="")
    all_projects_path = exp_utils.RAW_DATA_PATH(
        data_type="user-ids", owner='proj', repo='users', ext=all_projects_file)
    print(f'{all_projects_path=}')

    filter_projects_files = get_argv(key='-f').strip().split(",")
    filter_project_paths = [exp_utils.FILTER_PATH(filter_type=entry) for entry in filter_projects_files]
    print(f'{filter_project_paths=}')

    fig_output_path = exp_utils.FIGURE_PATH(
        data_source='pr',
        file_name="",
        figure_name=f"pr_project_filter_distribution_{all_projects_file}.png")
    print(f'{fig_output_path=}')

    project_distribution = get_distribution(
        all_projects_path, filter_project_paths)
    generate_figure(project_distribution, fig_output_path)
