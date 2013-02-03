


def test_compile():
    try:
        import tiddlywebplugins.simplewiki
        assert True
    except ImportError, exc:
        assert False, exc
