import textwrap
import unittest.mock as mock
from functools import partial

import jupytext
import nbformat
from jupytext.contentsmanager import build_jupytext_contents_manager_class
from notebook.notebookapp import NotebookApp
from notebook.services.contents.filemanager import FileContentsManager
from tornado.web import HTTPError

from .config import (
    IMPLECTUS_CONFIG_FILES,
    ImplectusConfiguration,
    construct_config,
    find_global_config,
    load_config_file,
    validate_config,
)
from .main import write_code, write_doc
from .util import DestinationNotOverwriteableError

__all__ = [
    "ImplectusContentsManager",
    "load_jupyter_server_extension",
]


class ImplectusContentsManager(
    jupytext.TextFileContentsManager,
    FileContentsManager,  # Help type deduction, since Jupytext hides its base
    ImplectusConfiguration,
):

    """A Jupyter contents manager which supports all the Jupytext formats, and also
    exports code and documentation when notebooks are saved.

    See https://jupyter-notebook.readthedocs.io/en/stable/extending/contents.html for
    Jupyter Contents API documentation.
    """

    def save(self, model: dict, path=""):
        """Save the file model and return the model with no content.

        Args:
            model: Jupyter virtual filesystem entity.
            path: API-style path, which seems to mean relative to the server's working
                directory but starting with a /.
        """
        relative_path = path.strip("/")
        if "type" in model and model["type"] == "notebook":
            config = self.get_config(relative_path)
            self.validate_config()
            if config.should_process(relative_path):
                nb = nbformat.from_dict(model["content"])
                # TODO: check these don't overwrite each other
                try:
                    if config.code_dir:
                        self.log.info("[Implectus] Saving code for %s" % relative_path)
                        write_code(nb, relative_path, config)
                    if config.doc_dir:
                        self.log.info("[Implectus] Saving docs for %s" % relative_path)
                        write_doc(nb, relative_path, config)
                except DestinationNotOverwriteableError as e:
                    raise HTTPError(
                        400, f"Implectus could not export to {e.filename} (it exists)"
                    )

        # TODO: why doesn't super work after re-deriving?
        return super(type(self), self).save(model, path)

    def get_config_file(self, directory):
        """Return the jupytext configuration file for the given dir, if any."""
        # TODO: doc
        with mock.patch.multiple(
            "jupytext.contentsmanager",
            JUPYTEXT_CONFIG_FILES=IMPLECTUS_CONFIG_FILES,
            find_global_jupytext_configuration_file=find_global_config,
        ):
            return super(type(self), self).get_config_file(directory)

    def _load_config_file(self, parent_dir, config_file):
        """Load the configuration file"""
        # TODO: doc
        with mock.patch.multiple(
            "jupytext.contentsmanager",
            load_jupytext_configuration_file=load_config_file,
            validate_jupytext_configuration_file=construct_config,
        ):
            config = super(type(self), self).load_config_file(config_file)
        if config:
            return validate_config(parent_dir, config_file, config)

    def load_config_file(self, config_file):
        """Placeholder that get_config replaces."""
        raise NotImplementedError()

    def get_config(self, path, *args, **kwargs):
        """Return the Implectus configuration for the given API path."""
        # Pass path into _load_config_file for validation
        try:
            old_load_config_file = self.load_config_file
            patched_load_config_file = partial(self._load_config_file, path)
            # https://github.com/python/mypy/issues/2427
            self.load_config_file = patched_load_config_file  # type: ignore
            config = super(type(self), self).get_config(path, *args, **kwargs)
        finally:
            self.load_config_file = old_load_config_file  # type: ignore
        if config and config.working_path.is_absolute():
            # TODO: is this still true?
            # get_config uses an absolute path, so the path that ends up in working_dir
            # is also an absolute path, but all the other paths in here are relative
            # to self.root_dir
            config.working_dir = str(config.working_path.relative_to(self.root_dir))
        return config


def build_implectus_contents_manager_class(base_class: type):
    """Derives a contents manager from the given base class.

    Jupytext does it this way so that it doesn't break applications with a different
    default contents manager.
    """
    return type(
        "ImplectusContentsManager",
        (base_class, ImplectusConfiguration),
        dict(ImplectusContentsManager.__dict__),
    )


def replace_contents_manager(app: NotebookApp):
    """Replace the app's contents manager with ours."""
    if not hasattr(app.contents_manager_class, "default_jupytext_formats"):
        app.log.debug(
            "[Implectus] Building Jupytext contents manager "
            f"from {app.contents_manager_class.__name__}"
        )
        app.contents_manager_class = build_jupytext_contents_manager_class(
            app.contents_manager_class
        )

    app.log.debug(
        "[Implectus] Building Implectus contents manager "
        f"from {app.contents_manager_class.__name__}"
    )
    contents_manager_class = build_implectus_contents_manager_class(
        app.contents_manager_class
    )
    contents_manager = contents_manager_class(parent=app, log=app.log)

    app.contents_manager_class = contents_manager_class
    app.contents_manager = contents_manager
    app.session_manager.contents_manager = contents_manager
    app.web_app.settings["contents_manager"] = contents_manager
    app.log.info("[Implectus] Contents manager set up successfully")


def load_jupyter_server_extension(app):
    """Use Implectus' content manager in the Jupyter notebook server.

    Called by the server during startup if the Implectus server extension is enabled.
    """
    if hasattr(app.contents_manager_class, "TODO"):
        app.log.info("[Implectus] Implectus contents manager already loaded")
        return

    # The contents manager has already been initialised in
    # notebook.NotebookApp.init_configurables, so we have to replace it (see
    # notebook.NotebookApp.initialize).
    try:
        replace_contents_manager(app)
    except Exception:
        app.log.error(
            textwrap.dedent(
                """\
            [Implectus] An error occurred. Please deactivate the server extension with
                jupyter serverextension disable implectus
            and configure the contents manager manually by adding
                c.NotebookApp.contents_manager_class = "implectus.ImplectusContentsManager"
            to your .jupyter/jupyter_notebook_config.py file.
            """
            )
        )
        raise
