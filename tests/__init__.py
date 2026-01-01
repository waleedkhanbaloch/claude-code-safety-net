"""
Test package initializer.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock


class TempDirTestCase(unittest.TestCase):
    """Base test class that provides a temporary directory for each test.

    Also patches Path.home() to return the temp directory, ensuring tests
    don't accidentally read real user config files from ~/.cc-safety-net/.
    """

    tmpdir: Path
    _tmpdir_obj: tempfile.TemporaryDirectory[str]
    _home_patch: Any  # mock._patch type is complex, use Any for simplicity

    def setUp(self) -> None:
        super().setUp()
        self._tmpdir_obj = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self._tmpdir_obj.name)
        # Patch Path.home() to prevent tests from reading real user config
        self._home_patch = mock.patch.object(Path, "home", return_value=self.tmpdir)
        self._home_patch.start()

    def tearDown(self) -> None:
        self._home_patch.stop()
        self._tmpdir_obj.cleanup()
        super().tearDown()
