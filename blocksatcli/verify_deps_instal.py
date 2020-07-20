import unittest, argparse
from . import dependencies


class TestDependencies(unittest.TestCase):
    def gen_args(self, target, btc=False):
        """Mock command-line argument"""
        parser     = argparse.ArgumentParser()
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
        expected_apps = ["dvbnet", "dvb-fe-tool", "dvbv5-zap", "ip", "iptables"]
        self.assertTrue(dependencies.check_apps(expected_apps))

    def test_sdr_deps(self):
        """Test the installation of SDR receiver dependencies"""
        args = self.gen_args("sdr")
        dependencies.run(args)
        expected_apps = ["rtl_sdr", "leandvb", "ldpc_tool", "tsp"]
        self.assertTrue(dependencies.check_apps(expected_apps))

    def test_standalone_deps(self):
        """Test the installation of standalone receiver dependencies"""
        args = self.gen_args("standalone")
        dependencies.run(args)
        expected_apps = ["ip", "iptables"]
        self.assertTrue(dependencies.check_apps(expected_apps))

    def test_bitcoin_satellite(self):
        """Test the installation of bitcoin-satellite"""
        args = self.gen_args("standalone", btc=True)
        dependencies.run(args)
        expected_apps = ["bitcoind", "bitcoin-cli", "bitcoin-tx", "bitcoin-qt"]
        self.assertTrue(dependencies.check_apps(expected_apps))

