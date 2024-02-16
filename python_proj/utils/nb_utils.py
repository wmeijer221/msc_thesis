# TODO: Remove this and replace all of it with `wmeijer_utils`.

import copy
from typing import Iterator

import matplotlib.pyplot as plt
import pandas as pd

from python_proj.utils.util import safe_save_fig

default_plot_settings = {"edgecolor": "black", "color": "#e69d00"}

default_plot_settings_2 = copy.deepcopy(default_plot_settings)
default_plot_settings_2["color"] = "#56b3e9"


def __fix_x_label_fontsize(column):
    # Adjusts x-label's fontsize to fit the text.
    fig = plt.gcf()
    fig_width = fig.get_figwidth()
    xlabel_fontsize = int(fig_width * 100 / len(column))
    ax = plt.gca()
    orig_fontsize = ax.xaxis.label.get_fontsize()
    ax.xaxis.label.set_fontsize(min(xlabel_fontsize, orig_fontsize))


def create_histogram(
    df: pd.DataFrame, column: str, output_folder: str, show_without_value=None
):
    can_create_feature_histograms = True

    if not can_create_feature_histograms:
        return

    binary_fields = df.select_dtypes(exclude="number").columns

    print(column)
    plt.clf()
    entries = df[column]

    if column in binary_fields:
        entries = df[column].replace({False: 0, True: 1})
        plt.xticks([0, 1], ["False", "True"])
        plt.hist(entries, bins=2, **default_plot_settings)
        plt.ylabel("Frequency")
    # elif __column in shown_fields_without_zeroes:
    elif not show_without_value is None:
        _, bins, _ = plt.hist(
            entries, bins=30, alpha=1, label="All Data", **default_plot_settings
        )
        ax: plt.Axes = plt.gca()
        ax.set_ylabel("Frequency")
        ax.set_xlabel(column)
        __fix_x_label_fontsize(column)

        filtered_data = df[column][df[column] != show_without_value]
        ax2 = ax.twinx()

        ax2.hist(
            filtered_data,
            bins,
            alpha=0.5,
            label=f"Excl. {show_without_value}",
            **default_plot_settings_2,
        )
        ax2.set_ylabel(f"Frequency (excl. x = {show_without_value})")
        ax2.set_zorder(10)
        plt.tight_layout()
    else:
        plt.hist(entries, bins=30, **default_plot_settings)
        plt.ylabel("Frequency")

    plt.xlabel(column)
    __fix_x_label_fontsize(column)
    plt.tight_layout()

    output_path = f"{output_folder}/{column}.png"
    safe_save_fig(output_path)


def create_predictor_histograms(
    df: pd.DataFrame, output_folder: str, columns: Iterator[str]
):
    # Iterate over the columns and generate histograms
    for column in columns:
        create_histogram(df, column, output_folder, show_without_value=0)


from wmeijer_utils.multithreading import parallelize_tasks
from functools import partial


def execute_partial(task, my_partial_task, *args, **kwargs):
    my_partial_task(columns=[task])


def create_predictor_histograms_in_parallel(
    df: pd.DataFrame, output_folder: str, columns: Iterator[str]
):
    """
    For those who want many figures, but don't
    have the time to create them sequentially.
    """
    partial_task = partial(
        create_predictor_histograms, df=df, output_folder=output_folder
    )
    parallelize_tasks(
        list(columns), execute_partial, thread_count=8, my_partial_task=partial_task
    )
