import copy
from pathlib import Path
from typing import Union, cast
from typing.io import TextIO

import jupytext
from nbformat import NotebookNode

from .config import LiterateConfiguration
from .export_code import relativize_imports, should_export
from .export_doc import document_cell, documented_names, should_document
from .util import concat, nb_cell


def _jupytext_writes(notebook: NotebookNode, fmt: str, **kwargs):
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


def writes_code(
    notebook: NotebookNode,
    source_filename: Union[str, Path],
    config: LiterateConfiguration,
):
    """Write the code for the given source file to a string.

    The format is given by config.code_format.

    Args:
        notebook: The notebook to write.
        source_filename: Full path of the file from which notebook was read.
        config: The Literate configuration.
    """
    nb = copy.deepcopy(notebook)

    nb.cells = [cell for cell in nb.cells if should_export(cell)]
    if config.export_code_as_package:
        nb.cells = [
            relativize_imports(cell, config.module_name(source_filename))
            for cell in nb.cells
        ]

    nb.metadata.get("jupytext", {})["notebook_metadata_filter"] = "-all"
    return _jupytext_writes(nb, config.code_format)


def write_code(
    notebook: NotebookNode,
    source_filename: Union[str, Path],
    config: LiterateConfiguration,
    fp: Union[str, Path, TextIO] = None,
):
    """Write the code for the given source file to a file.

    The format is given by config.code_format.

    Args:
        notebook: The notebook to write.
        source_filename: Full path of the file from which notebook was read.
        config: The Literate configuration.
        fp: Any file-like object with a write method that accepts Unicode, or a path to
            write a file, or None to determine the destination filename automatically.
    """
    if fp is None:
        fp = config.code_path_for_source(source_filename)
    if not hasattr(fp, "write"):
        # fp is a filename
        path = Path(fp)
        path.parent.mkdir(parents=True, exist_ok=True)
        return write_code(notebook, source_filename, config, path.open("w"))
    fp = cast(TextIO, fp)
    fp.write(writes_code(notebook, source_filename, config))


def writes_doc(
    notebook: NotebookNode,
    source_filename: Union[str, Path],
    config: LiterateConfiguration,
):
    """Write the documentation for the given source file to a string.

    The format is given by config.doc_format.

    Args:
        notebook: The notebook to write.
        source_filename: Full path of the file from which notebook was read.
        config: The Literate configuration.
    """
    nb = copy.deepcopy(notebook)

    # Insert py:currentmodule directive for autodoc
    directive = "```{py:currentmodule} %s```" % config.module_name(source_filename)
    nb.cells.insert(0, nb_cell("markdown", {}, directive))

    nb.cells = [cell for cell in nb.cells if should_document(cell)]
    documented_names_ = concat(documented_names(cell) for cell in nb.cells)
    nb.cells = concat(document_cell(cell, documented_names_) for cell in nb.cells)

    return _jupytext_writes(nb, config.doc_format)


def write_doc(
    notebook: NotebookNode,
    source_filename: Union[str, Path],
    config: LiterateConfiguration,
    fp: Union[str, Path, TextIO] = None,
):
    """Write the documentation for the given source file to a file.

    The format is given by config.doc_format.

    Args:
        notebook: The notebook to write.
        source_filename: Full path of the file from which notebook was read.
        config: The Literate configuration.
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


# TODO sanity checks:
#   imports are translatable
#   no conflicting tags


def sync(config: LiterateConfiguration):
    """Export code and doc for each file in the source directory."""
    if not config.source_dir:
        return
    sources = [
        path for path in config.source_path.glob("**/*") if config.should_process(path)
    ]
    for source in sources:
        nb = jupytext.read(source)
        if config.code_dir:
            write_code(nb, source, config)
        if config.doc_dir:
            write_doc(nb, source, config)


# TODO: CLI
