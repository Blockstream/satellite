import argparse
import sys
import unittest
from unittest.mock import patch

from blocksatcli import dependencies, util
from blocksatgui.daemon import daemon

runner = util.ProcessRunner()


class TestDependencies(unittest.TestCase):

    def setUp(self):
        # List of commands to execute after the test case
        self.undo_cmd = []

    def tearDown(self):
        if self.undo_cmd:
            for cmd in self.undo_cmd:
                runner.run(cmd)

    @patch("blocksatgui.daemon.dependencies._detect_venv")
    def test_gui_deps_pip(self, mock_detect_venv):
        mock_detect_venv.return_value = True

        args = argparse.Namespace(yes=True, dry_run=False)
        daemon.deps(args)

        self.assertTrue(dependencies.check_python_packages(["dbus-python"]))

        # Clean up installation
        self.undo_cmd.append(
            [sys.executable, "-m", "pip", "uninstall", "-y", "dbus-python"])

    @patch("blocksatgui.daemon.dependencies._detect_venv")
    def test_gui_deps_binary(self, mock_detect_venv):
        mock_detect_venv.return_value = False

        args = argparse.Namespace(yes=True, dry_run=False)
        daemon.deps(args)

        self.assertTrue(dependencies.is_package_installed("python3-dbus"))

        # Clean up installation
        manager = dependencies.get_pkg_manager()
        self.undo_cmd.append([manager, "remove", "python3-dbus", "-y"])
