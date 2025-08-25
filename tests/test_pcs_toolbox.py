from pcs_toolbox import __version__, add


def test_add():
    assert add(1, 2) == 3


def test_version():
    assert __version__ == "0.2.1"
