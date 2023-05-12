"""
Implements utility functions for the general experiment.
"""

from python_proj.utils.arg_utils import safe_get_argv


def build_data_path_from_argv(eco_key: str = "-e", data_source_key: str = '-d', file_name_key: str = '-f', file_ext: str = ".json"):
    base_path = './data/libraries/{eco}-libraries-1.6.0-2020-01-12/{data_source}/{file_name}{file_ext}'
    eco = safe_get_argv(eco_key, default="npm")
    data_source = safe_get_argv(data_source_key, default="pull-requests")
    file_name = safe_get_argv(file_name_key, default='sorted')
    return base_path.format(eco=eco,
                            data_source=data_source,
                            file_name=file_name,
                            file_ext=file_ext)
