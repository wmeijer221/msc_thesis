from os import path

import python_proj.utils.exp_utils as exp_utils
import python_proj.data_preprocessing.alias_unmasking.ght_alias_unmasking.merge_aliases as ght


owner = "DefinitelyTyped"
repo = "DefinitelyTyped"

exp_utils.load_paths_for_all_argv()
input_path = exp_utils.RAW_DATA_PATH(owner=owner, repo=repo, ext="")
output_path = exp_utils.RAW_DATA_PATH(owner=owner, repo=repo, ext="")
output_dir = path.dirname(output_path)

ght.merge_aliases(input_path, output_dir,thr_min=1, thr_max=100)
