"""Unit tests for export module."""

import io
import textwrap
from pathlib import Path

import jupytext
import pytest

from myst_literate.export import Module
from myst_literate.export import nb_cell as cell
from myst_literate.export import relative_import, relativize_imports, should_export


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


@pytest.mark.parametrize(
    "path,src",
    (("notebooks/main.py", ""), ("notebooks/main.ipynb", '{"metadata": {}}')),
)
def test_module_properties(path, src):
    module = Module(
        path=path,
        notebook_root="notebooks",
        package_root="package",
        doc_root="doc",
        fp=io.StringIO(src),
    )
    assert module._module_path == Path("package/main.py")
    assert module._module_name == "package.main"
    assert module._doc_path == Path("doc/main.ipynb")


def _test_export_library(
    source,
    expected,
    path="notebooks/main.py",
    notebook_root="notebooks",
    package_root="package",
    doc_root="doc",
):
    """Test exporting a notebook to a module.

    Args:
        source: Notebook source in py:light format.
        expected: Module output.
    """
    source = io.StringIO(source)
    module = Module(path, notebook_root, package_root, doc_root, fp=source)
    # Sanity check
    assert module._nb.metadata.jupytext.text_representation["format_name"] == "light"

    result = io.StringIO()
    module.export_to_package(result)
    assert result.getvalue() == expected


def test_export_library():
    source = textwrap.dedent(
        """\
        # # Title

        # + tags=["export"]
        def hello():
            print("Hello world")
        # -

        hello()
    """
    )
    expected = textwrap.dedent(
        """\
        def hello():
            print("Hello world")
    """
    )
    _test_export_library(source, expected)


def _test_export_doc(
    source,
    expected,
    path="notebooks/main.py",
    notebook_root="notebooks",
    package_root="package",
    doc_root="doc",
):
    """Test preprocessing a notebook for documentation generation.

    Args:
        source: Notebook source in py:light format.
        expected: Notebook output in py:light format.
    """
    source = io.StringIO(source)
    module = Module(path, notebook_root, package_root, doc_root, fp=source)
    # Sanity check
    assert module._nb.metadata.jupytext.text_representation["format_name"] == "light"

    nb = io.StringIO()
    module.preprocess_for_doc(nb)

    # Get back to markdown for comparison
    result_nb = jupytext.reads(nb.getvalue(), fmt="ipynb")
    result = jupytext.writes(result_nb, fmt="py:light")

    assert result == expected


def test_export_doc():
    source = textwrap.dedent(
        """\
        # # Title

        # + tags=["export"]
        def hello():
            print("Hello world")
        # -

        hello()
        """
    )
    expected = textwrap.dedent(
        """\
        # ```{py:currentmodule} package.main```

        # # Title

        # ```{autofunction} hello```

        # + tags=["export", "remove-input"]
        def hello():
            print("Hello world")
        # -

        hello()
        """
    )
    _test_export_doc(source, expected)
