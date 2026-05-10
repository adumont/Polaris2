import pathlib
import sys

import polaris2.webui._launcher as launcher


class TestLauncher:
    def test_module_imports(self):
        assert launcher is not None

    def test_main_sets_argv_and_calls_streamlit(self, monkeypatch):
        calls = []
        monkeypatch.setattr("streamlit.web.cli.main", lambda: calls.append("called"))
        monkeypatch.setattr(sys, "exit", lambda x: None)
        orig_argv = sys.argv.copy()
        try:
            launcher.main()
            assert "streamlit" in sys.argv[0]
            assert len(calls) == 1
        finally:
            sys.argv = orig_argv
