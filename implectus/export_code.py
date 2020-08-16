"""Helper functions for exporting code."""
import copy
import itertools
import re
from pathlib import Path
from typing import Union, cast
from typing.io import TextIO

from nbformat import NotebookNode

from .config import ImplectusConfiguration
from .util import implectus_header_cell, is_private, jupytext_writes


def should_export(cell):
    tags = cell.metadata.get("tags", {})
    return "export" in tags or "export-internal" in tags


def relative_import(name, current_module):
    """Return the relative name for 'name' when imported from 'current_module'."""
    name = name.split(".")
    current_module = current_module.split(".")
    assert len(current_module) > 1
    parent_module = current_module[:-1]
    common_part = list(
        itertools.takewhile(lambda x: x[0] == x[1], zip(name, parent_module))
    )
    if len(common_part) == 0:
        # name is not in the same package as current_module
        return ".".join(name)
    common_ancestor_name = "." * (len(current_module) - len(common_part))
    return common_ancestor_name + ".".join(name[len(common_part) :])


def relativize_imports(cell, module_name):
    """Turn imports from the package containing module_name into relative imports.

    Note that there's no way to make ```import package``` into a relative import,
    and doing it for ```import package.sibling``` is more work than I care to do, so
    only ```from package[.sibling]```-style imports are supported.
    """
    if cell.cell_type != "code":
        return cell
    # TODO: warn on absolute imports
    package_name = module_name.split(".")[0]
    re_import = re.compile(
        rf"^(\s*from )({package_name}\.?\S*)( import .*)$", flags=re.MULTILINE
    )
    cell.source = re_import.sub(
        lambda m: "".join((m[1], relative_import(m[2], module_name), m[3])), cell.source
    )
    return cell


_re_function_def = re.compile(r"^(?:async\s+)?def\s+([^\(\s]+)\s*\(", re.MULTILINE)
_re_class_def = re.compile(r"^class\s+([^\(\s]+)\s*(?:\(|:)", re.MULTILINE)


def exported_names(cell):
    if cell.cell_type != "code" or not should_export(cell):
        return []
    functions = _re_function_def.findall(cell.source)
    classes = _re_class_def.findall(cell.source)
    names = [(f, "function") for f in functions] + [(c, "class") for c in classes]
    return [(name, type_) for (name, type_) in names if not is_private(name)]


def writes_code(
    notebook: NotebookNode,
    source_filename: Union[str, Path],
    config: ImplectusConfiguration,
):
    """Write the code for the given source file to a string.

    The format is given by config.code_format.

    Args:
        notebook: The notebook to write.
        source_filename: Full path of the file from which notebook was read.
        config: The Implectus configuration.
    """
    nb = copy.deepcopy(notebook)

    nb.cells = [cell for cell in nb.cells if should_export(cell)]
    if config.export_code_as_package:
        nb.cells = [
            relativize_imports(cell, config.module_name(source_filename))
            for cell in nb.cells
        ]

    # Insert Implectus header
    nb.cells.insert(0, implectus_header_cell(source_filename))

    nb.metadata.get("jupytext", {})["notebook_metadata_filter"] = "-all"
    return jupytext_writes(nb, config.code_format)


def write_code(
    notebook: NotebookNode,
    source_filename: Union[str, Path],
    config: ImplectusConfiguration,
    fp: Union[str, Path, TextIO] = None,
):
    """Write the code for the given source file to a file.

    The format is given by config.code_format.

    Args:
        notebook: The notebook to write.
        source_filename: Full path of the file from which notebook was read.
        config: The Implectus configuration.
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
