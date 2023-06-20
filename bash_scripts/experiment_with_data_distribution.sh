#!/bin/bash

# Does three things:
# Iterate through all chronological datasets, removing invalid entries.
# Generate various training datasets with those chronological datasets using different window sizes.
# Generate figures of the data distribution.

echo Removing invalid entries.
python3 ./python_proj/data_preprocessing/sliding_window_2.py \
    -m r \
    -pd sorted_filtered2_core_complete,sorted_filtered2_focal_to_other_complete,sorted_filtered2_focal_to_other_complete,sorted_filtered2_focal_to_other_complete \
    -id sorted_filtered2_issues_core_no_invalid,sorted_filtered2_issues_core_no_invalid,sorted_filtered2_issues_core_no_invalid,sorted_filtered2_issues_core_no_invalid

echo Starting with all
python3 ./python_proj/data_preprocessing/sliding_window_2.py \
    -pd sorted_filtered2_core_complete_no_invalid,sorted_filtered2_focal_to_other_complete_no_invalid,sorted_filtered2_focal_to_other_complete_no_invalid,sorted_filtered2_focal_to_other_complete_no_invalid \
    -id sorted_filtered2_issues_core_no_invalid,sorted_filtered2_issues_core_no_invalid,sorted_filtered2_issues_core_no_invalid,sorted_filtered2_issues_core_no_invalid
python3 ./python_proj/modelling/data_distribution_2.py -s all --skip 4

for value in 30 90 180 365
do
    echo Starting with $value day window.
    python3 ./python_proj/data_preprocessing/sliding_window_2.py \
        -w $value \
        -pd sorted_filtered2_core_complete_no_invalid,sorted_filtered2_focal_to_other_complete_no_invalid,sorted_filtered2_focal_to_other_complete_no_invalid,sorted_filtered2_focal_to_other_complete_no_invalid \
        -id sorted_filtered2_issues_core_no_invalid,sorted_filtered2_issues_core_no_invalid,sorted_filtered2_issues_core_no_invalid,sorted_filtered2_issues_core_no_invalid
    python3 ./python_proj/modelling/data_distribution_2.py -s d_$value --skip 4
done

echo Done!
