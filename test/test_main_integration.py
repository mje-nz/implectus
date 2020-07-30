"""Integration tests for export module."""

import sys
import textwrap
from pathlib import Path

import pytest

from myst_literate.main import Module


class LiterateProjectDir:

    """Fixture helper."""

    def __init__(self, root, notebook_dir, package_dir, doc_dir):
        self.root = Path(root)
        self.notebook_root = self.root / notebook_dir
        self.package_root = self.root / package_dir
        self.doc_root = self.root / doc_dir

    def get_module(self, notebook_name):
        return Module(
            self.notebook_root / notebook_name,
            self.notebook_root,
            self.package_root,
            self.doc_root,
        )


@pytest.fixture
def project(request, tmpdir):
    """Temporary project directory fixture.

    Marks:
        notebook_dir: Folder containing notebooks, relative to project root.
        package_dir: Root folder of package to export into, relative to project root.
        doc_dir: Folder to export doc notebooks into, relative to project root.
    """
    notebook_dir = request.node.get_closest_marker("notebook_dir", "notebooks")
    package_dir = request.node.get_closest_marker("package_dir", "package")
    doc_dir = request.node.get_closest_marker("doc_dir", "doc")
    return LiterateProjectDir(tmpdir, notebook_dir, package_dir, doc_dir)


def test_export_library(project: LiterateProjectDir):
    project.notebook_root.mkdir()
    project.notebook_root.joinpath("main.py").write_text(
        textwrap.dedent(
            """\
            # # Title

            # + tags=["export"]
            def hello():
                print("Hello world")
                return True
            # -

            hello()
            """
        )
    )
    module = project.get_module("main.py")
    module.export_to_package()

    expected = textwrap.dedent(
        """\
        def hello():
            print("Hello world")
            return True
        """
    )
    assert project.package_root.joinpath("main.py").read_text() == expected

    sys.path.append(str(project.root))
    import package.main  # noqa: I900

    assert package.main.hello()
