
for FILTER in periphery_2_dependencies periphery_2_inv_dependencies
do
    # Retrieves data.
    # python3 ./python_proj/data_retrieval/retrieve_pull_requests.py -f $FILTER -t 3
    
    # python3 ./python_proj/data_retrieval/retrieve_issues.py -f _$FILTER -t 3

    # Restructures data into a usable format.
    python3 ./python_proj/data_preprocessing/merge_issue_pr_data.py -f _$FILTER

    SORTED_FILTER=sorted_$FILTER
    
    python3 ./python_proj/data_preprocessing/data_sorter.py \
        -d pull-requests \
        -t 32 \
        -k closed_at \
        -q _$FILTER \
        -n $SORTED_FILTER \
        -x --with-issue-data
    
    python3 ./python_proj/data_preprocessing/data_sorter.py \
        -d issues \
        -t 32 \
        -k closed_at \
        -q _$FILTER \
        -n sorted_$FILTER \
        -x --no-prs

    # Filters data.
    python3 ./python_proj/data_filters/post_sort_filter_everything.py \
        --chron_in_pr $SORTED_FILTER \
        --chron_in_issue $SORTED_FILTER \
        --tag periphery_2 \
        --windows all
done
