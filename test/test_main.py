"""Unit tests for main module."""

import textwrap

import jupytext

from implectus.config import ImplectusConfiguration
from implectus.main import writes_code, writes_doc

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


def test_writes_code():
    cfg = ImplectusConfiguration(source_dir=".", code_dir="package")
    nb = jupytext.reads(source, fmt="py:light")
    actual = writes_code(nb, "main.py", cfg)

    expected = textwrap.dedent(
        """\
        def hello():
            print("Hello world")
        """
    )
    assert actual == expected


def test_writes_doc():
    cfg = ImplectusConfiguration(
        source_dir=".", code_dir="package", export_code_as_package=True
    )
    nb = jupytext.reads(source, fmt="py:light")
    result = writes_doc(nb, "main.py", cfg)
    actual = jupytext.writes(jupytext.reads(result, fmt=cfg.doc_format), fmt="py:light")

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
    assert actual == expected
