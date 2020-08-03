import textwrap

import jupytext
import nbformat
from jupytext.contentsmanager import build_jupytext_contents_manager_class
from notebook.notebookapp import NotebookApp
from notebook.services.contents.filemanager import FileContentsManager

from .config import ImplectusConfiguration  # , load_implectus_config
from .main import write_code, write_doc

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
        # TODO: do nothing with default config
        relative_path = path.strip("/")
        if (
            "type" in model
            and model["type"] == "notebook"
            and self.should_process(relative_path)
        ):
            nb = nbformat.from_dict(model["content"])
            nb_path = self._get_os_path(relative_path)
            self.log.info("[Implectus] Saving code for %s" % relative_path)
            write_code(nb, nb_path, self)
            self.log.info("[Implectus] Saving docs for %s" % relative_path)
            write_doc(nb, nb_path, self)
        # TODO: why doesn't super work after re-deriving?
        return super(type(self), self).save(model, path)

    def get_config(self, path, use_cache=False):
        """Return the Implectus configuration for the given API path."""
        # TODO: load config from file
        # abs_path = Path(self._get_os_path(path.strip("/")))
        # parent_dir = abs_path.parent
        # return load_implectus_config(parent_dir) or self
        return self


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
            "from {}".format(app.contents_manager_class.__name__)
        )
        app.contents_manager_class = build_jupytext_contents_manager_class(
            app.contents_manager_class
        )

    app.log.debug(
        "[Implectus] Building Implectus contents manager "
        "from {}".format(app.contents_manager_class.__name__)
    )
    contents_manager_class = build_implectus_contents_manager_class(
        app.contents_manager_class
    )
    contents_manager = contents_manager_class(parent=app, log=app.log)
    # TODO load config from file
    contents_manager.validate_config()

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
