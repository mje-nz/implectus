# MyST-Literate
> Write Python libraries as literate programs using Jupyter notebooks.

The [Jupyter notebook](https://github.com/jupyter/notebook) is a great tool for literate Python programming, allowing code to be interspersed with rich outputs and Markdown.
It's not perfect though; notebooks discourage traditional software engineering practises like version control, testing, and code reuse, and the Jupyter interface is still basically just an interactive shell with a much weaker feature set than traditional IDEs.
[Jupytext](https://github.com/mwouts/jupytext) is an improvement: it makes notebooks version control- and IDE-friendly, and makes it much easier to develop some code in one notebook and then use it from another.
[Fast.ai's nbdev](https://github.com/fastai/nbdev) goes a step further and builds libraries from collections of notebooks, with a build process that extracts the implementations into a package and the documentation into compiled HTML.
This project takes the idea from nbdev and builds it on top of Jupytext, [Sphinx](https://www.sphinx-doc.org), and the tools from the [Executable Book Project](https://executablebooks.org/en/latest/).


## Features
Implemented:
* Export all cells in a notebook with "export" and "export-internal" cell tags into a Python module.
* Preprocess a notebook for use in a MyST-NB Sphinx documentation project by:
  * Adding `autodoc` directives for exported functions and classes that aren't otherwise documented.
  * Hiding the input areas of cells with "export" and "export-internal" cell tags
* Convert absolute imports in notebook to relative imports in exported module.

To do:
* Generate `__init__.py`
* Fill in `__all__`
* Copy images when exporting docs
* Command-line tool
* Jupytext integration:
  * Sync notebook to module/doc
  * Sync module back to notebook
* Support generating single files rather requiring modules to be in a package
* Export cells with "test" cell tags into test scripts
* Add examples
* Add documentation
* Set up RTD
* Support exporting to multiple files
* Support exporting to a file with a different name


## Related projects
There are many other projects with different approaches to literate Python programming such as [Pweave](https://github.com/mpastell/Pweave), [notedown](https://github.com/aaren/notedown), and [knitpy](https://github.com/jankatins/knitpy), which are also great.
