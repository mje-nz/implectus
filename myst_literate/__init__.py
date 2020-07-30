import textwrap

from .__about__ import __version__
from .contentsmanager import FileContentsManager, replace_contents_manager

__all__ = ["__version__", "FileContentsManager", "load_jupyter_server_extension"]


def load_jupyter_server_extension(app):
    """Use literate's content manager.

    Called by the Jupyter server during startup if the literate server extension is
    enabled.
    """
    if hasattr(app.contents_manager_class, "TODO"):
        app.log.info("[Literate] Literate contents manager already loaded")
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
            [Literate] An error occurred. Please deactivate the server extension with
                jupyter serverextension disable myst_literate
            and configure the contents manager manually by adding
                c.NotebookApp.contents_manager_class = "myst_literate.TextFileContentsManager"
            to your .jupyter/jupyter_notebook_config.py file.
            """
            )
        )
        raise
