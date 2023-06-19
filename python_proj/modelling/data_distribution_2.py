"""Plots distribution data."""

from csv import reader
from functools import partial

import matplotlib.pyplot as plt

import python_proj.utils.exp_utils as exp_utils


def make_plot(feature_name: str, data: list[float], output_path: str):
    """Makes a distribution plot for one feature."""

    # Create a histogram plot
    plt.cla()
    plt.hist(data, bins=30, density=True, edgecolor='black')

    # Add labels and title
    plt.xlabel('Value')
    plt.ylabel('Density')
    plt.title(f'Distribution Plot {feature_name}')
    
    plt.savefig(output_path)


def make_plots_for_all_features():
    """Makes plots for all features."""

    exp_utils.load_paths_for_eco()
    input_path = exp_utils.TRAIN_DATASET_PATH(file_name="test_dataset")
    figure_base_path: partial[str] = partial(
        exp_utils.FIGURE_PATH, data_source="distribution_2", file_name="")
    print(f'Loading data from: "{input_path}".')
    with open(input_path, "r", encoding='utf-8') as input_file:
        csv_reader = reader(input_file)
        header = next(csv_reader)
        input_data = [[] for _ in range(len(header))]
        for entry in csv_reader:
            for index, field in enumerate(entry):
                input_data[index].append(field)

    for title, input_data in zip(header, input_data):
        output_path = figure_base_path(figure_name=title)
        print(f'Creating figure at "{output_path}".')
        make_plot(title, input_data, output_path)


if __name__ == "__main__":
    make_plots_for_all_features()
