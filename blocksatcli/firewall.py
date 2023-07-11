"""Configure Firewall Rules"""
import logging
from abc import ABC, abstractmethod
from argparse import ArgumentDefaultsHelpFormatter
from shutil import which

from . import config, defs, util

logger = logging.getLogger(__name__)
runner = util.ProcessRunner(logger)


class BaseFirewall(ABC):

    @abstractmethod
    def verify(self, ports: list, src_ip: str, igmp: bool) -> bool:
        pass

    @abstractmethod
    def configure(self, ports: list, src_ip: str, igmp: bool,
                  prompt: bool) -> None:
        pass


class Iptables(BaseFirewall):

    def __init__(self, net_if):
        self.net_if = net_if

    def _get_cmd(self, ports, igmp):
        """Get command-line options to configure iptables"""
        cmd = [
            "iptables",
            "-I",
            "INPUT",
            "-p",
            "udp",
            "-i",
            self.net_if,
            "--match",
            "multiport",
            "--dports",
            ",".join(ports),
            "-j",
            "ACCEPT",
        ]

        cmd_igmp = [
            "iptables",
            "-I",
            "INPUT",
            "-p",
            "igmp",
            "-i",
            self.net_if,
            "-j",
            "ACCEPT",
        ]

        return cmd if not igmp else cmd_igmp

    def _get_rules(self):
        """Get iptables rules specifically applied to a target interface

        Returns:
            rules (list): List of dictionaries with information of the
            individual matched rules

        """
        # Unfortunately, root privileges are required to read the current
        # firewall rules. Hence, we can't read the current rules without
        # eventually asking the root password in dry-run mode. As a workaround,
        # return an empty list as if the rule was not set yet.
        if (runner.dry):
            return []

        # Get rules
        cmd = ["iptables", "-L", "-v", "--line-numbers"]
        res = runner.run(cmd, root=True, capture_output=True).stdout

        # Parse
        header1 = ""
        header2 = ""
        rules = list()
        for line in res.splitlines():
            if ("Chain INPUT" in line.decode()):
                header1 = line.decode()

            if ("destination" in line.decode()):
                header2 = line.decode()

            if (self.net_if in line.decode()):
                rules.append({
                    'rule': line.decode().split(),
                    'header1': header1,
                    'header2': header2
                })

        return rules

    def _add_rule(self, cmd):
        """Add iptables rule

        Args:
            cmd: List with iptables command.

        """
        assert (cmd[0] != "sudo")

        # Set up the iptables rules
        runner.run(cmd, root=True)

        for rule in self._get_rules():
            if (rule['rule'][3] == "ACCEPT" and rule['rule'][6] == cmd[6]
                    and rule['rule'][4] == cmd[4]):
                if (cmd[4] == "igmp"):
                    logger.info(
                        "Added firewall rule to accept IGMP traffic at the "
                        "{} interface.".format(cmd[6]))
                elif (cmd[4] == "udp" and rule['rule'][12] == cmd[10]):
                    logger.info(
                        "Added firewall rule to accept UDP traffic at the "
                        "{} interface with destination ports {}.".format(
                            cmd[6], cmd[10]))

    def _is_igmp_rule_set(self, cmd):
        """Check if an iptables rule for IGMP is already configured

        Args:
            cmd: List with iptables command.

        Returns:
            True if rule is already set, False otherwise.

        """
        assert (isinstance(cmd, list))
        assert (cmd[0] != "sudo")

        interface = cmd[6]

        for rule in self._get_rules():
            if (rule['rule'][3] == "ACCEPT" and rule['rule'][6] == interface
                    and rule['rule'][4] == "igmp"):
                logger.info(
                    "Firewall rule to accept IGMP traffic at the {} interface "
                    "is already configured.".format(interface))
                return True

        return False

    def _is_udp_rule_set(self, cmd):
        """Check if an iptables rule for UDP is already configured

        Args:
            net_if : Network interface name.
            cmd    : List with iptables command.

        Returns:
            True if rule is already set, False otherwise.

        """
        assert (isinstance(cmd, list))
        assert (cmd[0] != "sudo")

        protocol = cmd[4]
        interface = cmd[6]
        dest_ports = cmd[10]

        for rule in self._get_rules():
            if (rule['rule'][3] == "ACCEPT" and rule['rule'][6] == interface
                    and rule['rule'][4] == protocol
                    and rule['rule'][12] == dest_ports):
                logger.info(
                    "Firewall rule to accept UDP traffic at the {} interface "
                    "with destination ports {} is already configured.".format(
                        interface, dest_ports))
                return True
        return False

    def verify(self, ports: list, src_ip: str, igmp: bool = False) -> bool:
        """Verify if iptables rules are set

        Args:
            ports   : UDP ports used by satellite traffic.
            src_ip  : Source IP to whitelist (unique to each satellite).
            igmp    : Whether or not to configure rule to accept IGMP queries.

        Returns:
            True if rule is already set, False otherwise.

        """
        # Check UDP rule
        cmd = self._get_cmd(ports, igmp=False)
        is_rule_set = self._is_udp_rule_set(cmd)

        if not is_rule_set or not igmp:
            # Early return if UDP rules are not set. If that is the case,
            # we need to run the configuration process anyway.
            return is_rule_set

        # Check IGMP rule
        cmd = self._get_cmd(ports, igmp=True)
        is_igmp_rule_set = self._is_igmp_rule_set(cmd)

        return is_igmp_rule_set

    def configure(self,
                  ports: list,
                  src_ip: str,
                  igmp: bool = False,
                  prompt: bool = True) -> None:
        """Configure iptables rules on DVB-S2 interface

        Args:
            ports  : Ports used for blocks traffic and API traffic.
            igmp   : Whether or not to configure rule to accept IGMP queries.
            prompt : Ask yes/no before applying any changes.

        """

        cmd = self._get_cmd(ports, igmp=False)

        util.fill_print(
            "A firewall rule is required to accept Blocksat traffic arriving "
            + "through interface {} towards UDP ports {}.".format(
                self.net_if, ",".join(ports)))

        if (runner.dry):
            util.fill_print("The following command would be executed:")

        if (not self._is_udp_rule_set(cmd)):
            if (runner.dry or (not prompt) or util.ask_yes_or_no(
                    "Add the corresponding ACCEPT firewall rule?")):
                self._add_rule(cmd)
            else:
                print("\nFirewall configuration cancelled")

        # We're done, unless we also need to configure an IGMP rule
        if (not igmp):
            return

        # IGMP rule supports standalone DVB receivers. The host in this case
        # will need to periodically send IGMP membership reports in order for
        # upstream switches between itself and the DVB receiver to continue
        # delivering the multicast-addressed traffic. This overcomes the
        # scenario where group membership timeouts are implemented by the
        # intermediate switches.
        cmd = self._get_cmd(ports, igmp=True)

        print()
        util.fill_print(
            "A firewall rule is required to accept IGMP queries arriving "
            "from the standalone DVB-S2 receiver on interface {}.".format(
                self.net_if))

        if (runner.dry):
            util.fill_print("The following command would be executed:")

        if (not self._is_igmp_rule_set(cmd)):
            if (runner.dry or (not prompt) or util.ask_yes_or_no(
                    "Add the corresponding ACCEPT firewall rule?")):
                self._add_rule(cmd)
            else:
                print("\nIGMP firewall rule cancelled")


