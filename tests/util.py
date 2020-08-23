import json
import re
from pathlib import Path
from typing import Iterable, List

import jupytext
import pytest
import toml
import yaml
from nbformat import NotebookNode

from implectus.config import IMPLECTUS_CONFIG_FILES


@pytest.fixture
def tmpdir_cd(tmpdir):
    """Create a temporary directory and change to it for the duration of the test."""
    with tmpdir.as_cwd():
        yield tmpdir


def write_config(config_file_path, config: dict):
    """Write an Implectus config file in toml, yaml, json, or py format."""
    path = Path(config_file_path)
    path.parent.mkdir(exist_ok=True, parents=True)
    if path.suffix == ".py":
        config_src = [f'c.{k} = "{v}"' for (k, v) in config.items()]
        path.write_text("\n".join(config_src))
    else:
        with path.open("w") as f:
            if path.suffix == ".yaml" or path.suffix == ".yml":
                yaml.dump(config, f)
            elif path.suffix == ".json":
                json.dump(config, f)
            else:
                toml.dump(config, f)


def nb_to_py(path, strip_metadata=True):
    """Return the contents of a notebook (or script) as py:light."""
    nb = jupytext.read(path)
    if strip_metadata:
        nb.metadata.setdefault("jupytext", {})["notebook_metadata_filter"] = "-all"
    return jupytext.writes(nb, fmt="py:light")


def _strip_trailing_slash(pattern_or_patterns):
    if pattern_or_patterns is None:
        return []
    elif type(pattern_or_patterns) in (list, tuple):
        return [_strip_trailing_slash(pattern) for pattern in pattern_or_patterns]
    else:
        pattern = str(pattern_or_patterns)
        if pattern.endswith("/"):
            pattern = pattern[:-1]
        return pattern


def _path_expected(path: Path, expected):
    """Check if the given path or one of its parent dirs is in `expected`.

    Also ignore config files and .ipynb_checkpoints.
    """
    if _strip_trailing_slash(path) in expected:
        return True
    for parent in path.parents:
        if str(parent) in expected:
            return True

    # Ignore these as well to save typing
    if path.name in IMPLECTUS_CONFIG_FILES or ".ipynb_checkpoints" in path.parts:
        return True
    return False


def no_extra_files(path=".", expected: Iterable = None):
    """Check if the given path contains only files and dirs from `expected`.

    Also ignore config files and .ipynb_checkpoints.
    """
    expected = _strip_trailing_slash(expected)
    unexpected_dirs = []  # type: List[str]
    for file in Path(path).glob("**/*"):
        if _path_expected(file, expected):
            # Drop parent dir from unexpected_dirs list
            for parent in file.parents:
                if str(parent) in unexpected_dirs:
                    unexpected_dirs.remove(str(parent))
            continue
        if file.is_dir():
            unexpected_dirs.append(str(file))
            continue
        print("Unexpected file", file)
        return False
    return len(unexpected_dirs) == 0


def _resolve_code(code_or_file, _load=lambda f: Path(f).read_text()):
    """If `code_or_file` is a filename then load it, otherwise return it as-is."""
    if "\n" in code_or_file or len(code_or_file) > 256:
        return code_or_file
    if Path(code_or_file).is_file():
        return _load(code_or_file)
    return code_or_file


def _split_header(code):
    """Extract the Implectus header from a generated code string."""
    lines = code.splitlines()
    assert len(lines) > 3
    assert lines[0].startswith("# # Autogenerated"), "Missing header"
    assert lines[1].startswith("# This file was"), "Missing header"
    assert lines[2].startswith("# edit `"), "Missing header"
    assert not lines[3], "Missing gap"
    return "\n".join(lines[:3]), "\n".join(lines[4:])


def _remove_header_version(header):
    """Remove the version number from an Implectus header."""
    return re.sub(r"Implectus [\d\.]+?\. ", "Implectus. ", header)


def code_equal(actual, expected, assert_=True, _resolve=_resolve_code):
    """Check whether generated code files or strings are equivalent.

    Only works when both are py:light for now.
    """
    actual = _resolve(actual)
    expected = _resolve(expected)
    actual_header, actual_code = _split_header(actual)
    expected_header, expected_code = _split_header(expected)
    actual_header = _remove_header_version(actual_header)
    expected_header = _remove_header_version(expected_header)
    if assert_ is True:
        assert actual_header == expected_header
        assert actual_code == expected_code
    if assert_ is False:
        assert actual_header != expected_header or actual_code != expected_code
    return actual_header == expected_header and actual_code == expected_code


def _resolve_doc(doc_or_file):
    """If `code_or_file` is a filename then load it as py:light, otherwise return it."""
    return _resolve_code(doc_or_file, nb_to_py)


def doc_equal(*args, **kwargs):
    """Check whether generated code files or strings are equivalent.

    Arguments must be files or py:light strings.
    """
    return code_equal(*args, **kwargs, _resolve=_resolve_doc)  # type: ignore


def create_nb(cells=None, metadata=None, nbformat=4, nbformat_minor=4):
    return NotebookNode(
        metadata=metadata or {},
        nbformat=nbformat,
        nbformat_minor=nbformat_minor,
        cells=cells or [],
    )