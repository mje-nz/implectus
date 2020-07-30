"""Utility functions."""
import itertools

from nbformat import NotebookNode


def nb_cell(cell_type, metadata=None, source=""):
    """Construct a Jupyter notebook cell."""
    return NotebookNode(
        {"cell_type": cell_type, "metadata": metadata or {}, "source": source}
    )


def concat(iterable):
    """Concatenate each element in an iterable of iterables into a list."""
    return list(itertools.chain(*iterable))


def is_private(name):
    """Check whether a Python object is private based on its name."""
    return name.startswith("_")
