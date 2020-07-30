"""Integration tests for export module."""

import sys
import textwrap

import jupytext
import pytest

from myst_literate.config import LiterateConfiguration
from myst_literate.main import write_code, write_doc


@pytest.fixture
def config(tmpdir):
    return LiterateConfiguration(root_dir=str(tmpdir))


source = textwrap.dedent(
    """\
    # # Title

    # + tags=["export"]
    def hello():
        print("Hello world")
        return True
    # -

    hello()
    """
)


def test_write_code(config):
    config.source_dir = "notebooks"
    config.code_dir = "package"
    nb = jupytext.reads(source, fmt="py:light",)
    write_code(nb, config.root_path / "notebooks" / "main.py", config)

    expected = textwrap.dedent(
        """\
        def hello():
            print("Hello world")
            return True
        """
    )
    assert (config.root_path / "package" / "main.py").read_text() == expected
    sys.path.append(str(config.root_path))
    import package.main  # noqa: I900

    assert package.main.hello()


def test_write_doc(config):
    config.source_dir = "notebooks"
    config.code_dir = "package"
    config.doc_dir = "doc"
    config.export_code_as_package = True
    nb = jupytext.reads(source, fmt="py:light",)
    write_doc(nb, config.root_path / "notebooks" / "main.py", config)
    result = jupytext.read(config.root_path / "doc" / "main.ipynb")
    actual = jupytext.writes(result, fmt="py:light")

    expected = textwrap.dedent(
        """\
        # ```{py:currentmodule} package.main```

        # # Title

        # ```{autofunction} hello```

        # + tags=["export", "remove-input"]
        def hello():
            print("Hello world")
            return True
        # -

        hello()
        """
    )
    assert actual == expected
