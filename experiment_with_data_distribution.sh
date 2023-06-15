#!/bin/bash

mkdir ./data/figures/data_distribution_2

echo Starting with all
python3 ./python_proj/data_preprocessing/sliding_window_2.py \
    -pd sorted_filtered_focal_to_other_complete,sorted_filtered_other_to_focal_sample_1_complete,sorted_other_to_focal_sample_2_complete,sorted_filtered_core_complete \
    -id sorted_filtered_issues_core,sorted_filtered_issues_core_to_other,sorted_filtered_other_to_core_sample_1,sorted_filtered_other_to_core_sample_2
    
    
python3 ./python_proj/modelling/data_distribution_2.py
cd /data/s4509412/data/data/figures/data_distribution_2/
mkdir ./all
mv ./*.png ./all/
cd ../../..

for value in 30 90 180 365
do
    echo Starting with $value
    python3 ./python_proj/data_preprocessing/sliding_window_2.py \
        -w $value \
        -pd sorted_filtered_focal_to_other_complete,sorted_filtered_other_to_focal_sample_1_complete,sorted_other_to_focal_sample_2_complete,sorted_filtered_core_complete \
        -id sorted_filtered_issues_core,sorted_filtered_issues_core_to_other,sorted_filtered_other_to_core_sample_1,sorted_filtered_other_to_core_sample_2
    python3 ./python_proj/modelling/data_distribution_2.py
    cd /data/s4509412/data/data/figures/data_distribution_2/
    mkdir ./d_$value/
    mv ./*.png ./d_$value/
    cd ~/msc_thesis
done

echo Done
