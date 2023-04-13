"""Configure Firewall Rules"""
import logging
from argparse import ArgumentDefaultsHelpFormatter
from shutil import which
from . import util, defs, config

logger = logging.getLogger(__name__)
runner = util.ProcessRunner(logger)


def _get_iptables_rules(net_if):
    """Get iptables rules that are specifically applied to a target interface

    Args:
        net_if : network interface name

    Returns:
        list of dictionaries with information of the individual matched rules

    """
    # Unfortunately, root privileges are required to read the current firewall
    # rules. Hence, we can't read the current rules without eventually asking
    # the root password in dry-run mode. As a workaround, return an empty list
    # as if the rule was not set yet.
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

        if (net_if in line.decode()):
            rules.append({
                'rule': line.decode().split(),
                'header1': header1,
                'header2': header2
            })

    return rules


def _is_iptables_igmp_rule_set(net_if, cmd):
    """Check if an iptables rule for IGMP is already configured

    Args:
        net_if : network interface name
        cmd    : list with iptables command

    Returns:
        True if rule is already set, False otherwise.

    """
    assert (cmd[0] != "sudo")
    for rule in _get_iptables_rules(net_if):
        if (rule['rule'][3] == "ACCEPT" and rule['rule'][6] == cmd[6]
                and rule['rule'][4] == "igmp"):
            print("\nFirewall rule for IGMP already configured\n")
            print(rule['header1'])
            print(rule['header2'])
            print(" ".join(rule['rule']))
            print("\nSkipping...")
            return True

    return False


def _is_iptables_udp_rule_set(net_if, cmd):
    """Check if an iptables rule for UDP is already configured

    Args:
        net_if : network interface name
        cmd    : list with iptables command

    Returns:
        True if rule is already set, False otherwise.

    """
    assert (cmd[0] != "sudo")
    for rule in _get_iptables_rules(net_if):
        if (rule['rule'][3] == "ACCEPT" and rule['rule'][6] == cmd[6]
                and rule['rule'][4] == "udp" and rule['rule'][12] == cmd[10]):
            print("\nFirewall rule already configured\n")
            print(rule['header1'])
            print(rule['header2'])
            print(" ".join(rule['rule']))
            print("\nSkipping...")
            return True

    return False


def _is_firewalld_udp_rule_set(rich_rule):
    """Check if firewalld rule for UDP is already configured

    Args:
        rich_rule: Firewalld rich rule

    Returns:
        True if rule is already set, False otherwise.

    """
    cmd = ['firewall-cmd', '--query-rich-rule', "{}".format(rich_rule)]
    res = runner.run(cmd, root=True, capture_output=True).stdout

    return res == "yes"


def _is_firewalld_igmp_rule_set():
    """Check if firewalld rule for UDP is already configured

    Args:
        rich_rule: Firewalld rich rule

    Returns:
        True if rule is already set, False otherwise.

    """
    cmd = ['firewall-cmd', '--query-protocol=igmp']
    res = runner.run(cmd, root=True, capture_output=True).stdout

    return res == "yes"


def _add_iptables_rule(net_if, cmd):
    """Add iptables rule

    Args:
        net_if : network interface name
        cmd    : list with iptables command

    """
    assert (cmd[0] != "sudo")

    # Set up the iptables rules
    runner.run(cmd, root=True)

    for rule in _get_iptables_rules(net_if):
        print_rule = False

        if (rule['rule'][3] == "ACCEPT" and rule['rule'][6] == cmd[6]
                and rule['rule'][4] == cmd[4]):
            if (cmd[4] == "igmp"):
                print_rule = True
            elif (cmd[4] == "udp" and rule['rule'][12] == cmd[10]):
                print_rule = True

            if (print_rule):
                print("Added iptables rule:\n")
                print(rule['header1'])
                print(rule['header2'])
                print(" ".join(rule['rule']) + "\n")


def _get_iptables_cmd(net_if, ports, igmp):
    """Get command-line options to configure iptables"""
    cmd = [
        "iptables",
        "-I",
        "INPUT",
        "-p",
        "udp",
        "-i",
        net_if,
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
        net_if,
        "-j",
        "ACCEPT",
    ]

    return cmd if not igmp else cmd_igmp


def _get_firewalld_rich_rule(src_ip, mcast_ip, portrange):
    """Get firewalld rich rule to accept Blocksat traffic"""
    return ("rule "
            "family=ipv4 "
            "source address={} "
            "destination address={}/32 "
            "port port={} protocol=udp accept".format(src_ip, mcast_ip,
                                                      portrange))


