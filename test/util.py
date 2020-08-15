import json
from pathlib import Path
from typing import Iterable, List

import jupytext
import pytest
import toml
import yaml

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


def nb_to_py(path):
    """Return the contents of a notebook (or script) as py:light."""
    return jupytext.writes(jupytext.read(path), fmt="py:light")


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
