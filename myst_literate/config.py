from pathlib import Path

from traitlets import Bool, Unicode
from traitlets.config import Configurable


class LiterateConfiguration(Configurable):

    # TODO: make paths absolute when loading from a file

    source_dir = Unicode(
        "notebooks",
        help="Directory containing literate source notebooks, which is used to determine "
        "output paths.  If this is specified in a config file then it is relative to "
        "the file, otherwise it is relative to the working directory.",
        config=True,
    )

    code_dir = Unicode(
        "",
        help="Root directory of package into which to export code.  If this is specified in "
        "a config file then it is relative to the file, otherwise it is relative to the "
        "working directory.",
        config=True,
    )

    doc_dir = Unicode(
        "doc",
        help="Directory into which to export documentation.  If this is specified in a config "
        "file then it is relative to the file, otherwise it is relative to the working "
        "directory.",
        config=True,
    )

    export_code_as_package = Bool(
        False,
        help="Whether to export code as a package or as individual modules, i.e., whether "
        "to generate __init__.py modules.",
        config=True,
    )

    code_format = Unicode(
        "py:nomarker", help="Jupytext format for exported code.", config=True
    )

    doc_format = Unicode(
        "ipynb", help="Jupytext format for exported documentation.", config=True
    )

    root_dir = Unicode("", help="Root folder of project.")

    def validate_config(self):
        """Check whether the configuration is valid.

        This is not called magically.
        """
        if self.export_code_as_package and not self.code_dir:
            raise ValueError(
                "Can't export code as package without specifying a package path "
                "(code_dir=%r)" % self.code_dir
            )

    @property
    def root_path(self):
        # TODO: should this be always absolute?
        return Path(self.root_dir)

    @property
    def source_path(self):
        """Path to source directory (absolute if root path is set)."""
        return self.root_path / self.source_dir

    @property
    def code_path(self):
        """Path to code directory (absolute if root path is set)."""
        return self.root_path / self.code_dir

    @property
    def doc_path(self):
        """Path to doc directory (absolute if root path is set)."""
        return self.root_path / self.doc_dir

    def should_process(self, path):
        """Check if a path should be treated as a source document."""
        return self.source_path.resolve() in (self.root_path / path).resolve().parents

    def relative_path_to_source(self, source_file_path):
        """Get the given path relative to the source folder."""
        # TODO: is source_notebook allowed to be a relative path?
        src = Path(source_file_path)
        if self.source_path.is_absolute():
            assert src.is_absolute()
        return src.relative_to(self.source_path)

    def code_path_for_source(self, source_file_path):
        """Get the path of the module into which to export the given source's code."""
        filename = self.relative_path_to_source(source_file_path).with_suffix(".py")
        return self.code_path / filename

    def module_name(self, source_file_path):
        """Calculate the module name for the given source notebook when exported."""
        self.validate_config()
        if self.export_code_as_package:
            package = Path(self.code_dir).parts[-1]
            module_path = Path(package) / self.relative_path_to_source(source_file_path)
            return ".".join(module_path.with_suffix("").parts)
        else:
            return Path(source_file_path).with_suffix("").name

    def doc_path_for_source(self, source_file_path):
        """Get the path of the module into which to export the given source's code."""
        doc_filename = self.relative_path_to_source(source_file_path)
        return self.doc_path / doc_filename.with_suffix(".ipynb")


def load_literate_config(path):
    raise NotImplementedError()
