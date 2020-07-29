import copy
import importlib
import itertools
from pathlib import Path
import re
import sys
import types

import jupytext
from nbformat import NotebookNode


def nb_cell(cell_type, metadata=None, source=""):
    return NotebookNode({
        "cell_type": cell_type,
        "metadata": metadata or {},
        "source": source
    })


def should_export(cell):
    tags = cell.metadata.get("tags", {})
    return "export" in tags or "export-internal" in tags


def relative_import(name, current_module):
    """Return the relative name for 'name' when imported from 'current_module'."""
    name = name.split(".")
    current_module = current_module.split(".")
    assert len(current_module) > 1
    parent_module = current_module[:-1]
    common_part = list(itertools.takewhile(
        lambda x: x[0] == x[1],
        zip(name, parent_module)
    ))
    if len(common_part) == 0:
        # name is not in the same package as current_module
        return ".".join(name)
    common_ancestor_name = "." * (len(current_module) - len(common_part))
    return common_ancestor_name + ".".join(name[len(common_part):])


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
        r"^(\s*from )({}\.?\S*)( import .*)$".format(package_name),
        flags=re.MULTILINE)
    cell.source = re_import.sub(
        lambda m: "".join((m[1], relative_import(m[2], module_name), m[3])),
        cell.source
    )
    return cell


_re_function_def = re.compile(r"^(?:async\s+)?def\s+([^\(\s]+)\s*\(", re.MULTILINE)
_re_class_def = re.compile(r"^class\s+([^\(\s]+)\s*(?:\(|:)", re.MULTILINE)


def is_private(name):
    return name.startswith("_")


def exported_names(cell):
    if cell.cell_type != "code" or not should_export(cell):
        return []
    functions = _re_function_def.findall(cell.source)
    classes = _re_class_def.findall(cell.source)
    names = [(f, "function") for f in functions] + [(c, "class") for c in classes]
    return [(name, type_) for (name, type_) in names if not is_private(name)]


def should_document(cell):
    tags = cell.metadata.get("tags", {})
    return "export-internal" not in tags and "remove-cell" not in tags


_directives = "module|function|data|exception|class|decorator"
_re_sphinx_directive = re.compile(
    r"^\s*```\s*{(?:py:|auto)?(?:%s)}\s+([^`\s(]*).*?```" % _directives,
    re.MULTILINE | re.DOTALL
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
            cells.insert(0, nb_cell("markdown", {}, "\n".join(directives)))
    return cells


def concat(iterable):
    """Concatenate each element in an iterable of iterables into a list."""
    return list(itertools.chain(*iterable))


class Module:

    def __init__(self, path, notebook_root, package_root, doc_root=None, fp=None):
        """Read a module from a file of any type Jupytext supports.

        Args:
            path: Path of notebook to read.
            notebook_root: Folder containing notebooks.
            package_root: Root folder of package to export into.
            doc_root: Folder to export documentation notebooks into.
            fp: File-like object to read notebook from (for testing).
        """
        self._notebook_root = Path(notebook_root)
        try:
            self._notebook_filename = Path(path).relative_to(self._notebook_root)
        except ValueError as e:
            raise ValueError("Notebook must be inside notebook root") from e
        self._package_root = Path(package_root)
        self._doc_root = Path(doc_root)
        if not fp:
            fp = open(path)
        self._nb = jupytext.read(fp, fmt=self._notebook_filename.suffix)

    @property
    def _module_path(self):
        """Path of exported module."""
        return self._package_root/self._notebook_filename.with_suffix(".py")

    @property
    def _module_name(self):
        """Dotted name of exported module."""
        return ".".join(self._module_path.with_suffix("").parts)

    @property
    def _doc_path(self):
        """Path of exported documentation notebook."""
        return self._doc_root/self._notebook_filename.with_suffix(".ipynb")

    def export_to_package(self, fp=None):
        """Export the cells marked for export into a module in the given package.

        Args:
            fp: File-like object to write module to (for testing).
        """
        nb = copy.deepcopy(self._nb)

        nb.cells = [cell for cell in nb.cells if should_export(cell)]
        nb.cells = [relativize_imports(cell, self._module_name) for cell in nb.cells]

        if not fp:
            self._module_path.parent.mkdir(parents=True, exist_ok=True)
            fp = self._module_path.open("w")
        nb.metadata.get("jupytext", {})["notebook_metadata_filter"] = "-all"
        jupytext.write(nb, fp, fmt="py:nomarker")

    def preprocess_for_doc(self, fp=None):
        """Preprocess a notebook and write into documentation folder.

        Args:
            fp: File-like object to output notebook to (for testing).
        """
        nb = copy.deepcopy(self._nb)

        # Insert py:currentmodule directive for autodoc
        directive = "```{py:currentmodule} %s```" % self._module_name
        nb.cells.insert(0, nb_cell("markdown", {}, directive))

        nb.cells = [cell for cell in nb.cells if should_document(cell)]
        documented_names_ = concat(documented_names(cell) for cell in nb.cells)
        nb.cells = concat(document_cell(cell, documented_names_) for cell in nb.cells)

        if not fp:
            fp = self._doc_path.open("w")
        jupytext.write(nb, fp, fmt="ipynb")


# TODO sanity checks:
#   imports are translatable
#   no conflicting tags


def main(notebook_filename, notebook_root, package_root, doc_root):
    module = Module(notebook_filename, notebook_root, package_root, doc_root)
    module.export_to_package()
    module.preprocess_for_doc()


# TODO: test
