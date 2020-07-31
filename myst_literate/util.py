"""Utility functions."""
import itertools

from nbformat import NotebookNode


def nb_cell(cell_type: str, source="", metadata: dict = None, **kwargs):
    """Construct a Jupyter notebook cell.

    Args:
        cell_type: Cell type (markdown, code, raw).
        source: Cell source.
        metadata: Metadata dictionary.
        **kwargs: Additional metadata.
    """
    metadata = dict(metadata or {}, **kwargs)
    return NotebookNode(
        {"cell_type": cell_type, "metadata": metadata, "source": source}
    )


def concat(iterable):
    """Concatenate each element in an iterable of iterables into a list."""
    return list(itertools.chain(*iterable))


def is_private(name):
    """Check whether a Python object is private based on its name."""
    return name.startswith("_")
