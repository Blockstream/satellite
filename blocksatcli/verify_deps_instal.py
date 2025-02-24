import argparse
import logging
import os
import unittest

import distro
from packaging.version import Version

from . import dependencies, util

runner = util.ProcessRunner()


class TestDependencies(unittest.TestCase):

    def setUp(self):
        # List of commands to execute after the test case
        self.undo_cmd = []

    def tearDown(self):
        if self.undo_cmd:
            for cmd in self.undo_cmd:
                runner.run(cmd)

    def gen_args(self, target=None, btc=False, gui=False):
        """Mock command-line argument"""
        logging.basicConfig(level=logging.DEBUG)
        default_cfg_dir = os.path.join(util.get_home_dir(), ".blocksat")
        parser = argparse.ArgumentParser()
        parser.add_argument('--cfg-dir',
                            default=default_cfg_dir,
                            help="Directory to use for configuration files")
        subparsers = parser.add_subparsers()
        dependencies.subparser(subparsers)
        args = ["deps", "-y"]

        if target:
            args.extend(["install", "--target", target])
            if (btc):
                args.append("--btc")
        elif gui:
            args.append("gui")

        return parser.parse_args(args)

    def test_usb_deps(self):
        """Test the installation of USB receiver dependencies"""
        args = self.gen_args("usb")
        dependencies.run(args)
        expected_apps = [
            "dvbnet", "dvb-fe-tool", "dvbv5-zap", "ip", "iptables"
        ]
        self.assertTrue(dependencies.check_apps(expected_apps))

    def test_sdr_deps(self):
        """Test the installation of SDR receiver dependencies"""
        args = self.gen_args("sdr")
        dependencies.run(args)
        expected_apps = ["rtl_sdr", "leandvb", "ldpc_tool", "tsp"]
        self.assertTrue(dependencies.check_apps(expected_apps))

        # gr-dvbs2rx on fc >= 36 and Ubuntu >= 22.04.
        distro_id = distro.id()
        distro_ver = distro.version()
        fc36_or_higher = distro_id == 'fedora' and int(distro_ver) >= 36
        ubuntu22_or_higher = distro_id == 'ubuntu' and Version(
            distro_ver) >= Version('22.04')
        debian_bookworm_or_higher = distro_id == 'debian' and Version(
            distro_ver) >= Version('12')
        if fc36_or_higher or ubuntu22_or_higher or debian_bookworm_or_higher:
            self.assertTrue(dependencies.check_apps(["dvbs2-rx"]))
        else:
            self.assertFalse(dependencies.check_apps(["dvbs2-rx"]))

    def test_standalone_deps(self):
        """Test the installation of standalone receiver dependencies"""
        args = self.gen_args("standalone")
        dependencies.run(args)
        expected_apps = ["ip", "iptables"]
        self.assertTrue(dependencies.check_apps(expected_apps))

    def test_sat_ip_deps(self):
        """Test the installation of sat-ip receiver dependencies"""
        args = self.gen_args("sat-ip")
        dependencies.run(args)
        expected_apps = ["tsp"]
        self.assertTrue(dependencies.check_apps(expected_apps))

    def test_bitcoin_satellite(self):
        """Test the installation of bitcoin-satellite"""
        args = self.gen_args("standalone", btc=True)
        dependencies.run(args)
        expected_apps = ["bitcoind", "bitcoin-cli", "bitcoin-tx", "bitcoin-qt"]
        self.assertTrue(dependencies.check_apps(expected_apps))
