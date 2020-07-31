"""Integration tests for export module."""

import sys
import textwrap

import jupytext
import pytest

from myst_literate.config import LiterateConfiguration
from myst_literate.main import sync, write_code, write_doc


@pytest.fixture
def config(tmpdir):
    return LiterateConfiguration(
        source_dir="notebooks",
        code_dir="package",
        doc_dir="doc",
        root_dir=str(tmpdir),
        export_code_as_package=True,
    )


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
code = textwrap.dedent(
    """\
    def hello():
        print("Hello world")
        return True
    """
)
doc = textwrap.dedent(
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


def test_write_code(config):
    nb = jupytext.reads(source, fmt="py:light",)
    write_code(nb, config.root_path / "notebooks" / "main.py", config)

    assert (config.root_path / "package" / "main.py").read_text() == code

    sys.path.append(str(config.root_path))
    import package.main  # noqa: I900

    assert package.main.hello()


def test_write_doc(config):
    nb = jupytext.reads(source, fmt="py:light",)
    write_doc(nb, config.root_path / "notebooks" / "main.py", config)

    result = jupytext.read(config.root_path / "doc" / "main.ipynb")
    assert jupytext.writes(result, fmt="py:light") == doc


def test_sync(config):
    config.source_path.mkdir()
    (config.root_path / "notebooks" / "main.py").write_text(source)
    sync(config)

    assert (config.root_path / "notebooks" / "main.py").read_text() == source
    assert (config.root_path / "package" / "main.py").read_text() == code
    doc_result = jupytext.read(config.root_path / "doc" / "main.ipynb")
    assert jupytext.writes(doc_result, fmt="py:light") == doc


# TODO: try everything by changing root dir and by changing working dir
