"""
This module provides common utility functions used across the project,
such as the 'grouper' for iterating over a list in fixed-size chunks.
"""

from itertools import zip_longest


def grouper(iterable, n, fillvalue=None):
    """Groups elements from an iterable into fixed-length chunks."""
    iterators = [iter(iterable)] * n
    return (
        filter(None, values) for values in zip_longest(fillvalue=fillvalue, *iterators)
    )
