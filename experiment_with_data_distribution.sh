#!/bin/bash

echo Removing invalid entries.
python3 ./python_proj/data_preprocessing/sliding_window_2.py \
    -m r \
    -pd sorted_filtered_focal_to_other_complete,sorted_filtered_other_to_focal_sample_1_complete,sorted_filtered_other_to_focal_sample_2_complete,sorted_filtered_core_complete \
    -id sorted_filtered_issues_core,sorted_filtered_issues_core_to_other,sorted_filtered_other_to_core_sample_1,sorted_filtered_other_to_core_sample_2

mkdir ./data/figures/data_distribution_2

echo Starting with all
python3 ./python_proj/data_preprocessing/sliding_window_2.py \
    -pd sorted_filtered_focal_to_other_complete_no_invalid,sorted_filtered_other_to_focal_sample_1_complete_no_invalid,sorted_filtered_other_to_focal_sample_2_complete_no_invalid,sorted_filtered_core_complete_no_invalid \
    -id sorted_filtered_issues_core_no_invalid,sorted_filtered_issues_core_to_other_no_invalid,sorted_filtered_other_to_core_sample_1_no_invalid,sorted_filtered_other_to_core_sample_2_no_invalid
python3 ./python_proj/modelling/data_distribution_2.py -s all

for value in 30 90 180 365
do
    echo Starting with $value day window.
    python3 ./python_proj/data_preprocessing/sliding_window_2.py \
        -w $value \
        -pd sorted_filtered_focal_to_other_complete_no_invalid,sorted_filtered_other_to_focal_sample_1_complete_no_invalid,sorted_filtered_other_to_focal_sample_2_complete_no_invalid,sorted_filtered_core_complete_no_invalid \
        -id sorted_filtered_issues_core_no_invalid,sorted_filtered_issues_core_to_other_no_invalid,sorted_filtered_other_to_core_sample_1_no_invalid,sorted_filtered_other_to_core_sample_2_no_invalid
    python3 ./python_proj/modelling/data_distribution_2.py -s d_$value
done

echo Done!
