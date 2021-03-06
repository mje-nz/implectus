"""Utility functions."""
import itertools
import re
import textwrap
from pathlib import Path

import jupytext
from nbformat import NotebookNode

from .__about__ import __version__


def nb_cell(cell_type: str, source="", metadata: dict = None, **kwargs):
    """Construct a Jupyter notebook cell.

    Args:
        cell_type: Cell type (markdown, code, raw).
        source: Cell source.
        metadata: Metadata dictionary.
        **kwargs: Additional metadata.
    """
    metadata = dict(metadata or {}, **kwargs)
    return NotebookNode(cell_type=cell_type, metadata=metadata, source=source)


_implectus_header_template = textwrap.dedent(
    """\
    # Autogenerated from `{filename}`
    This file was created by Implectus {version}.  Do not edit this file;
    edit `{filename}` instead."""
)
_implectus_header_re = re.compile(
    _implectus_header_template.replace(".", r"\.").format(
        filename=r"([^\n]*?)", version=r"([\w\.\-]*?)"
    )
)


def implectus_header_cell(filename):
    """Generate an Implectus 'autogenerated from' header cell."""
    text = _implectus_header_template.format(filename=filename, version=__version__)
    return nb_cell("markdown", text)


def is_implectus_header_cell(cell: NotebookNode):
    """Check if a cell is an Implectus header cell."""
    return cell.cell_type == "markdown" and _implectus_header_re.match(cell.source)


def is_autogenerated(filename):
    """Check if a notebook was generated by Implectus."""
    try:
        nb = jupytext.read(filename)
        return is_implectus_header_cell(nb.cells[0])
    except (ValueError, FileNotFoundError):
        return False


class DestinationNotOverwriteableError(RuntimeError):
    def __init__(self, filename: str):
        super().__init__()
        self.filename = filename


def assert_overwriteable(filename):
    """Throw if `filename` exists and isn't autogenerated.

    Raises: DestinationNotOverwriteableError
    """
    if Path(filename).exists() and not is_autogenerated(filename):
        raise DestinationNotOverwriteableError(filename)


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
