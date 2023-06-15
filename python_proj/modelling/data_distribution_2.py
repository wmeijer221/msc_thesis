import matplotlib.pyplot as plt
import numpy as np
from csv import reader


def make_plot(feature_name: str, data: list[float]):
    # Create a histogram plot
    plt.cla()
    plt.hist(data, bins=30, density=True, edgecolor='black')

    # Add labels and title
    plt.xlabel('Value')
    plt.ylabel('Density')
    plt.title('Distribution Plot')

    plt.savefig(f"./data/figures/data_distribution_2/{feature_name}.png")


with open("./data/libraries/npm-libraries-1.6.0-2020-01-12/test_dataset.csv", "r") as input_file:
    csv_reader = reader(input_file)
    header = next(csv_reader)
    data = [[] for _ in range(len(header))]
    for entry in csv_reader:
        for index, field in enumerate(entry):
            data[index].append(field)

for title, data in zip(header, data):
    make_plot(title, data)
