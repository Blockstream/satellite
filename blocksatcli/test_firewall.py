import argparse
from unittest import TestCase
from unittest.mock import call, patch

from . import defs, firewall


class TestIptables(TestCase):

    @patch('blocksatcli.firewall.runner.run')
    def test_config_udp_rule_with_udp_already_set(self, mock_runner):
        """Test iptables configuration with UDP rule already set
        """
        mock_runner.return_value.stdout = (
            "Chain INPUT (policy ACCEPT 0 packets, 0 bytes)\n"
            "num pkts bytes target prot opt in out source destination\n"
            "1 0 0 ACCEPT udp  -- eth0 any anywhere anywhere "
            "multiport dports 4433,4434").encode()

        firewall_cls = firewall.Iptables("eth0")
        firewall_cls.configure(ports=defs.src_ports,
                               src_ip="192.168.0.2",
                               igmp=False,
                               prompt=False)

        # Expect only one iptables call to check if the rule is set
        mock_runner.assert_called_once_with(
            ['iptables', '-L', '-v', '--line-numbers'],
            root=True,
            capture_output=True)

    @patch('blocksatcli.firewall.runner.run')
    def test_config_udp_and_igmp_rules_with_both_already_set(
            self, mock_runner):
        """Test iptables configuration with UDP and IGMP rules already set
        """
        mock_runner.return_value.stdout = (
            "Chain INPUT (policy ACCEPT 0 packets, 0 bytes)\n"
            "num pkts bytes target prot opt in out source destination\n"
            "1 0 0 ACCEPT igmp  -- eth0 any anywhere anywhere \n"
            "2 0 0 ACCEPT udp  -- eth0 any anywhere anywhere "
            "multiport dports 4433,4434").encode()

        firewall_cls = firewall.Iptables("eth0")
        firewall_cls.configure(ports=defs.src_ports,
                               src_ip="192.168.0.2",
                               igmp=True,
                               prompt=False)

        # Expect two calls to check if UDP and IGMP rules are set
        call_get_iptables_rules = call(
            ['iptables', '-L', '-v', '--line-numbers'],
            root=True,
            capture_output=True)

        mock_runner.assert_has_calls([
            # Check if udp rule is set (_is_udp_rule_set func)
            call_get_iptables_rules,
            # Check if igmp rule is set (_is_igmp_rule_set)
            call_get_iptables_rules
        ])

    @patch('blocksatcli.firewall.runner.run')
    def test_verify_iptables_rules_udp_and_igmp_already_set(self, mock_runner):
        """Test verify iptables configuration with rules already set
        """
        mock_runner.return_value.stdout = (
            "Chain INPUT (policy ACCEPT 0 packets, 0 bytes)\n"
            "num pkts bytes target prot opt in out source destination\n"
            "1 0 0 ACCEPT igmp  -- eth0 any anywhere anywhere \n"
            "2 0 0 ACCEPT udp  -- eth0 any anywhere anywhere "
            "multiport dports 4433,4434").encode()

        firewall_cls = firewall.Iptables("eth0")
        res = firewall_cls.verify(ports=defs.src_ports,
                                  src_ip="192.168.0.2",
                                  igmp=True)
        assert (res is True)

    @patch('blocksatcli.firewall.runner.run')
    def test_verify_iptables_rules_udp_and_igmp_not_set(self, mock_runner):
        """Test verify iptables configuration with rules missing
        """
        mock_runner.return_value.stdout = (
            "Chain INPUT (policy ACCEPT 0 packets, 0 bytes)\n"
            "num pkts bytes target prot opt in out source destination"
        ).encode()

        firewall_cls = firewall.Iptables("eth0")
        res = firewall_cls.verify(ports=defs.src_ports,
                                  src_ip="192.168.0.2",
                                  igmp=True)
        assert (res is False)

    @patch('blocksatcli.firewall.runner.run')
    def test_verify_iptables_rules_udp_not_set(self, mock_runner):
        """Test verify iptables configuration with UDP rule missing
        """
        mock_runner.return_value.stdout = (
            "Chain INPUT (policy ACCEPT 0 packets, 0 bytes)\n"
            "num pkts bytes target prot opt in out source destination\n"
            "1 0 0 ACCEPT igmp  -- eth0 any anywhere anywhere").encode()

        firewall_cls = firewall.Iptables("eth0")
        res = firewall_cls.verify(ports=defs.src_ports,
                                  src_ip="192.168.0.2",
                                  igmp=True)
        assert (res is False)

    @patch('blocksatcli.firewall.runner.run')
    def test_verify_iptables_rules_igmp_not_set(self, mock_runner):
        """Test verify iptables configuration with IGMP rule missing
        """
        mock_runner.return_value.stdout = (
            "Chain INPUT (policy ACCEPT 0 packets, 0 bytes)\n"
            "num pkts bytes target prot opt in out source destination\n"
            "1 0 0 ACCEPT udp  -- eth0 any anywhere anywhere "
            "multiport dports 4433,4434").encode()

        firewall_cls = firewall.Iptables("eth0")
        res = firewall_cls.verify(ports=defs.src_ports,
                                  src_ip="192.168.0.2",
                                  igmp=True)
        assert (res is False)


