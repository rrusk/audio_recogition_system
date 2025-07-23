# libs/utils.py
from itertools import zip_longest

def grouper(iterable, n, fillvalue=None):
    """Groups elements from iterable in chunks of size n."""
    iterators = [iter(iterable)] * n
    return (
        filter(None, values)
        for values in zip_longest(fillvalue=fillvalue, *iterators)
    )
