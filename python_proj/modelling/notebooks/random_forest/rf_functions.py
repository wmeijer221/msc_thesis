"""
Helper script for reusable RF model creation scripts.
"""

from typing import Iterator, Tuple, Dict

import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    f1_score,
    confusion_matrix,
    classification_report,
    accuracy_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import KFold

from python_proj.utils.mt_utils import parallelize_tasks
from python_proj.utils.util import Counter


def calculate_metrics(predicted_labels, true_labels, sample_weights=None):
    """Calculates standard performance metrics: accuracy, precision, recall, F1."""
    return {
        "accuracy": accuracy_score(
            true_labels, predicted_labels, sample_weight=sample_weights
        ),
        "precision": precision_score(
            true_labels, predicted_labels, sample_weight=sample_weights
        ),
        "recall": recall_score(
            true_labels, predicted_labels, sample_weight=sample_weights
        ),
        "f1": f1_score(true_labels, predicted_labels, sample_weight=sample_weights),
    }


def create_model(
    train_predictors: pd.DataFrame,
    train_labels: pd.Series,
    test_predictors: pd.DataFrame,
    test_labels: pd.Series,
    random_state: int | Counter,
) -> Tuple[RandomForestRegressor, Dict[str, float]]:
    """
    Creates a single random forest model,
    returing the model and its performance metrics.
    """
    # Model creation and predictions.
    if isinstance(random_state, Counter):
        random_state = random_state.get_next()
    print(f"{random_state=}")
    rf = RandomForestRegressor(n_estimators=100, random_state=random_state)

    rf.fit(train_predictors, train_labels)

    predictions = rf.predict(test_predictors)
    predictions = [pred >= 0.5 for pred in predictions]

    # F1 scores.
    conf = confusion_matrix(test_labels, predictions)

    metrics = calculate_metrics(predictions, test_labels)

    print(f"{metrics=}\n")

    # Other metrics.
    print(f"Confusion matrix:\n{conf}\n")
    print("Classification report:")
    print(classification_report(test_labels, predictions))

    return rf, metrics


def kfold_rf_evaluation(
    df: pd.DataFrame,
    predictor_fields: Iterator[str],
    k: int,
    label_column: str,
    seed_counter: Counter,
) -> Tuple[Dict[str, float], float, float]:
    """
    Creates rf models using k-fold CV, returning their
    individual F1 scores, their mean, and the standard deviation.
    """
    random_state = seed_counter.get_next()

    def __create_model_for_fold(task, *args, **kwargs):
        train_idx, test_idx = task
        train = df.loc[train_idx, :]
        test = df.loc[test_idx, :]
        train_predictors = train[predictor_fields]
        train_labels = train[label_column]
        test_predictors = test[predictor_fields]
        test_labels = test[label_column]
        _, rf_metrics = create_model(
            train_predictors, train_labels, test_predictors, test_labels, random_state
        )
        return rf_metrics

    kf = KFold(n_splits=k, shuffle=True, random_state=seed_counter.get_next())
    tasks = kf.split(df)
    models_and_f1s = parallelize_tasks(
        tasks,
        __create_model_for_fold,
        thread_count=min(k, 12),
        return_results=True,
        print_lifetime_events=False,
    )

    f1_scores = [entry["f1"] for entry in models_and_f1s]
    f1_mean = np.mean(f1_scores)
    f1_std = np.std(f1_scores)

    return f1_scores, f1_mean, f1_std
