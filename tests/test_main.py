#!/usr/bin/env python3
"""test the __main__ entry point module"""

import importlib
import importlib.machinery
import importlib.util
from unittest.mock import MagicMock, patch


class TestMain:
    """
    Test cases for the `__main__` entry point module, ensuring that the CLI is
    invoked correctly.
    """

    @patch("ica.cli.main", return_value=None)
    def test_main(self, cli_main: MagicMock) -> None:
        """Should import main."""
        # Load the module spec and create the module
        loader = importlib.machinery.SourceFileLoader("__main__", "./ica/__main__.py")
        spec = importlib.util.spec_from_loader(loader.name, loader)
        if not spec:
            raise ImportError("Failed to load module spec")
        main_module = importlib.util.module_from_spec(spec)
        # Expose package information to dynamically-imported module
        main_module.__package__ = __package__
        loader.exec_module(main_module)
        cli_main.assert_called_once()
