"""Integration tests for export module."""

import sys
import textwrap
from pathlib import Path

import jupytext
import pytest

from implectus.config import ImplectusConfiguration
from implectus.main import sync, write_code, write_doc

from .util import code_equal, doc_equal


@pytest.fixture
def config(tmpdir_cd):
    return ImplectusConfiguration(
        source_dir="notebooks",
        code_dir="package",
        doc_dir="doc",
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
    # # Autogenerated from `notebooks/main.py`
    # This file was created by Implectus 0.0.1.  Do not edit this file;
    # edit `notebooks/main.py` instead.

    def hello():
        print("Hello world")
        return True
    """
)
doc = textwrap.dedent(
    """\
    # # Autogenerated from `notebooks/main.py`
    # This file was created by Implectus 0.0.1.  Do not edit this file;
    # edit `notebooks/main.py` instead.

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
    write_code(nb, "notebooks/main.py", config)

    assert code_equal("package/main.py", code)

    sys.path.append(str(config.working_path))
    import package.main  # noqa: I900

    assert package.main.hello()


def test_write_doc(config):
    nb = jupytext.reads(source, fmt="py:light",)
    write_doc(nb, "notebooks/main.py", config)

    assert doc_equal("doc/main.ipynb", doc)


def test_sync(config):
    config.source_path.mkdir()
    Path("notebooks/main.py").write_text(source)
    sync(config)

    assert Path("notebooks/main.py").read_text() == source
    assert code_equal("package/main.py", code)
    assert doc_equal("doc/main.ipynb", doc)


# TODO: try everything by changing root dir and by changing working dir
