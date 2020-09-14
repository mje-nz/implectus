import os
import unittest.mock as mock
import warnings
from pathlib import Path
from typing import Iterator, Optional, Union

import jupytext.config
from traitlets import Bool, Unicode

try:
    # Introduced after 1.6.0
    from jupytext.config import JupytextConfigurationError
except ImportError:
    JupytextConfigurationError = ValueError

__all__ = [
    "ImplectusConfigWarning",
    "ImplectusConfiguration",
    "construct_config",
    "find_global_config",
    "load_config_file",
    "load_config_for_path",
    "validate_config",
]


class ImplectusConfigWarning(RuntimeWarning):
    pass


class ImplectusConfigError(JupytextConfigurationError):
    pass


class ImplectusConfiguration(jupytext.config.JupytextConfiguration):

    """Implectus configuration.

    There are two ways this is used.

    In the Jupyter server, paths are always relative to the server's working directory
    (so working_dir="") and the config is loaded from disk when needed.

    In the CLI (TBD), a config file is found for each path in turn, the folder
    containing it is the working_dir while processing that path, and all paths are
    absolute.

    Note that although the contents manager itself is a configuration, only
    self.notebook_extensions is used from it.  (There's also an edge case where it is
    used as a fallback, which a lot of Jupytext's tests use.)
    """

    source_dir = Unicode(
        "",
        help="Directory containing source documents (relative to config file), which "
        "is used to determine output paths.",
        config=True,
    )

    code_dir = Unicode(
        "",
        help="Root directory of package into which to export code (relative to config "
        "file).  The name of this directory is used as the package name when rewriting "
        "imports.",
        config=True,
    )

    doc_dir = Unicode(
        "",
        help="Directory into which to export documentation (relative to config file).",
        config=True,
    )

    # TODO: should this even be an option?
    export_code_as_package = Bool(
        False,
        help="Whether to export code as a package or as individual modules, i.e., "
        "whether to generate __init__.py modules.",
        config=True,
    )

    code_format = Unicode(
        "py:nomarker", help="Jupytext format for exported code.", config=True
    )

    doc_format = Unicode(
        "ipynb", help="Jupytext format for exported documentation.", config=True
    )

    # Root directory of project (set in load_config_for_path).
    # N.B. FileContentsManager uses root_dir, which defaults to the notebook server's
    # notebook dir.
    working_dir = Unicode("")

    def validate_config(self):
        """Check whether the configuration is valid.

        (This is not called magically anywhere.)
        """
        if self.export_code_as_package and not self.code_dir:
            raise ValueError(
                "Can't export code as package without specifying a code directory "
                "(code_dir=%r)" % self.code_dir
            )

    @property
    def working_path(self):
        """Root directory of project (either absolute or relative to cwd)."""
        return Path(self.working_dir)

    @property
    def source_path(self):
        """Path to source directory (either absolute or relative to cwd)."""
        return self.working_path / self.source_dir

    @property
    def code_path(self):
        """Path to code directory (either absolute or relative to cwd)."""
        return self.working_path / self.code_dir

    @property
    def doc_path(self):
        """Path to doc directory (either absolute or relative to cwd)."""
        return self.working_path / self.doc_dir

    def _check_absoluteness(self, path):
        """Check that `path` and `root_path` are both absolute or both relative."""
        if self.working_path.is_absolute() and not Path(path).is_absolute():
            warnings.warn(
                "Candidate paths must be absolute when the root dir is absolute",
                ImplectusConfigWarning,
            )
            return False
        return True

    def should_process(self, path):
        """Check if a path should be treated as a source document."""
        if not self.source_dir:
            return False
        if not self._check_absoluteness(path):
            return False
        # source_path and path are either both relative or both absolute
        return self.source_path in Path(path).parents

    def _relative_path_to_source(self, source_file_path):
        """Get the path to the given source file relative to the source folder.

        Raises:
            ImplectusConfigWarning: if the source file path has different absoluteness
                to the root dir.
            ValueError: if the source file is not in the source folder.
        """
        if not self.source_dir:
            return None
        # TODO: when does this matter?
        if not self._check_absoluteness(source_file_path):
            return None
        src = Path(source_file_path)
        return src.relative_to(self.source_path)

    def code_path_for_source(self, source_file_path):
        """Get the path of the module into which to export the given source's code."""
        filename = self._relative_path_to_source(source_file_path)
        if filename and self.code_dir:
            return self.code_path / filename.with_suffix(".py")

    def module_name(self, source_file_path):
        """Calculate the module name for the given source notebook when exported."""
        self.validate_config()
        if not self.source_dir:
            return
        if self.export_code_as_package:
            package = Path(self.code_dir).parts[-1]
            relative_path = self._relative_path_to_source(source_file_path)
            if relative_path is not None:
                module_path = Path(package) / relative_path.with_suffix("")
                return ".".join(module_path.parts)
        else:
            # TODO: Is this even useful?
            return Path(source_file_path).with_suffix("").name

    def doc_path_for_source(self, source_file_path):
        """Get the path of the module into which to export the given source's docs."""
        if not self.source_dir or not self.doc_dir:
            return
        doc_filename = self._relative_path_to_source(source_file_path)
        return self.doc_path / doc_filename.with_suffix(".ipynb")