class Firewalld(BaseFirewall):

    def __init__(self, net_if):
        self.net_if = net_if

    def _get_rich_rule(self, src_ip, mcast_ip, portrange):
        """Get firewalld rich rule to accept Blocksat traffic"""
        return ("rule "
                "family=ipv4 "
                "source address={} "
                "destination address={}/32 "
                "port port={} protocol=udp accept".format(
                    src_ip, mcast_ip, portrange))

    def _is_udp_rule_set(self, src_ip, mcast_ip, portrange):
        """Check if firewalld rule for UDP is already configured

        Args:
            src_ip: Source IP address.
            mcast_ip: Destination IP address.
            portrange: Destination port range.

        Returns:
            True if rule is already set, False otherwise.

        """
        rich_rule = self._get_rich_rule(src_ip, mcast_ip, portrange)
        cmd = [
            'firewall-cmd', '--quiet', '--query-rich-rule',
            "{}".format(rich_rule)
        ]
        res = runner.run(cmd, root=True, nocheck=True)
        is_rule_set = res is not None and res.returncode == 0

        if is_rule_set:
            logger.info("Firewall rule to accept UDP traffic from IP address "
                        "{} to the destination IP address {} in ports {} "
                        "is already configured.".format(
                            src_ip, mcast_ip, portrange))

        return is_rule_set

    def _is_igmp_rule_set(self):
        """Check if firewalld rule for UDP is already configured

        Args:
            rich_rule: Firewalld rich rule.

        Returns:
            True if rule is already set, False otherwise.

        """
        cmd = ['firewall-cmd', '--quiet', '--query-protocol=igmp']
        res = runner.run(cmd, root=True, nocheck=True)
        is_rule_set = res is not None and res.returncode == 0

        if is_rule_set:
            logger.info(
                "Firewall rule to accept IGMP traffic is already configured.")

        return is_rule_set

    def verify(self, ports: list, src_ip: str, igmp: bool = False) -> bool:
        """Verify if firewalld rules are set

        Args:
            ports  : UDP ports used by satellite traffic.
            src_ip : Source IP to whitelist (unique to each satellite).
            igmp   : Whether or not to configure rule to accept IGMP queries.

        Returns:
            True if rule is already set, False otherwise.

        """
        if len(ports) > 1:
            portrange = "{}-{}".format(min(ports), max(ports))
        else:
            portrange = ports

        # Check UDP rule
        is_rule_set = self._is_udp_rule_set(src_ip, defs.mcast_ip, portrange)
        if not is_rule_set or not igmp:
            # Early return if UDP rules are not set. If that is the case,
            # we need to run the configuration process anyway.
            return is_rule_set

        # Check IGMP rule
        is_igmp_rule_set = self._is_igmp_rule_set()
        return is_igmp_rule_set

    def configure(self,
                  ports: list,
                  src_ip: str,
                  igmp: bool = False,
                  prompt: bool = False) -> None:
        """Configure firewalld for blocksat and IGMP traffic

        Add one rich rule for blocksat traffic coming specifically from the
        satellite of choice (corresponding to the given source IP) and another
        rich rule (if necessary) for IGMP traffic.

        NOTE: unlike the iptables configuration, the current firewalld
        configuration disregards the network interface. The alternative to
        consider the interface is to use firewalld zones. However, because the
        network interface may not be dedicated to DVB-S2 traffic (e.g., when
        using a standalone receiver), it can be undesirable to assign the
        interface receiving satellite traffic to a dedicated zone just for
        blocksat. In contrast, the rich rule approach is more generic and works
        for all types of receivers.

        """
        if len(ports) > 1:
            portrange = "{}-{}".format(min(ports), max(ports))
        else:
            portrange = ports

        util.fill_print(
            "- Configure the firewall to accept Blocksat traffic arriving " +
            "from {} towards address {} on UDP ports {}:\n".format(
                src_ip, defs.mcast_ip, portrange))

        if (not runner.dry and prompt):
            if (not util.ask_yes_or_no("Add firewalld rule?")):
                print("\nFirewall configuration cancelled")
                return

        if (not self._is_udp_rule_set(src_ip, defs.mcast_ip, portrange)):
            rich_rule = self._get_rich_rule(src_ip, defs.mcast_ip, portrange)
            runner.run(
                ['firewall-cmd', '--add-rich-rule', "{}".format(rich_rule)],
                root=True)
            logger.info("Added firewall rule to accept UDP traffic from "
                        "IP address {} to destination address {} "
                        "on ports {}.".format(src_ip, defs.mcast_ip,
                                              portrange))

        if (runner.dry):
            print()
            util.fill_print(
                "NOTE: Add \"--permanent\" to make it persistent. In this "
                "case, remember to reload firewalld afterwards.")

        # We're done, unless we also need to configure an IGMP rule
        if (not igmp):
            return

        util.fill_print(
            "- Allow IGMP packets. This is necessary when using a standalone "
            "DVB-S2 receiver connected through a switch:\n")

        if (not runner.dry and prompt):
            if (not util.ask_yes_or_no("Enable IGMP on the firewall?")):
                print("\nFirewall configuration cancelled")
                return

        if (not self._is_igmp_rule_set()):
            runner.run(['firewall-cmd', '--add-protocol=igmp'], root=True)
            logger.info("Added firewall rule to accept IGMP traffic.")


