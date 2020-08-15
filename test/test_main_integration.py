"""Integration tests for export module."""

import sys
import textwrap

import jupytext
import pytest

from implectus.config import ImplectusConfiguration
from implectus.main import sync, write_code, write_doc


# TODO: use tmpdir_cd
@pytest.fixture
def config(tmpdir):
    return ImplectusConfiguration(
        source_dir="notebooks",
        code_dir="package",
        doc_dir="doc",
        working_dir=str(tmpdir),
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
    write_code(nb, config.working_path / "notebooks" / "main.py", config)

    assert (config.working_path / "package" / "main.py").read_text() == code

    sys.path.append(str(config.working_path))
    import package.main  # noqa: I900

    assert package.main.hello()


def test_write_doc(config):
    nb = jupytext.reads(source, fmt="py:light",)
    write_doc(nb, config.working_path / "notebooks" / "main.py", config)

    result = jupytext.read(config.working_path / "doc" / "main.ipynb")
    assert jupytext.writes(result, fmt="py:light") == doc


def test_sync(config):
    config.source_path.mkdir()
    (config.working_path / "notebooks" / "main.py").write_text(source)
    sync(config)

    assert (config.working_path / "notebooks" / "main.py").read_text() == source
    assert (config.working_path / "package" / "main.py").read_text() == code
    doc_result = jupytext.read(config.working_path / "doc" / "main.ipynb")
    assert jupytext.writes(doc_result, fmt="py:light") == doc


# TODO: try everything by changing root dir and by changing working dir