class Firewalld(TestCase):

    @patch('blocksatcli.firewall.runner.run')
    def test_config_udp_rule_with_udp_already_set(self, mock_runner):
        """Test firewalld configuration with UDP rule already set
        """
        mock_runner.return_value.returncode = 0

        firewall_cls = firewall.Firewalld("eth0")
        firewall_cls.configure(ports=defs.src_ports,
                               src_ip="192.168.0.2",
                               igmp=False,
                               prompt=False)

        portrange = "{}-{}".format(min(defs.src_ports), max(defs.src_ports))

        # Expect only one firewalld call to check if the rule is set
        mock_runner.assert_called_once_with([
            'firewall-cmd', '--quiet', '--query-rich-rule',
            ("rule "
             "family=ipv4 "
             "source address=192.168.0.2 "
             f"destination address={defs.mcast_ip}/32 "
             f"port port={portrange} protocol=udp accept")
        ],
                                            root=True,
                                            nocheck=True)

    @patch('blocksatcli.firewall.runner.run')
    def test_config_udp_and_igmp_rules_with_both_already_set(
            self, mock_runner):
        """Test firewalld configuration with UDP and IGMP rules already set
        """
        mock_runner.return_value.returncode = 0

        firewall_cls = firewall.Firewalld("eth0")
        firewall_cls.configure(ports=defs.src_ports,
                               src_ip="192.168.0.2",
                               igmp=True,
                               prompt=False)

        portrange = "{}-{}".format(min(defs.src_ports), max(defs.src_ports))

        # Expect two firewalld calls to check if the UDP and IGMP rules are set
        call_check_firewalld_udp_rule = call([
            'firewall-cmd', '--quiet', '--query-rich-rule',
            ("rule "
             "family=ipv4 "
             "source address=192.168.0.2 "
             f"destination address={defs.mcast_ip}/32 "
             f"port port={portrange} protocol=udp accept")
        ],
                                             root=True,
                                             nocheck=True)
        call_check_firewalld_igmp_rule = call(
            ['firewall-cmd', '--quiet', '--query-protocol=igmp'],
            root=True,
            nocheck=True)
        mock_runner.assert_has_calls([
            # Check if udp rule is set (_is_udp_rule_set func)
            call_check_firewalld_udp_rule,
            # Check if igmp rule is set (_is_igmp_rule_set)
            call_check_firewalld_igmp_rule
        ])

    @patch('blocksatcli.firewall.runner.run')
    def test_verify_firewalld_rules_udp_and_igmp_already_set(
            self, mock_runner):
        """Test verify firewalld configuration with rules already set
        """
        mock_runner.return_value.returncode = 0

        firewall_cls = firewall.Firewalld("eth0")
        res = firewall_cls.verify(ports=defs.src_ports,
                                  src_ip="192.168.0.2",
                                  igmp=True)
        assert (res is True)

    @patch('blocksatcli.firewall.runner.run')
    def test_verify_firewalld_rules_udp_and_igmp_not_set(self, mock_runner):
        """Test verify firewalld configuration with rules missing
        """
        mock_runner.return_value.returncode = 1

        firewall_cls = firewall.Firewalld("eth0")
        res = firewall_cls.verify(ports=defs.src_ports,
                                  src_ip="192.168.0.2",
                                  igmp=True)
        assert (res is False)

    @patch('blocksatcli.firewall.Firewalld._is_igmp_rule_set')
    @patch('blocksatcli.firewall.Firewalld._is_udp_rule_set')
    def test_verify_firewalld_rules_udp_not_set(self, mock_is_udp_set,
                                                mock_is_igmp_set):
        """Test verify firewalld configuration with UDP rule missing
        """
        mock_is_udp_set.return_value = False
        mock_is_igmp_set.return_value = True

        firewall_cls = firewall.Firewalld("eth0")
        res = firewall_cls.verify(ports=defs.src_ports,
                                  src_ip="192.168.0.2",
                                  igmp=True)
        assert (res is False)

    @patch('blocksatcli.firewall.Firewalld._is_igmp_rule_set')
    @patch('blocksatcli.firewall.Firewalld._is_udp_rule_set')
    def test_verify_firewalld_rules_igmp_not_set(self, mock_is_udp_set,
                                                 mock_is_igmp_set):
        """Test verify firewalld configuration with IGMP rule missing
        """
        mock_is_udp_set.return_value = True
        mock_is_igmp_set.return_value = False

        firewall_cls = firewall.Firewalld("eth0")
        res = firewall_cls.verify(ports=defs.src_ports,
                                  src_ip="192.168.0.2",
                                  igmp=True)
        assert (res is False)