def is_firewalld():
    """Check if the firewall is based on firewalld"""
    if (which('firewall-cmd') is None):
        return False

    if (which('systemctl') is None):
        # Can't check whether firewalld is running
        return False

    # Run the following commands even in dry-run mode
    res1 = runner.run(['systemctl', 'is-active', '--quiet', 'firewalld'],
                      nodry=True,
                      nocheck=True)
    res2 = runner.run(['systemctl', 'is-active', '--quiet', 'iptables'],
                      nodry=True,
                      nocheck=True)

    # If running (active), 'is-active' returns 0
    if (res1.returncode == 0 and res2.returncode == 0):
        raise ValueError(
            "Failed to detect firewall system (firewalld or iptables)")

    return (res1.returncode == 0)


def get_firewall(net_if) -> BaseFirewall:
    if is_firewalld():
        return Firewalld(net_if)
    else:
        return Iptables(net_if)


def verify(net_ifs, ports, src_ip, igmp=False):
    assert (isinstance(net_ifs, list))
    firewall_set = list()

    for net_if in net_ifs:
        firewall = get_firewall(net_if)
        res = firewall.verify(ports, src_ip, igmp)
        firewall_set.append(res)

    return all(firewall_set)


def configure(net_ifs, ports, src_ip, igmp=False, prompt=True, dry=False):
    """Configure firewall rules to accept blocksat traffic via DVB interface

    Args:
        net_ifs : List of DVB network interface names.
        ports   : UDP ports used by satellite traffic.
        src_ip  : Source IP to whitelist (unique to each satellite).
        igmp    : Whether or not to configure rule to accept IGMP queries.
        prompt  : Prompt user to accept configurations before executing them.
        dry     : Dry run mode.

    """
    assert (isinstance(net_ifs, list))
    runner.set_dry(dry)
    util.print_header("Firewall Rules")

    for i, net_if in enumerate(net_ifs):
        firewall = get_firewall(net_if)
        firewall.configure(ports, src_ip, igmp, prompt)

        if (i < len(net_ifs) - 1):
            print("")


def subparser(subparsers):  # pragma: no cover
    """Parser for firewall command"""
    p = subparsers.add_parser('firewall',
                              description="Set firewall rules",
                              help='Set firewall rules',
                              formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-i',
                   '--interface',
                   required=True,
                   help='Network interface')
    p.add_argument(
        '--standalone',
        default=False,
        action='store_true',
        help='Apply configurations for a standalone DVB-S2 receiver')
    p.add_argument('-y',
                   '--yes',
                   default=False,
                   action='store_true',
                   help="Default to answering Yes to configuration prompts")
    p.add_argument("--dry-run",
                   action='store_true',
                   default=False,
                   help="Print all commands but do not execute them")
    p.set_defaults(func=firewall_subcommand)
    return p


def firewall_subcommand(args):
    """Call function that sets firewall rules

    Handles the firewall subcommand

    """
    user_info = config.read_cfg_file(args.cfg, args.cfg_dir)

    if (user_info is None):
        return

    configure([args.interface],
              defs.src_ports,
              user_info['sat']['ip'],
              igmp=args.standalone,
              prompt=(not args.yes),
              dry=args.dry_run)
