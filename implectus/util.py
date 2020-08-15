"""Utility functions."""
import itertools

import jupytext
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


def jupytext_writes(notebook: NotebookNode, fmt: str, **kwargs):
    """"Write a notebook to a Unicode string in a given Jupytext format.

    Args:
        notebook: The notebook to write.
        fmt: The Jupytext format (e.g. "py:light", "ipynb").
        **kwargs: Additional arguments for `nbformat.writes`.

    Returns: The Unicode representation of the notebook, with a trailing newline.
    """
    content = jupytext.writes(notebook, fmt, **kwargs)
    if isinstance(content, bytes):
        content = content.decode("utf8")
    if not content.endswith("\n"):
        content += "\n"
    return content
