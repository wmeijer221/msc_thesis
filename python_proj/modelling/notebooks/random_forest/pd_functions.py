"""
Helper script for reusable PDP plotting functions.
"""

from matplotlib import pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import PartialDependenceDisplay

from python_proj.utils.util import safe_save_fig


def create_partial_dependence_plots(
    rf_model: RandomForestRegressor, used_predictors: pd.DataFrame, output_folder: str
):
    """Creates figures showing partial dependence plots."""
    # Collective partial dependence plot.
    PartialDependenceDisplay.from_estimator(
        rf_model, used_predictors, used_predictors.columns, percentiles=(0.01, 0.99)
    )

    fig = plt.gcf()
    axs = fig.axes

    lines = []
    for ax in axs:
        __lines = list([(line.get_xdata(), line.get_ydata()) for line in ax.lines])
        lines.extend(__lines)

    for (x, y), label in zip(lines, used_predictors.columns):
        plt.clf()
        plt.plot(x, y, linestyle="-", color="#e69d00")
        plt.xlabel(label)
        plt.ylabel("Partial Dependence")
        plt.tight_layout()
        output_path = f"{output_folder}/{label}.png"
        safe_save_fig(output_path)
