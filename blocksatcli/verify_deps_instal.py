import argparse
import logging
import unittest
import os
from distutils.version import LooseVersion

import distro

from . import dependencies, util


class TestDependencies(unittest.TestCase):

    def gen_args(self, target, btc=False):
        """Mock command-line argument"""
        logging.basicConfig(level=logging.DEBUG)
        default_cfg_dir = os.path.join(util.get_home_dir(), ".blocksat")
        parser = argparse.ArgumentParser()
        parser.add_argument('--cfg-dir',
                            default=default_cfg_dir,
                            help="Directory to use for configuration files")
        subparsers = parser.add_subparsers()
        dependencies.subparser(subparsers)
        args = ["deps", "-y", "install", "--target", target]
        if (btc):
            args.append("--btc")
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
        ubuntu22_or_higher = distro_id == 'ubuntu' and LooseVersion(
            distro_ver) >= '22.04'
        if fc36_or_higher or ubuntu22_or_higher:
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
