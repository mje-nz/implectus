"""Units tests for test utils."""

from pathlib import Path

from .util import no_extra_files


def test_no_extra_files(tmpdir_cd):
    assert no_extra_files()

    Path("test.txt").touch()
    assert not no_extra_files()
    assert no_extra_files(expected="test.txt")
    Path("test.txt").unlink()

    Path("src").mkdir()
    assert not no_extra_files()
    assert no_extra_files(expected=["src/"])
    assert no_extra_files(expected=["src"])
    assert not no_extra_files(expected=["src/test.txt"])

    Path("src/test.txt").touch()
    assert not no_extra_files()
    assert not no_extra_files(expected=["test.txt"])
    assert no_extra_files(expected=["src/test.txt"])
    assert no_extra_files(expected=["src/"])
    assert no_extra_files(expected=["src"])
