import copy
from pathlib import Path

import jupytext

from .export_code import relativize_imports, should_export
from .export_doc import document_cell, documented_names, should_document
from .util import concat, nb_cell


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
        return self._package_root / self._notebook_filename.with_suffix(".py")

    @property
    def _module_name(self):
        """Dotted name of exported module."""
        return ".".join(self._module_path.with_suffix("").parts)

    @property
    def _doc_path(self):
        """Path of exported documentation notebook."""
        return self._doc_root / self._notebook_filename.with_suffix(".ipynb")

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
