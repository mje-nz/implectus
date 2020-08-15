import jupytext

from .config import ImplectusConfiguration
from .export_code import write_code
from .export_doc import write_doc

# TODO sanity checks:
#   imports are translatable
#   no conflicting tags


def sync(config: ImplectusConfiguration):
    """Export code and doc for each file in the source directory."""
    if not config.source_dir:
        return
    sources = [
        path for path in config.source_path.glob("**/*") if config.should_process(path)
    ]
    for source in sources:
        nb = jupytext.read(source)
        if config.code_dir:
            write_code(nb, source, config)
        if config.doc_dir:
            write_doc(nb, source, config)


# TODO: CLI