class TestFirewall(TestCase):

    def setUp(self):
        # Add minimum args to firewall configuration
        self.args = argparse.Namespace(cfg='',
                                       cfg_dir='',
                                       interface='eth0',
                                       standalone=True,
                                       dry_run=False,
                                       yes=True)

    @patch('blocksatcli.firewall.is_firewalld')
    def test_get_firewalld_class(self, mock_firewalld):
        # Firewalld installed.
        mock_firewalld.return_value = True
        firewall_cls = firewall.get_firewall("eth0")
        assert (isinstance(firewall_cls, firewall.Firewalld))

    @patch('blocksatcli.firewall.is_firewalld')
    def test_get_iptables_class(self, mock_firewalld):
        # Firewalld not installed. Use iptables directly
        mock_firewalld.return_value = False
        firewall_cls = firewall.get_firewall("eth0")
        assert (isinstance(firewall_cls, firewall.Iptables))

    @patch('blocksatcli.firewall.runner.run')
    @patch('blocksatcli.firewall.is_firewalld')
    @patch('blocksatcli.config.read_cfg_file')
    def test_add_iptables_rules(self, mock_receiver_cfg, mock_firewalld,
                                mock_runner):
        """Test iptables configuration to accept blocksat traffic
        """
        # Firewalld not installed. Use iptables directly
        mock_firewalld.return_value = False

        mock_runner.return_value.stdout = (
            b"Chain INPUT (policy ACCEPT 0 packets, 0 bytes)\n"
            b"num pkts bytes target prot opt in out source destination\n"
            b" \n")
        mock_receiver_cfg.return_value = {'sat': {'ip': '192.168.0.2'}}

        # Run firewall configuration
        firewall.firewall_subcommand(self.args)

        # Expected iptables calls
        call_get_iptables_rules = call(
            ['iptables', '-L', '-v', '--line-numbers'],
            root=True,
            capture_output=True)
        call_add_iptables_rule_udp = call([
            'iptables', '-I', 'INPUT', '-p', 'udp', '-i', 'eth0', '--match',
            'multiport', '--dports', '4433,4434', '-j', 'ACCEPT'
        ],
                                          root=True)
        call_add_iptables_rule_igmp = call([
            'iptables', '-I', 'INPUT', '-p', 'igmp', '-i', 'eth0', '-j',
            'ACCEPT'
        ],
                                           root=True)
        mock_runner.assert_has_calls([
            # Check if udp rule is set (_is_iptables_udp_rule_set func)
            call_get_iptables_rules,
            # Add udp rule (_add_iptables_rule func)
            call_add_iptables_rule_udp,
            # Check if udp rule was added correctly (_add_iptables_rule func)
            call_get_iptables_rules,
            # Check if igmp rule is set (_is_iptables_igmp_rule_set)
            call_get_iptables_rules,
            # Add igmp rule to iptables (_add_iptables_rule func)
            call_add_iptables_rule_igmp,
            # Check if igmp rule was added correctly (_add_iptables_rule func)
            call_get_iptables_rules
        ])

    @patch('blocksatcli.util.ask_yes_or_no')
    @patch('blocksatcli.firewall.runner.run')
    @patch('blocksatcli.firewall.is_firewalld')
    @patch('blocksatcli.config.read_cfg_file')
    def test_add_firewalld_rules(self, mock_receiver_cfg, mock_firewalld,
                                 mock_runner, mock_ask_yes_or_no):
        """Test firewalld configuration to accept blocksat traffic
        """
        mock_firewalld.return_value = True  # Firewalld installed
        mock_ask_yes_or_no.return_value = True
        mock_receiver_cfg.return_value = {'sat': {'ip': '192.168.0.2'}}
        mock_runner.return_value.returncode = 1  # udp/igmp rule not set

        # Run firewall configuration
        firewall.firewall_subcommand(self.args)

        # Expected firewalld calls
        rich_rule = ("rule "
                     "family=ipv4 "
                     "source address=192.168.0.2 "
                     "destination address=239.0.0.2/32 "
                     "port port=4433-4434 protocol=udp accept")
        add_firewalld_rule_udp = call(
            ["firewall-cmd", "--add-rich-rule", rich_rule], root=True)
        check_firewalld_rule_udp = call(
            ["firewall-cmd", "--quiet", "--query-rich-rule", rich_rule],
            root=True,
            nocheck=True)
        add_firewalld_rule_igmp = call(["firewall-cmd", "--add-protocol=igmp"],
                                       root=True)
        check_firewalld_rule_igmp = call(
            ["firewall-cmd", "--quiet", "--query-protocol=igmp"],
            root=True,
            nocheck=True)

        mock_runner.assert_has_calls([
            # Check if udp rule is set
            check_firewalld_rule_udp,
            # Add udp rule
            add_firewalld_rule_udp,
            # Check if igmp rule is set
            check_firewalld_rule_igmp,
            # Add igmp rule
            add_firewalld_rule_igmp
        ])