def _configure_iptables(net_if, ports, igmp=False, prompt=True):
    """Configure iptables rules on DVB-S2 interface

    Args:
        net_if : DVB network interface name
        ports  : ports used for blocks traffic and API traffic
        igmp   : Whether or not to configure rule to accept IGMP queries
        prompt : Ask yes/no before applying any changes

    """

    cmd = _get_iptables_cmd(net_if, ports, igmp=False)

    util.fill_print(
        "A firewall rule is required to accept Blocksat traffic arriving " +
        "through interface {} towards UDP ports {}.".format(
            net_if, ",".join(ports)))

    if (runner.dry):
        util.fill_print("The following command would be executed:")

    if (not _is_iptables_udp_rule_set(net_if, cmd)):
        if (runner.dry or (not prompt) or util.ask_yes_or_no(
                "Add the corresponding ACCEPT firewall rule?")):
            _add_iptables_rule(net_if, cmd)
        else:
            print("\nFirewall configuration cancelled")

    # We're done, unless we also need to configure an IGMP rule
    if (not igmp):
        return

    # IGMP rule supports standalone DVB receivers. The host in this case will
    # need to periodically send IGMP membership reports in order for upstream
    # switches between itself and the DVB receiver to continue delivering the
    # multicast-addressed traffic. This overcomes the scenario where group
    # membership timeouts are implemented by the intermediate switches.
    cmd = _get_iptables_cmd(net_if, ports, igmp=True)

    print()
    util.fill_print(
        "A firewall rule is required to accept IGMP queries arriving from the "
        "standalone DVB-S2 receiver on interface {}.".format(net_if))

    if (runner.dry):
        util.fill_print("The following command would be executed:")

    if (not _is_iptables_igmp_rule_set(net_if, cmd)):
        if (runner.dry or (not prompt) or util.ask_yes_or_no(
                "Add the corresponding ACCEPT firewall rule?")):
            _add_iptables_rule(net_if, cmd)
        else:
            print("\nIGMP firewall rule cancelled")


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


def _configure_firewalld(net_if, ports, src_ip, igmp, prompt):
    """Configure firewalld for blocksat and IGMP traffic

    Add one rich rule for blocksat traffic coming specifically from the
    satellite of choice (corresponding to the given source IP) and another rich
    rule (if necessary) for IGMP traffic.

    NOTE: unlike the iptables configuration, the current firewalld
    configuration disregards the network interface. The alternative to consider
    the interface is to use firewalld zones. However, because the network
    interface may not be dedicated to DVB-S2 traffic (e.g., when using a
    standalone receiver), it can be undesirable to assign the interface
    receiving satellite traffic to a dedicated zone just for blocksat. In
    contrast, the rich rule approach is more generic and works for all types of
    receivers.

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

    rich_rule = _get_firewalld_rich_rule(src_ip, defs.mcast_ip, portrange)
    runner.run(['firewall-cmd', '--add-rich-rule', "{}".format(rich_rule)],
               root=True)

    if (runner.dry):
        print()
        util.fill_print(
            "NOTE: Add \"--permanent\" to make it persistent. In this case, "
            "remember to reload firewalld afterwards.")

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

    runner.run(['firewall-cmd', '--add-protocol=igmp'], root=True)
    print()


def _verify_firewalld(ports, src_ip, igmp):
    """Verify if firewalld rules are set

    Args:
        ports   : UDP ports used by satellite traffic
        src_ip  : Source IP to whitelist (unique to each satellite)
        igmp    : Whether or not to configure rule to accept IGMP queries

    Returns:
        True if rule is already set, False otherwise.

    """
    if len(ports) > 1:
        portrange = "{}-{}".format(min(ports), max(ports))
    else:
        portrange = ports

    # Check UDP rule
    rich_rule = _get_firewalld_rich_rule(src_ip, defs.mcast_ip, portrange)
    is_rule_set = _is_firewalld_udp_rule_set(rich_rule)

    if not is_rule_set or not igmp:
        # Early return if UDP rules are not set. If that is the case,
        # we need to run the configuration process anyway.
        return is_rule_set

    # Check IGMP rule
    is_igmp_rule_set = _is_firewalld_igmp_rule_set()
    return is_igmp_rule_set


def _verify_iptables(net_if, ports, src_ip, igmp):
    """Verify if iptables rules are set

    Args:
        net_ifs : List of DVB network interface names
        ports   : UDP ports used by satellite traffic
        src_ip  : Source IP to whitelist (unique to each satellite)
        igmp    : Whether or not to configure rule to accept IGMP queries

    Returns:
        True if rule is already set, False otherwise.

    """
    # Check UDP rule
    cmd = _get_iptables_cmd(net_if, ports, igmp=False)
    is_rule_set = _is_iptables_udp_rule_set(net_if, cmd)

    if not is_rule_set or not igmp:
        # Early return if UDP rules are not set. If that is the case,
        # we need to run the configuration process anyway.
        return is_rule_set

    # Check IGMP rule
    cmd = _get_iptables_cmd(net_if, ports, igmp=True)
    is_igmp_rule_set = _is_iptables_igmp_rule_set(net_if, cmd)

    return is_igmp_rule_set


def verify(net_ifs, ports, src_ip, igmp=False):
    assert (isinstance(net_ifs, list))
    firewall_set = list()
    for net_if in net_ifs:
        if (is_firewalld()):
            res = _verify_firewalld(ports, src_ip, igmp)
        else:
            res = _verify_iptables(net_if, ports, src_ip, igmp)

        firewall_set.append(res)

    return all(firewall_set)


def configure(net_ifs, ports, src_ip, igmp=False, prompt=True, dry=False):
    """Configure firewallrules to accept blocksat traffic via DVB interface

    Args:
        net_ifs : List of DVB network interface names
        ports   : UDP ports used by satellite traffic
        src_ip  : Source IP to whitelist (unique to each satellite)
        igmp    : Whether or not to configure rule to accept IGMP queries
        prompt  : Prompt user to accept configurations before executing them
        dry     : Dry run mode

    """
    assert (isinstance(net_ifs, list))
    runner.set_dry(dry)
    util.print_header("Firewall Rules")

    for i, net_if in enumerate(net_ifs):
        if (is_firewalld()):
            _configure_firewalld(net_if, ports, src_ip, igmp, prompt)
        else:
            _configure_iptables(net_if, ports, igmp, prompt)

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
