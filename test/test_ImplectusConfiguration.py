"""Unit tests for ImplectusConfiguration.

The rest of the config module has its own test file.
"""
from pathlib import Path

import pytest

from implectus.config import ImplectusConfiguration


@pytest.mark.parametrize(
    "source,root,expected",
    (
        ("notebooks", "", "notebooks"),
        ("notebooks", ".", "./notebooks"),
        ("/tmp/notebooks", "", "/tmp/notebooks"),
        ("/tmp/notebooks", ".", "/tmp/notebooks"),
        ("notebooks", "/home/implectus", "/home/implectus/notebooks"),
        ("/tmp/notebooks", "/home/implectus", "/tmp/notebooks"),
    ),
)
def test_source_path(source, root, expected):
    cfg = ImplectusConfiguration(source_dir=source, working_dir=root)
    assert cfg.source_path == Path(expected)


@pytest.mark.parametrize(
    "code,root,expected",
    (
        ("package", "", "package"),
        ("package", ".", "./package"),
        ("/tmp/package", "", "/tmp/package"),
        ("/tmp/package", ".", "/tmp/package"),
        ("package", "/home/implectus", "/home/implectus/package"),
        ("/tmp/package", "/home/implectus", "/tmp/package"),
    ),
)
def test_code_path(code, root, expected):
    cfg = ImplectusConfiguration(code_dir=code, working_dir=root)
    assert cfg.code_path == Path(expected)


@pytest.mark.parametrize(
    "doc,root,expected",
    (
        ("doc", "", "doc"),
        ("doc", ".", "./doc"),
        ("/tmp/doc", "", "/tmp/doc"),
        ("/tmp/doc", ".", "/tmp/doc"),
        ("doc", "/home/implectus", "/home/implectus/doc"),
        ("/tmp/doc", "/home/doc", "/tmp/doc"),
    ),
)
def test_doc_path(doc, root, expected):
    cfg = ImplectusConfiguration(doc_dir=doc, working_dir=root)
    assert cfg.doc_path == Path(expected)


@pytest.mark.parametrize(
    "path,source,root,expected",
    (
        # Relative paths
        ("notebooks/main.py", "notebooks", "", True),
        ("main.py", "notebooks", "", False),
        ("main.py", ".", "", True),
        # Absolute paths
        ("/tmp/main.py", "notebooks", "/tmp", False),
        ("/tmp/notebooks/main.py", "notebooks", "/tmp", True),
        ("main.py", "notebooks", "/tmp", False),
        ("notebooks/main.py", "notebooks", "/tmp", False),
        # No source dir specified
        ("main.py", "", "", False),
        ("main.py", "", ".", False),
        ("/tmp/notebooks/main.py", "", "", False),
        ("/tmp/notebooks/main.py", "", "/tmp", False),
        ("/tmp/main.py", "", "/tmp", False),
    ),
)
@pytest.mark.filterwarnings(
    "ignore:Candidate paths must be absolute:implectus.config.ImplectusConfigWarning"
)
def test_should_process(path, source, root, expected):
    cfg = ImplectusConfiguration(source_dir=source, working_dir=root)
    assert cfg.should_process(path) == expected


# TODO: remove this and maintain coverage through public interface
@pytest.mark.parametrize(
    "path,source,root,expected",
    (
        # No source path
        ("main.py", "", "", None),
        ("notebooks/main.py", "", "", None),
        # Absolute paths
        ("/tmp/notebooks/main.py", "/tmp/notebooks", "", "main.py"),
        ("/tmp/notebooks/main.py", "notebooks", "/tmp", "main.py"),
        ("notebooks/main.py", "notebooks", "/tmp", None),
        ("notebooks/main.py", "", "/tmp", None),
        # Relative paths
        ("notebooks/main.py", "notebooks", "", "main.py"),
        ("./notebooks/main.py", "notebooks", "", "main.py"),
        ("notebooks/module/main.py", "notebooks", "", "module/main.py"),
    ),
)
@pytest.mark.filterwarnings(
    "ignore:Candidate paths must be absolute:implectus.config.ImplectusConfigWarning"
)
def test_relative_path_to_source(path, source, root, expected):
    if expected is not None:
        expected = Path(expected)
    cfg = ImplectusConfiguration(source_dir=source, working_dir=root)
    assert cfg._relative_path_to_source(path) == expected


@pytest.mark.parametrize(
    "path,source,root",
    (
        ("/home/implectus/notebooks/main.py", "/tmp/notebooks", "."),
        ("/home/implectus/notebooks/main.py", "notebooks", "/tmp"),
    ),
)
def test_relative_path_to_source_invalid(path, source, root):
    cfg = ImplectusConfiguration(source_dir=source, working_dir=root)
    with pytest.raises(ValueError):
        cfg._relative_path_to_source(path)


