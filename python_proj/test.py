my_dcit = {
    'a': 1,
    'b': 2,
    'c': 3
}

from python_proj.utils.util import invert_dict

my_inverted_dict = invert_dict(my_dcit)

print(f'{my_inverted_dict=}')
