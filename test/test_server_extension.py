import textwrap
from pathlib import Path

import jupytext
import pytest

from implectus import ImplectusContentsManager
from implectus.server_extension import build_implectus_contents_manager_class

from .util import nb_to_py, no_extra_files, write_config


@pytest.fixture(params=[True, False])
def cm(tmpdir_cd, request):
    """Create a temporary directory, change to it, and return a contents manager."""
    should_build = request.param
    if should_build:
        class_ = build_implectus_contents_manager_class(
            jupytext.TextFileContentsManager
        )
    else:
        class_ = ImplectusContentsManager
    cm = class_(
        source_dir="notebooks",
        code_dir="package",
        doc_dir="doc",
        export_code_as_package=True,
    )
    return cm


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


# TODO: put test data into files and parametrize


@pytest.mark.parametrize(
    "path", ("main.py", "src/main.py", "notebooks/main.py", "notebooks/main.ipynb")
)
def test_does_nothing_by_default(tmpdir_cd, path):
    cm = ImplectusContentsManager()
    if len(Path(path).parts) > 1:
        Path(path).parent.mkdir(exist_ok=True, parents=True)
    jupytext.write(jupytext.reads(source, fmt="py:light"), path)

    nb = cm.get("/" + path)
    cm.save(nb, "/" + path)

    assert no_extra_files(expected=[path])


def test_only_code_output(tmpdir_cd):
    cm = ImplectusContentsManager()
    cm.source_dir = "."
    cm.code_dir = "package"
    Path("main.py").write_text(source)

    nb = cm.get("/main.py")
    cm.save(nb, "/main.py")

    assert Path("package/main.py").read_text() == code
    assert no_extra_files(expected=["main.py", "package/main.py"])


def test_only_doc_output(tmpdir_cd):
    cm = ImplectusContentsManager()
    cm.source_dir = "."
    cm.doc_dir = "docs"
    Path("main.py").write_text(source)

    nb = cm.get("/main.py")
    cm.save(nb, "/main.py")

    assert nb_to_py("docs/main.ipynb") == doc.replace("package.", "")
    assert no_extra_files(expected=["main.py", "docs/main.ipynb"])


@pytest.mark.parametrize("path", ("notebooks/main.py", "notebooks/main.ipynb"))
def test_load_save(cm, path):
    cm.source_path.mkdir()
    jupytext.write(jupytext.reads(source, fmt="py:light"), path)

    nb = cm.get("/" + path)
    cm.save(nb, "/" + path)

    assert nb_to_py(path) == source
    assert Path("package/main.py").read_text() == code
    assert nb_to_py("doc/main.ipynb") == doc
    assert no_extra_files(expected=[path, "package/main.py", "doc/main.ipynb"])


# TODO: case where code ends up with front matter


@pytest.mark.parametrize("path", ("main.py", "notebooks/main.py"))
def test_jupytext_still_works(cm, path):
    (cm.working_path / path).parent.mkdir(exist_ok=True)

    nb = jupytext.reads(source, fmt="py:light")
    nb.metadata["jupytext"] = dict(
        formats="ipynb,py:light", notebook_metadata_filter="-all"
    )
    model = dict(type="notebook", content=nb, format="json")

    cm.save(model, "/" + path)

    assert Path(path).read_text() == source
    result_nb = jupytext.read(Path(path).with_suffix(".ipynb"))
    assert jupytext.writes(result_nb, fmt="py:light") == source


# TODO: run Jupytext test suite somehow?


def test_load_save_with_config_file(tmpdir_cd):
    write_config(
        "implectus.yaml",
        dict(
            source_dir="src",
            code_dir="implectus",
            doc_dir="docs",
            export_code_as_package=True,
        ),
    )
    Path("src").mkdir()
    Path("src/main.py").write_text(source)

    cm = ImplectusContentsManager()
    nb = cm.get("/src/main.py")
    cm.save(nb, "/src/main.py")

    assert Path("src/main.py").read_text() == source
    assert Path("implectus/main.py").read_text() == code
    assert nb_to_py("docs/main.ipynb") == doc.replace("package.", "implectus.")
    assert no_extra_files(
        expected=["src/main.py", "implectus/main.py", "docs/main.ipynb"]
    )


def test_load_save_outside_source_dir_with_config_file(tmpdir_cd):
    write_config(
        "implectus.yaml",
        dict(
            source_dir="notebooks",
            code_dir="implectus",
            doc_dir="docs",
            export_code_as_package=True,
        ),
    )
    Path("src").mkdir()
    Path("src/main.py").write_text(source)

    cm = ImplectusContentsManager()
    nb = cm.get("/src/main.py")
    cm.save(nb, "/src/main.py")

    assert Path("src/main.py").read_text() == source
    assert no_extra_files(expected=["src/main.py"])


def test_load_save_with_config_in_subdir(tmpdir_cd):
    Path("src").mkdir()
    write_config(
        "src/implectus.yaml",
        dict(
            source_dir="notebooks",
            code_dir="code",
            doc_dir="docs",
            export_code_as_package=True,
        ),
    )
    Path("src/notebooks").mkdir()
    Path("src/notebooks/main.py").write_text(source)

    cm = ImplectusContentsManager()
    nb = cm.get("/src/notebooks/main.py")
    cm.save(nb, "/src/notebooks/main.py")

    assert Path("src/notebooks/main.py").read_text() == source
    assert Path("src/code/main.py").read_text() == code
    assert nb_to_py("src/docs/main.ipynb") == doc.replace("package.", "code.")
    assert no_extra_files(
        expected=["src/notebooks/main.py", "src/code/main.py", "src/docs/main.ipynb"]
    )