@pytest.mark.parametrize("export_package", (True, False))
@pytest.mark.parametrize(
    "path,source,code,expected",
    (
        # Missing source path or code path
        ("main.py", "", "package", None),
        ("main.ipynb", "", "package", None),
        ("notebooks/main.py", "notebooks", "", None),
        ("notebooks/main.ipynb", "notebooks", "", None),
        ("notebooks/module/main.py", "notebooks", "", None),
        ("notebooks/module/main.ipynb", "notebooks", "", None),
        # Valid versions of above
        ("main.py", ".", "package", "package/main.py"),
        ("main.ipynb", ".", "package", "package/main.py"),
        ("notebooks/main.py", "notebooks", ".", "main.py"),
        ("notebooks/main.ipynb", "notebooks", ".", "main.py"),
        ("notebooks/module/main.py", "notebooks", ".", "module/main.py"),
        ("notebooks/module/main.ipynb", "notebooks", ".", "module/main.py"),
        # Other valid cases
        ("notebooks/main.py", "notebooks", "package", "package/main.py"),
        ("notebooks/module/main.py", "notebooks", "package", "package/module/main.py"),
        ("notebooks/main.ipynb", "notebooks", "package", "package/main.py"),
        (
            "notebooks/module/main.ipynb",
            "notebooks",
            "package",
            "package/module/main.py",
        ),
    ),
)
def test_code_path_for_source(path, source, code, expected, export_package):
    if expected is not None:
        expected = Path(expected)
    cfg = ImplectusConfiguration(
        source_dir=source, code_dir=code, export_code_as_package=export_package
    )
    assert cfg.code_path_for_source(path) == expected


@pytest.mark.parametrize(
    "path,source,code,root,expected",
    (
        # Missing source path or code path
        ("main.py", "", "package", "", None),
        ("/tmp/main.py", "", "package", "/tmp", None),
        # Valid
        ("main.py", ".", "package", "", "package.main"),
        ("/tmp/main.py", ".", "package", "/tmp", "package.main"),
        ("notebooks/main.py", "notebooks", "package", "", "package.main"),
        ("notebooks/module/main.py", "notebooks", "package", "", "package.module.main"),
    ),
)
def test_module_name_with_package(path, source, code, root, expected):
    cfg = ImplectusConfiguration(
        source_dir=source, code_dir=code, working_dir=root, export_code_as_package=True
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
    cfg = ImplectusConfiguration(
        source_dir=source, code_dir=code, working_dir=root, export_code_as_package=True
    )
    with pytest.raises(ValueError):
        cfg.module_name(path)


@pytest.mark.parametrize(
    "path,source,code,expected",
    (
        # Missing source path
        ("main.py", "", "", None),
        ("main.py", "", "code", None),
        # Missing code path
        ("main.ipynb", ".", "", "main"),
        ("notebooks/main.py", "notebooks", "", "main"),
        ("notebooks/subdir/main.py", "notebooks", "", "main"),
        # Also valid
        ("main.ipynb", ".", ".", "main"),
        ("main.py", ".", "code", "main"),
        ("notebooks/main.py", "notebooks", ".", "main"),
        ("notebooks/subdir/main.py", "notebooks", ".", "main"),
        ("notebooks/subdir/main.py", "notebooks", "code", "main"),
    ),
)
def test_module_name_without_package(path, source, code, expected):
    cfg = ImplectusConfiguration(
        source_dir=source, code_dir=code, export_code_as_package=False
    )
    assert cfg.module_name(path) == expected


@pytest.mark.parametrize(
    "path,source,doc,expected",
    (
        # Missing source path or doc path
        ("notebooks/main.py", "notebooks", "", None),
        ("main.py", "", "doc", None),
        ("notebooks/module/main.py", "notebooks", "", None),
        # Valid
        ("notebooks/main.py", "notebooks", ".", "main.ipynb"),
        ("main.py", ".", "doc", "doc/main.ipynb"),
        ("notebooks/module/main.py", "notebooks", ".", "module/main.ipynb"),
        ("notebooks/main.py", "notebooks", "doc", "doc/main.ipynb"),
        ("notebooks/module/main.py", "notebooks", "doc", "doc/module/main.ipynb"),
    ),
)
def test_doc_path_for_source(path, source, doc, expected):
    if expected is not None:
        expected = Path(expected)
    cfg = ImplectusConfiguration(source_dir=source, doc_dir=doc)
    assert cfg.doc_path_for_source(path) == expected


# TODO: test with root path above working directory
