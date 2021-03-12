"""Configure Firewall Rules"""
import subprocess, logging, os
from argparse import ArgumentDefaultsHelpFormatter
from shutil import which
from . import util, defs, config


logger = logging.getLogger(__name__)


def _get_iptables_rules(net_if):
    """Get iptables rules that are specifically applied to a target interface

    Args:
        net_if : network interface name

    Returns:
        list of dictionaries with information of the individual matched rules

    """



    # Get rules
    cmd = util.root_cmd(["iptables", "-L", "-v", "--line-numbers"])
    res = subprocess.check_output(cmd)

    # Parse
    header1 = ""
    header2 = ""
    rules   = list()
    for line in res.splitlines():
        if ("Chain INPUT" in line.decode()):
            header1 = line.decode()

        if ("destination" in line.decode()):
            header2 = line.decode()

        if (net_if in line.decode()):
            rules.append({
                'rule' : line.decode().split(),
                'header1' : header1,
                'header2' : header2
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
    offset = 1 if cmd[0] == "sudo" else 0

    for rule in _get_iptables_rules(net_if):
        if (rule['rule'][3] == "ACCEPT" and
            rule['rule'][6] == cmd[6 + offset] and
            rule['rule'][4] == "igmp"):
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
    offset = 1 if cmd[0] == "sudo" else 0
    for rule in _get_iptables_rules(net_if):
        if (rule['rule'][3] == "ACCEPT" and
            rule['rule'][6] == cmd[6 + offset] and
            (rule['rule'][4] == "udp" and
             rule['rule'][12] == cmd[10 + offset])):
            print("\nFirewall rule already configured\n")
            print(rule['header1'])
            print(rule['header2'])
            print(" ".join(rule['rule']))
            print("\nSkipping...")
            return True

    return False


def _add_iptables_rule(net_if, cmd):
    """Add iptables rule

    Args:
        net_if : network interface name
        cmd    : list with iptables command

    """
    offset = 1 if cmd[0] == "sudo" else 0

    # Set up iptables rules
    logging.debug("> " + " ".join(cmd))
    subprocess.check_output(cmd)

    for rule in _get_iptables_rules(net_if):
        print_rule = False

        if (rule['rule'][3] == "ACCEPT" and
            rule['rule'][6] == cmd[6 + offset] and
            rule['rule'][4] == cmd[4 + offset]):
            if (cmd[4 + offset] == "igmp"):
                print_rule = True
            elif (cmd[4 + offset] == "udp" and
                  rule['rule'][12] == cmd[10 + offset]):
                print_rule = True

            if (print_rule):
                print("Added iptables rule:\n")
                print(rule['header1'])
                print(rule['header2'])
                print(" ".join(rule['rule']) + "\n")


def _configure_iptables(net_if, ports, igmp=False, prompt=True):
    """Configure iptables rules to accept blocksat traffic on a DVB-S2 interface

    Args:
        net_if : DVB network interface name
        ports  : ports used for blocks traffic and API traffic
        igmp   : Whether or not to configure rule to accept IGMP queries

    """

    not_root = (os.geteuid() != 0)

    cmd = util.root_cmd([
        "iptables",
        "-I", "INPUT",
        "-p", "udp",
        "-i", net_if,
        "--match", "multiport",
        "--dports", ",".join(ports),
        "-j", "ACCEPT",
    ])

    if (not_root):
        print(" ".join(cmd))
    elif (not _is_iptables_udp_rule_set(net_if, cmd)):
        print("- Configure firewall rule to accept Blocksat traffic arriving " +
              "at interface %s\ntowards UDP ports %s." %(net_if, ",".join(ports)))
        if ((not prompt) or
            util._ask_yes_or_no("Add corresponding ACCEPT firewall rule?")):
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
    cmd = util.root_cmd([
        "iptables",
        "-I", "INPUT",
        "-p", "igmp",
        "-i", net_if,
        "-j", "ACCEPT",
    ])

    if (not_root):
        print(" ".join(cmd))
    elif (not _is_iptables_igmp_rule_set(net_if, cmd)):
        print("Configure also a firewall rule to accept IGMP queries. This is " +
              "necessary when using a standalone DVB-S2 receiver.")
        if ((not prompt) or
            util._ask_yes_or_no("Add corresponding ACCEPT rule on firewall?")):
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

    res1 = subprocess.run(['systemctl', 'is-active', '--quiet', 'firewalld'])
    res2 = subprocess.run(['systemctl', 'is-active', '--quiet', 'iptables'])

    # If running (active), 'is-active' returns 0
    if (res1.returncode == 0 and res2.returncode == 0):
        raise ValueError(
            "Failed to detect firewall system (firewalld or iptables)"
        )

    return (res1.returncode == 0)


def _configure_firewalld(net_if, ports, src_ip, igmp, prompt):
    """Configure firewalld for blocksat and IGMP traffic

    Add one rich rule for blocksat traffic coming specifically from the
    satellite of choice (corresponding to the given source IP) and another rich
    rule (if necessary) for IGMP traffic.

    NOTE: unlike the iptables configuration, the current firewalld configuration
    disregards the network interface. The alternative to consider the interface
    is to use firewalld zones. However, because the network interface may not be
    dedicated to DVB-S2 traffic (e.g., when using a standalone receiver), it can
    be undesirable to assign the interface receiving satellite traffic to a
    dedicated zone just for blocksat. In contrast, the rich rule approach is
    more generic and works for all types of receivers.

    """
    dry_run = os.geteuid() != 0
    runner = util.ProcessRunner(logger, dry_run)

    if len(ports) > 1:
        portrange = "{}-{}".format(min(ports), max(ports))
    else:
        portrange = ports

    util.fill_print(
        "- Configure the firewall to accept Blocksat traffic arriving " +
          "from {} towards address {} on UDP ports {}:\n".format(
              src_ip, defs.mcast_ip, portrange)
    )

    if (not dry_run and prompt):
        if (not util._ask_yes_or_no("Add firewalld rule?")):
            print("\nFirewall configuration cancelled")
            return

    rich_rule = (
        "rule "
        "family=ipv4 "
        "source address={} "
        "destination address={}/32 "
        "port port={} protocol=udp accept".format(
            src_ip, defs.mcast_ip, portrange
        )
    )
    cmd = ['firewall-cmd', '--add-rich-rule', "{}".format(rich_rule)]
    runner.run(util.root_cmd(cmd))

    if (dry_run):
        print()
        util.fill_print(
            "NOTE: Add \"--permanent\" to make it persistent. In this case, "
            "remember to reload firewalld afterwards."
        )

    # We're done, unless we also need to configure an IGMP rule
    if (not igmp):
        return

    util.fill_print(
        "- Allow IGMP packets. This is necessary when using a standalone "
        "DVB-S2 receiver connected through a switch:\n"
    )

    if (not dry_run and prompt):
        if (not util._ask_yes_or_no("Enable IGMP on the firewall?")):
            print("\nFirewall configuration cancelled")
            return

    cmd = ['firewall-cmd', '--add-protocol=igmp']
    runner.run(util.root_cmd(cmd))
    print()


def configure(net_ifs, ports, src_ip, igmp=False, prompt=True):
    """Configure firewallrules to accept blocksat traffic via DVB interface

    Args:
        net_ifs : List of DVB network interface names
        ports   : UDP ports used by satellite traffic
        src_ip  : Source IP to whitelist (unique to each satellite)
        igmp    : Whether or not to configure rule to accept IGMP queries
        prompt  : Prompt user to accept configurations before executing them

    """
    assert(isinstance(net_ifs, list))
    util._print_header("Firewall Rules")

    if (os.geteuid() != 0):
        util.fill_print("Please run blocksat-cli as root or run the following \
        commands on your own:\n")

    for i, net_if in enumerate(net_ifs):
        if (is_firewalld()):
            _configure_firewalld(net_if, ports, src_ip, igmp, prompt)
        else:
            _configure_iptables(net_if, ports, igmp, prompt)

        if (i < len(net_ifs) - 1):
            print("")


def subparser(subparsers):
    """Parser for firewall command"""
    p = subparsers.add_parser('firewall',
                              description="Set firewall rules",
                              help='Set firewall rules',
                              formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-i', '--interface', required = True,
                   help='Network interface')
    p.add_argument('--standalone', default=False,
                   action='store_true',
                   help='Apply configurations for a standalone DVB-S2 receiver')
    p.set_defaults(func=firewall_subcommand)
    return p


def firewall_subcommand(args):
    """Call function that sets firewall rules

    Handles the firewall subcommand

    """
    user_info = config.read_cfg_file(args.cfg, args.cfg_dir)

    if (user_info is None):
        return

    configure([args.interface], defs.src_ports, user_info['sat']['ip'],
              igmp=args.standalone)


