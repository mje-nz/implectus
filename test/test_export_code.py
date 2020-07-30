"""Unit tests for export_code module."""

import pytest

from myst_literate.export_code import relative_import, relativize_imports, should_export
from myst_literate.util import nb_cell as cell


class TestShouldExport:

    """Tests for should_export function."""

    def test_export(self):
        assert should_export(cell("code", {"tags": ["export"]}, "pass"))

    def test_export_internal(self):
        assert should_export(cell("code", {"tags": ["export-internal"]}, "pass"))

    def test_untagged(self):
        assert not should_export(cell("code", {}, "pass"))

    @pytest.mark.parametrize("cell_type", ("markdown", "raw"))
    def test_noncode(self, cell_type):
        assert not should_export(cell(cell_type, {}, "pass"))


class TestRelativeImport:

    """Tests for relative_import function."""

    @pytest.mark.parametrize(
        "name,expected",
        (
            ("package", "."),
            ("package.sibling", ".sibling"),
            ("package.sibling.niece", ".sibling.niece"),
            ("other_package", "other_package"),
        ),
    )
    def test_simple(self, name, expected):
        assert relative_import(name, "package.module") == expected

    @pytest.mark.parametrize(
        "name,expected",
        (
            ("package", ".."),
            ("package.aunt", "..aunt"),
            ("package.aunt.cousin", "..aunt.cousin"),
            ("package.parent", "."),
            ("package.parent.sibling", ".sibling"),
            ("package.parent.sibling.niece", ".sibling.niece"),
            ("other_package", "other_package"),
        ),
    )
    def test_parent(self, name, expected):
        assert relative_import(name, "package.parent.module") == expected


class TestRelativizeImports:

    """Tests for relativize_imports function."""

    @pytest.mark.parametrize(
        "in_,out",
        (
            ("from package import name", "from . import name"),
            ("from package import name1, name2", "from . import name1, name2"),
            (
                "from package import name1 as name, name2",
                "from . import name1 as name, name2",
            ),
            ("from package.sibling import name", "from .sibling import name"),
            (
                "from other_package.module import name",
                "from other_package.module import name",
            ),
            (
                "from package.sibling.niece import name",
                "from .sibling.niece import name",
            ),
            ("from other_package import name", "from other_package import name"),
        ),
    )
    def test_simple(self, in_, out):
        input_cell = cell("code", {}, in_)
        output_cell = relativize_imports(input_cell, "package.module")
        assert output_cell.source == out

    @pytest.mark.parametrize(
        "in_,out",
        (
            ("from package import name", "from .. import name"),
            ("from package.aunt import name", "from ..aunt import name"),
            ("from package.aunt.cousin import name", "from ..aunt.cousin import name"),
            ("from package.parent import name", "from . import name"),
            ("from package.parent.sibling import name", "from .sibling import name"),
            (
                "from package.parent.sibling.niece import name",
                "from .sibling.niece import name",
            ),
            ("from other_package import name", "from other_package import name"),
        ),
    )
    def test_parent(self, in_, out):
        input_cell = cell("code", {}, in_)
        output_cell = relativize_imports(input_cell, "package.parent.module")
        assert output_cell.source == out


# TODO: exported_names
