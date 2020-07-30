"""Helper functions for exporting documentation."""
import re

from .export_code import exported_names
from .util import nb_cell


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
            cells.insert(0, nb_cell("markdown", {}, "\n".join(directives)))
    return cells
