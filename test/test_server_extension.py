import textwrap

import jupytext
import pytest

from myst_literate import LiterateContentsManager
from myst_literate.server_extension import build_literate_contents_manager_class


@pytest.fixture(params=[True, False])
def cm(tmpdir, request):
    should_build = request.param
    if should_build:
        class_ = build_literate_contents_manager_class(jupytext.TextFileContentsManager)
    else:
        class_ = LiterateContentsManager
    return class_(root_dir=str(tmpdir))


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


@pytest.mark.parametrize("path", ("main.py", "notebooks/main.py"))
def test_jupytext_still_works(cm, path):
    cm.source_dir = "notebooks"
    cm.code_dir = "package"
    cm.doc_dir = "doc"
    cm.export_code_as_package = True
    (cm.root_path / path).parent.mkdir(exist_ok=True)

    nb = jupytext.reads(source, fmt="py:light")
    nb.metadata["jupytext"] = dict(
        formats="ipynb,py:light", notebook_metadata_filter="-all"
    )
    model = dict(type="notebook", content=nb, format="json")

    cm.save(model, path)

    assert (cm.root_path / path).read_text() == source
    result_nb = jupytext.read((cm.root_path / path).with_suffix(".ipynb"))
    assert jupytext.writes(result_nb, fmt="py:light") == source
