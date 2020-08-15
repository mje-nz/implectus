"""Unit tests for config module, apart from ImplectusConfiguration."""

import os
from pathlib import Path

import pyfakefs  # noqa: F401
import pytest

from implectus.config import load_config_for_path

from .util import write_config

HOME = os.environ["HOME"]


@pytest.mark.parametrize(
    "config_file_path",
    (
        # Not at all exhaustive
        f"{HOME}/.implectus.toml",
        f"{HOME}/.implectus.yml",
        f"{HOME}/.implectus.yaml",
        f"{HOME}/.implectus.json",
        # pyfakefs breaks PyFormatLoader
        # f"{HOME}/.implectus.py",
        "/usr/share/implectus.yaml",
        # These should work too
        f"{HOME}/.jupytext",
        f"{HOME}/.jupytext.toml",
        f"{HOME}/.jupytext.yml",
        f"{HOME}/.jupytext.yaml",
        f"{HOME}/.jupytext.json",
        "/usr/share/jupytext.yaml",
    ),
)
@pytest.mark.filterwarnings(
    "ignore:Setting Implectus paths:implectus.config.ImplectusConfigWarning"
)
def test_finding_global_config(fs, config_file_path):
    """Use pyfakefs to test finding global config files."""
    # TODO: Why is this so slow with pyfakefs??
    write_config(
        config_file_path, dict(source_dir="custom", default_jupytext_formats="custom")
    )
    config = load_config_for_path("notebook.py")
    # Loading Implectus config works
    assert config.source_dir == "custom"
    # Loading Jupytext config works
    assert config.default_jupytext_formats == "custom"
    # Working dir not set automatically
    assert not config.working_dir


def _test_finding_local_config(root, config_name, notebook_name):
    config_path = Path(root) / config_name
    write_config(
        config_path, dict(source_dir="custom", default_jupytext_formats="custom")
    )
    notebook_path = Path(root) / notebook_name
    config = load_config_for_path(notebook_path)
    # Loading Implectus config works
    assert config.source_dir == "custom"
    # Loading Jupytext config works
    assert config.default_jupytext_formats == "custom"
    # Working dir set automatically
    assert config.working_dir == root


@pytest.mark.parametrize(
    "config_name",
    (
        # Exhaustive
        "implectus.toml",
        "implectus.yml",
        "implectus.yaml",
        "implectus.json",
        ".implectus.toml",
        ".implectus.yml",
        ".implectus.yaml",
        ".implectus.json",
        ".implectus.py",
        "jupytext",
        "jupytext.toml",
        "jupytext.yml",
        "jupytext.yaml",
        "jupytext.json",
        ".jupytext",
        ".jupytext.toml",
        ".jupytext.yml",
        ".jupytext.yaml",
        ".jupytext.json",
        ".jupytext.py",
    ),
)
def test_finding_local_config(
    tmpdir, config_name,
):
    _test_finding_local_config(tmpdir, config_name, "test.ipynb")


@pytest.mark.parametrize(
    "notebook_path",
    (
        "",
        ".",
        "notebooks" "notebooks/" "notebooks/test.ipynb",
        "notebooks/submodule",
        "notebooks/submodule/",
        "notebooks/submodule/test.py",
    ),
)
def test_finding_local_config_for_path(tmpdir, notebook_path):
    # Treat paths without extensions as dirs
    p = Path(tmpdir) / notebook_path
    if not p.suffix:
        p.mkdir(parents=True, exist_ok=True)

    _test_finding_local_config(tmpdir, "implectus.yaml", notebook_path)


# TODO: Jupytext integration tests to make sure it still picks up the config
