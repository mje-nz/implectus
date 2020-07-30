import jupytext
import nbformat
from jupytext.contentsmanager import build_jupytext_contents_manager_class
from notebook.notebookapp import NotebookApp
from notebook.services.contents.filemanager import FileContentsManager

from .config import LiterateConfiguration  # , load_literate_config
from .main import write_code, write_doc


def build_literate_contents_manager_class(base_class: FileContentsManager):
    """Derives a contents manager from the given base class."""

    class LiterateContentsManager(base_class, LiterateConfiguration):  # type: ignore
        """Jupyter contents manager which supports Jupytext and Myst-Literate files."""

        def save(self, model: dict, path=""):
            """Save the file model and return the model with no content."""
            # TODO: do nothing with default config
            if "type" in model and model["type"] == "notebook":
                # TODO: only for notebooks in source path
                nb = nbformat.from_dict(model["content"])
                nb_path = self._get_os_path(path)
                self.log.info("[Literate] Saving code for %s" % path)
                # TODO: move path calculation out of write_code/doc?
                write_code(nb, nb_path, self)
                self.log.info("[Literate] Saving docs for %s" % path)
                write_doc(nb, nb_path, self)
            return super().save(model, path)

        def get_config(self, path, use_cache=False):
            """Return the Literate configuration for the given API path."""
            # TODO: load config from file
            # abs_path = Path(self._get_os_path(path.strip("/")))
            # parent_dir = abs_path.parent
            # return load_literate_config(parent_dir) or self
            return self

    return LiterateContentsManager


FileContentsManager = build_literate_contents_manager_class(
    jupytext.TextFileContentsManager
)


def replace_contents_manager(app: NotebookApp):
    if not hasattr(app.contents_manager_class, "default_jupytext_formats"):
        app.log.debug(
            "[Literate] Building Jupytext contents manager "
            "from {}".format(app.contents_manager_class.__name__)
        )
        app.contents_manager_class = build_jupytext_contents_manager_class(
            app.contents_manager_class
        )

    app.log.debug(
        "[Literate] Building Literate contents manager "
        "from {}".format(app.contents_manager_class.__name__)
    )
    contents_manager_class = build_literate_contents_manager_class(
        app.contents_manager_class
    )
    contents_manager = contents_manager_class(parent=app, log=app.log)
    # TODO load config from file
    contents_manager.validate_config()

    app.contents_manager_class = contents_manager_class
    app.contents_manager = contents_manager
    app.session_manager.contents_manager = contents_manager
    app.web_app.settings["contents_manager"] = contents_manager
    app.log.info("[Literate] Contents manager set up successfully")
