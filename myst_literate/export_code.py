"""Helper functions for exporting code."""
import itertools
import re

from .util import is_private


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
        r"^(\s*from )({}\.?\S*)( import .*)$".format(package_name), flags=re.MULTILINE
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
