"""Helper functions for exporting documentation."""
import copy
import re
from pathlib import Path
from typing import Union, cast
from typing.io import TextIO

from nbformat import NotebookNode

from .config import ImplectusConfiguration
from .export_code import exported_names
from .util import concat, jupytext_writes, nb_cell

__all__ = ["write_doc", "writes_doc"]


def should_document(cell):
    tags = cell.metadata.get("tags", {})
    return "export-internal" not in tags and "remove-cell" not in tags


_directives = "module|function|data|exception|class|decorator"
_re_sphinx_directive = re.compile(
    r"^\s*```\s*{(?:py:|auto)?(?:%s)}\s+([^`\s(]*).*?```" % _directives,
    re.MULTILINE | re.DOTALL,
)


def documented_names(cell):
    """For markdown cells, return the names that are already documented."""
    if cell.cell_type != "markdown" or not should_document(cell):
        return []
    return _re_sphinx_directive.findall(cell.source)


def autodoc_directive_for_name(name, type_):
    return "```{auto%s} %s```" % (type_, name)


def document_cell(cell, skip_names):
    """Replace exported code cells with autodoc directives for the names they define.

    Args:
        skip_names: List of names to skip.

    Returns:
        list of cells to insert where the cell was.
    """
    tags = cell.metadata.get("tags", {})
    cells = [cell]
    if "export" in tags:
        # Create autodoc directives for any exported names that haven't been documented
        # manually elsewhere in the notebook
        directives = [
            autodoc_directive_for_name(name, type_)
            for (name, type_) in exported_names(cell)
            if name not in skip_names
        ]
        # Hide the cell's code
        cell.metadata.tags.append("remove-input")
        cells = [cell]
        if directives:
            # Insert a cell with the autodoc directives before this one in the notebook,
            # so that a cell which defines a function and then executes something will
            # at least have the autodoc directive before the output
            cells.insert(0, nb_cell("markdown", "\n".join(directives)))
    return cells


def writes_doc(
    notebook: NotebookNode,
    source_filename: Union[str, Path],
    config: ImplectusConfiguration,
):
    """Write the documentation for the given source file to a string.

    The format is given by config.doc_format.

    Args:
        notebook: The notebook to write.
        source_filename: Full path of the file from which notebook was read.
        config: The Implectus configuration.
    """
    nb = copy.deepcopy(notebook)

    # Insert py:currentmodule directive for autodoc
    module_name = config.module_name(source_filename)
    # TODO: should module_name() throw instead?
    assert module_name is not None
    directive = "```{py:currentmodule} %s```" % module_name
    nb.cells.insert(0, nb_cell("markdown", directive))

    nb.cells = [cell for cell in nb.cells if should_document(cell)]
    documented_names_ = concat(documented_names(cell) for cell in nb.cells)
    nb.cells = concat(document_cell(cell, documented_names_) for cell in nb.cells)

    return jupytext_writes(nb, config.doc_format)


def write_doc(
    notebook: NotebookNode,
    source_filename: Union[str, Path],
    config: ImplectusConfiguration,
    fp: Union[str, Path, TextIO] = None,
):
    """Write the documentation for the given source file to a file.

    The format is given by config.doc_format.

    Args:
        notebook: The notebook to write.
        source_filename: Full path of the file from which notebook was read.
        config: The Implectus configuration.
        fp: Any file-like object with a write method that accepts Unicode, or a path to
            write a file, or None to determine the destination filename automatically.
    """
    if fp is None:
        fp = config.doc_path_for_source(source_filename)
    if not hasattr(fp, "write"):
        # fp is a filename
        path = Path(fp)
        path.parent.mkdir(parents=True, exist_ok=True)
        return write_doc(notebook, source_filename, config, path.open("w"))
    fp = cast(TextIO, fp)
    fp.write(writes_doc(notebook, source_filename, config))
