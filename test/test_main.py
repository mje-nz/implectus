"""Unit tests for main module."""

import io
import textwrap
from pathlib import Path

import jupytext
import pytest

from myst_literate.main import Module


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