# Copy Jupytext's config search behaviour
IMPLECTUS_CONFIG_FILES = [
    # No implectus or .implectus because I can't easily patch in the check for them
    "implectus.toml",
    "implectus.yml",
    "implectus.yaml",
    "implectus.json",
]
IMPLECTUS_CONFIG_FILES.extend(["." + filename for filename in IMPLECTUS_CONFIG_FILES])
IMPLECTUS_CONFIG_FILES.extend([".implectus.py"] + jupytext.config.JUPYTEXT_CONFIG_FILES)
IMPLECTUS_CEILING_DIRECTORIES = [
    path
    for path in os.environ.get("IMPLECTUS_CEILING_DIRECTORIES", "").split(":")
    if path
]
IMPLECTUS_CEILING_DIRECTORIES.extend(jupytext.config.JUPYTEXT_CEILING_DIRECTORIES)


def _global_config_dirs() -> Iterator[str]:
    """Return the directories Implectus will search for a global config file."""
    for config_dir in jupytext.config.global_jupytext_configuration_directories():
        yield config_dir.replace("jupytext", "implectus")


def find_global_config() -> Optional[str]:
    """Search for global Implectus or Jupytext config files.

    Returns: the path to the first config file found.
    """
    for config_dir in _global_config_dirs():
        config_file = _find_config(config_dir, search_parent_dirs=False)
        if config_file:
            return config_file
    return None


def _find_config(path, search_parent_dirs=True) -> Optional[str]:
    """Search for Implectus or Jupytext config files, starting at the given path.

    First check `path`, then optionally search its parents until the root directory or
    any of the directories in the `IMPLECTUS_CEILING_DIRS` and `JUPYTEXT_CEILING_DIRS`
    environment variables are reached.  Finally, search the global config directories.

    Returns: the path to the first config file found.
    """
    with mock.patch.multiple(
        "jupytext.config",
        JUPYTEXT_CONFIG_FILES=IMPLECTUS_CONFIG_FILES,
        find_global_jupytext_configuration_file=find_global_config,
    ):
        return jupytext.config.find_jupytext_configuration_file(
            path, search_parent_dirs
        )


def load_config_file(config_file_path: str, *args, **kwargs):
    """Read an Implectus or Jupytext config file (TOML, YAML, Python, or JSON)."""
    # TODO: doc
    try:
        return jupytext.config.load_jupytext_configuration_file(
            config_file_path, *args, **kwargs
        )
    except JupytextConfigurationError as e:
        raise ImplectusConfigError(e)


def construct_config(
    config_file_path: str, config: Optional[dict]
) -> Optional[ImplectusConfiguration]:
    """Turn a dict-like config into an ImplectusConfiguration."""
    # TODO: doc
    with mock.patch.multiple(
        "jupytext.config", JupytextConfiguration=ImplectusConfiguration
    ):
        return jupytext.config.validate_jupytext_configuration_file(
            config_file_path, config
        )


def validate_config(
    notebook_path: Union[str, Path],
    config_file_path: Union[str, Path],
    config: Optional[ImplectusConfiguration],
):
    if config is None:
        return
    # TODO: doc
    notebook_path = Path(notebook_path)
    config_file_path = Path(config_file_path)
    config_dir = config_file_path.parent
    if config_dir == notebook_path or config_dir in notebook_path.parents:
        # If a local config file was used, use that dir as the working dir
        config.working_dir = str(config_dir)
    elif config.source_dir or config.code_dir or config.doc_dir:
        # Discourage setting paths in global config
        # TODO: test
        warnings.warn(
            "Setting Implectus paths in a global config file will make them relative "
            "to the working directory, which means the CLI will only work from the "
            "project root.",
            ImplectusConfigWarning,
        )
    return config


def load_config_for_path(notebook_path):
    """Load the Implectus or Jupytext config file that applies to the given notebook."""
    # TODO: doc
    config_file = _find_config(notebook_path)
    if not config_file:
        return None

    # TODO: put this in find_config?
    # TODO: this needs its own test
    notebook_path = Path(notebook_path)
    if notebook_path.is_file() and notebook_path.samefile(config_file):
        # Inherited from Jupytext; I guess this filters out implectus.py
        return None

    config_dict = load_config_file(config_file)
    config = construct_config(config_file, config_dict)
    config = validate_config(notebook_path, config_file, config)
    return config
