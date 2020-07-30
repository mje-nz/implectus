import textwrap

import jupytext
import pytest

from myst_literate import FileContentsManager


@pytest.fixture
def cm(tmpdir):
    return FileContentsManager(root_dir=str(tmpdir))


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


def test_load_save(cm):
    cm.source_dir = "notebooks"
    cm.code_dir = "package"
    cm.doc_dir = "doc"
    cm.export_code_as_package = True
    cm.source_path.mkdir()
    cm.source_path.joinpath("main.py").write_text(source)

    nb = cm.get("notebooks/main.py")
    cm.save(model=nb, path="notebooks/main.py")

    assert (cm.root_path / "notebooks" / "main.py").read_text() == source
    assert (cm.root_path / "package" / "main.py").read_text() == code
    doc_nb = jupytext.read(cm.root_path / "doc" / "main.ipynb")
    assert jupytext.writes(doc_nb, fmt="py:light") == doc
