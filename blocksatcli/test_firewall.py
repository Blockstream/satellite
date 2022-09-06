import argparse
from unittest import TestCase
from unittest.mock import patch, call

from . import firewall


class TestFirewall(TestCase):

    def setUp(self):
        # Add minimum args to firewall configuration
        self.args = argparse.Namespace(cfg='',
                                       cfg_dir='',
                                       interface='eth0',
                                       standalone=True,
                                       dry_run=False,
                                       yes=True)

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
        # Firewalld installed
        mock_firewalld.return_value = True

        mock_ask_yes_or_no.return_value = True
        mock_receiver_cfg.return_value = {'sat': {'ip': '192.168.0.2'}}

        # Run firewall configuration
        firewall.firewall_subcommand(self.args)

        # Expected firewalld calls
        add_firewalld_rule_udp = call([
            "firewall-cmd", "--add-rich-rule",
            ("rule "
             "family=ipv4 "
             "source address=192.168.0.2 "
             "destination address=239.0.0.2/32 "
             "port port=4433-4434 protocol=udp accept")
        ],
                                      root=True)
        add_firewalld_rule_igmp = call(["firewall-cmd", "--add-protocol=igmp"],
                                       root=True)
        mock_runner.assert_has_calls(
            [add_firewalld_rule_udp, add_firewalld_rule_igmp])
