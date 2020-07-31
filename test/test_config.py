from pathlib import Path

import pytest

from myst_literate.config import LiterateConfiguration


@pytest.mark.parametrize(
    "source,root,expected",
    (
        ("notebooks", "", "notebooks"),
        ("notebooks", ".", "./notebooks"),
        ("/tmp/notebooks", "", "/tmp/notebooks"),
        ("/tmp/notebooks", ".", "/tmp/notebooks"),
        ("notebooks", "/home/literate", "/home/literate/notebooks"),
        ("/tmp/notebooks", "/home/literate", "/tmp/notebooks"),
    ),
)
def test_source_path(source, root, expected):
    cfg = LiterateConfiguration(source_dir=source, root_dir=root)
    assert cfg.source_path == Path(expected)


@pytest.mark.parametrize(
    "code,root,expected",
    (
        ("package", "", "package"),
        ("package", ".", "./package"),
        ("/tmp/package", "", "/tmp/package"),
        ("/tmp/package", ".", "/tmp/package"),
        ("package", "/home/literate", "/home/literate/package"),
        ("/tmp/package", "/home/literate", "/tmp/package"),
    ),
)
def test_code_path(code, root, expected):
    cfg = LiterateConfiguration(code_dir=code, root_dir=root)
    assert cfg.code_path == Path(expected)


@pytest.mark.parametrize(
    "doc,root,expected",
    (
        ("doc", "", "doc"),
        ("doc", ".", "./doc"),
        ("/tmp/doc", "", "/tmp/doc"),
        ("/tmp/doc", ".", "/tmp/doc"),
        ("doc", "/home/literate", "/home/literate/doc"),
        ("/tmp/doc", "/home/doc", "/tmp/doc"),
    ),
)
def test_doc_path(doc, root, expected):
    cfg = LiterateConfiguration(doc_dir=doc, root_dir=root)
    assert cfg.doc_path == Path(expected)


@pytest.mark.parametrize(
    "path,source,root,expected",
    (
        ("notebooks/main.py", "notebooks", "", True),
        ("main.py", "notebooks", "", False),
        ("main.py", ".", "", True),
        ("main.py", "", ".", True),
        ("main.py", "", "", True),
        ("/tmp/notebooks/main.py", "notebooks", "/tmp", True),
        ("notebooks/main.py", "notebooks", "/tmp", True),
        ("/tmp/notebooks/main.py", "", "", False),
    ),
)
def test_should_process(path, source, root, expected):
    cfg = LiterateConfiguration(source_dir=source, root_dir=root)
    assert cfg.should_process(path) == expected


@pytest.mark.parametrize(
    "path,source,root,expected",
    (
        ("notebooks/main.py", "notebooks", "", "main.py"),
        ("./notebooks/main.py", "notebooks", "", "main.py"),
        ("notebooks/module/main.py", "notebooks", "", "module/main.py"),
        ("/tmp/notebooks/main.py", "/tmp/notebooks", "", "main.py"),
        ("/tmp/notebooks/main.py", "notebooks", "/tmp", "main.py"),
    ),
)
def test_relative_path_to_source(path, source, root, expected):
    cfg = LiterateConfiguration(source_dir=source, root_dir=root)
    assert cfg.relative_path_to_source(path) == Path(expected)


@pytest.mark.parametrize(
    "path,source,root",
    (
        ("/home/literate/notebooks/main.py", "/tmp/notebooks", "."),
        ("/home/literate/notebooks/main.py", "notebooks", "/tmp"),
    ),
)
def test_relative_path_to_source_invalid(path, source, root):
    cfg = LiterateConfiguration(source_dir=source, root_dir=root)
    with pytest.raises(ValueError):
        cfg.relative_path_to_source(path)


@pytest.mark.parametrize("export_package", (True, False))
@pytest.mark.parametrize(
    "path,source,code,expected",
    (
        ("notebooks/main.py", "notebooks", "", "main.py"),
        ("main.py", "", "package", "package/main.py"),
        ("notebooks/main.py", "notebooks", "package", "package/main.py"),
        ("notebooks/module/main.py", "notebooks", "", "module/main.py"),
        ("notebooks/module/main.py", "notebooks", "package", "package/module/main.py"),
        ("notebooks/main.ipynb", "notebooks", "", "main.py"),
        ("main.ipynb", "", "package", "package/main.py"),
        ("notebooks/main.ipynb", "notebooks", "package", "package/main.py"),
        ("notebooks/module/main.ipynb", "notebooks", "", "module/main.py"),
        (
            "notebooks/module/main.ipynb",
            "notebooks",
            "package",
            "package/module/main.py",
        ),
    ),
)
def test_code_path_for_source(path, source, code, expected, export_package):
    cfg = LiterateConfiguration(
        source_dir=source, code_dir=code, export_code_as_package=export_package
    )
    assert cfg.code_path_for_source(path) == Path(expected)


@pytest.mark.parametrize(
    "path,source,code,root,expected",
    (
        ("main.py", "", "package", "", "package.main"),
        ("notebooks/main.py", "notebooks", "package", "", "package.main"),
        ("/tmp/main.py", "", "package", "/tmp", "package.main"),
        ("notebooks/module/main.py", "notebooks", "package", "", "package.module.main"),
    ),
)
def test_module_name_with_package(path, source, code, root, expected):
    cfg = LiterateConfiguration(
        source_dir=source, code_dir=code, root_dir=root, export_code_as_package=True
    )
    assert cfg.module_name(path) == expected


@pytest.mark.parametrize(
    "path,source,code,root",
    (
        ("main.py", "", "", ""),
        ("/tmp/main.py", "", "", "/tmp"),
        ("notebooks/module/main.py", "notebooks", "", ""),
    ),
)
def test_module_name_with_package_invalid(path, source, code, root):
    cfg = LiterateConfiguration(
        source_dir=source, code_dir=code, root_dir=root, export_code_as_package=True
    )
    with pytest.raises(ValueError):
        cfg.module_name(path)


@pytest.mark.parametrize(
    "path,source,code,expected",
    (
        ("main.py", "", "", "main"),
        ("notebooks/main.py", "notebooks", "", "main"),
        ("main.py", "", "code", "main"),
        ("notebooks/subdir/main.py", "notebooks", "", "main"),
        ("notebooks/subdir/main.py", "notebooks", "code", "main"),
    ),
)
def test_module_name_without_package(path, source, code, expected):
    cfg = LiterateConfiguration(
        source_dir=source, code_dir=code, export_code_as_package=False
    )
    assert cfg.module_name(path) == expected


@pytest.mark.parametrize(
    "path,source,doc,expected",
    (
        ("notebooks/main.py", "notebooks", "", "main.ipynb"),
        ("main.py", "", "doc", "doc/main.ipynb"),
        ("notebooks/main.py", "notebooks", "doc", "doc/main.ipynb"),
        ("notebooks/module/main.py", "notebooks", "", "module/main.ipynb"),
        ("notebooks/module/main.py", "notebooks", "doc", "doc/module/main.ipynb"),
    ),
)
def test_doc_path_for_source(path, source, doc, expected):
    cfg = LiterateConfiguration(source_dir=source, doc_dir=doc)
    assert cfg.doc_path_for_source(path) == Path(expected)


# TODO: test with root path above working directory
