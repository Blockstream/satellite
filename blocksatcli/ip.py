"""Configure IP Address of DVB Interfaces"""
import logging
import os
import subprocess
import textwrap
from ipaddress import IPv4Interface
from shutil import which

from . import util

logger = logging.getLogger(__name__)
runner = util.ProcessRunner(logger)


def _check_debian_net_interfaces_d(dry):
    """Check if /etc/network/interfaces.d/ is included as source-directory

    If the distribution doesn't have the `/etc/network/interface` directory,
    just return.

    """
    if_file = "/etc/network/interfaces"

    if (not os.path.exists(if_file)):
        return

    if_dir = "/etc/network/interfaces.d/"
    src_line = "source /etc/network/interfaces.d/*"

    if (dry):
        util.fill_print(
            "Make sure directory \"{}\" is considered as source for network "
            "interface configurations. Check if your \"{}\" file contains "
            "the following line:".format(if_dir, if_file))
        print("\n{}\n".format(src_line))
        print("If not, add it.\n")
        return

    with open(if_file) as fd:
        current_cfg = fd.read()

    src_included = False
    for line in current_cfg.splitlines():
        if src_line in line:
            src_included = True
            break

    if (src_included):
        return

    with open(if_file, 'a') as fd:
        fd.write("\n" + src_line)


def _add_to_netplan(ifname, addr_with_prefix):
    """Create configuration file at /etc/netplan/"""
    assert ("/" in addr_with_prefix)
    cfg_dir = "/etc/netplan/"

    cfg = ("network:\n"
           "  version: 2\n"
           "  renderer: networkd\n"
           "  ethernets:\n"
           "    {0}:\n"
           "      dhcp4: no\n"
           "      optional: true\n"
           "      addresses: [{1}]\n").format(ifname, addr_with_prefix)

    fname = "blocksat-" + ifname + ".yaml"
    path = os.path.join(cfg_dir, fname)

    if (runner.dry):
        util.fill_print("Create a file named {} at {} and add the "
                        "following to it:".format(fname, cfg_dir))
        print(cfg)
        return

    runner.create_file(cfg, path, root=True)


def _add_to_interfaces_d(ifname, addr, netmask):
    """Create configuration file at /etc/network/interfaces.d/"""
    if_dir = "/etc/network/interfaces.d/"
    cfg = ("iface {0} inet static\n"
           "    address {1}\n"
           "    netmask {2}\n").format(ifname, addr, netmask)
    fname = ifname + ".conf"
    path = os.path.join(if_dir, fname)

    if (runner.dry):
        util.fill_print("Create a file named {} at {} and add the "
                        "following to it:".format(fname, if_dir))
        print(cfg)
        return

    runner.create_file(cfg, path, root=True)


def _add_to_sysconfig_net_scripts(ifname, addr, netmask):
    """Create configuration file at /etc/sysconfig/network-scripts/"""
    cfg_dir = "/etc/sysconfig/network-scripts/"
    cfg = ("NM_CONTROLLED=\"yes\"\n"
           "DEVICE=\"{0}\"\n"
           "BOOTPROTO=none\n"
           "ONBOOT=\"no\"\n"
           "IPADDR={1}\n"
           "NETMASK={2}\n").format(ifname, addr, netmask)

    fname = "ifcfg-" + ifname
    path = os.path.join(cfg_dir, fname)

    if (runner.dry):
        util.fill_print("Create a file named {} at {} and add the "
                        "following to it:".format(fname, cfg_dir))
        print(cfg)
        return

    runner.create_file(cfg, path, root=True)


def _set_static_iface_ip(ifname, ipv4_if):
    """Set static IP address for target network interface

    Args:
        ifname  : Network device name
        ipv4_if : IPv4Interface object with the target interface address

    """
    isinstance(ipv4_if, IPv4Interface)
    addr = str(ipv4_if.ip)
    addr_with_prefix = ipv4_if.with_prefixlen
    netmask = str(ipv4_if.netmask)

    if (which("netplan") is not None):
        _add_to_netplan(ifname, addr_with_prefix)
    elif (os.path.exists("/etc/network/interfaces.d/")):
        _add_to_interfaces_d(ifname, addr, netmask)
    elif (os.path.exists("/etc/sysconfig/network-scripts")):
        _add_to_sysconfig_net_scripts(ifname, addr, netmask)
    else:
        raise ValueError("Could not set a static IP address on interface "
                         "{}".format(ifname))


def _check_ip(net_if, ip_addr):
    """Check if interface has IP and if it matches target IP

    Args:
        net_if  : DVB network interface name
        ip_addr : Target IP address for the DVB interface slash subnet mask

    Returns:
        (Bool, Bool) Tuple of booleans. The first indicates whether interface
        already has an IP. The second indicates whether the interface IP (if
        existing) matches with respect to a target IP.

    """
    try:
        res = subprocess.check_output(["ip", "addr", "show", "dev", net_if],
                                      stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return False, False

    has_ip = False
    ip_ok = False
    for line in res.splitlines():
        if "inet" in line.decode() and "inet6" not in line.decode():
            has_ip = True
            # Check if IP matches target
            inet_info = line.decode().split()
            inet_if = IPv4Interface(inet_info[1])
            target_if = IPv4Interface(ip_addr)
            ip_ok = (inet_if == target_if)
            break

    return has_ip, ip_ok


def _set_ip(net_if, ip_addr, verbose):
    """Set the IP of the DVB network interface

    Args:
        net_if    : DVB network interface name
        ip_addr   : Target IP address for the DVB interface slash subnet mask
        verbose   : Controls verbosity

    """
    inet_if = IPv4Interface(ip_addr)

    # Flush previous IP
    if (runner.dry):
        print("Flush any IP address from interface {}:\n".format(net_if))
    runner.run(["ip", "address", "flush", "dev", net_if], root=True)
    if (runner.dry):
        print()

    # Configure new static IP
    _set_static_iface_ip(net_if, inet_if)


def set_ips(net_ifs, ip_addrs, verbose=True, dry=False):
    """Set IPs of one or multiple DVB network interface(s

    Args:
        net_ifs   : List of DVB network interface names
        ip_addrs  : List of IP addresses for the dvbnet interface's subnet mask
        verbose   : Controls verbosity
        dry       : Dry run mode

    """
    runner.set_dry(dry)

    if (verbose):
        util._print_header("Interface IP Address")

    if (dry):
        print("Configure a static IP address on the dvbnet interface.\n")

    # Configure static IP addresses
    if (which("netplan") is None):
        _check_debian_net_interfaces_d(dry)

    for net_if, ip_addr in zip(net_ifs, ip_addrs):
        _set_ip(net_if, ip_addr, verbose)

    # Bring up interfaces
    if (which("netplan") is not None):
        if (dry):
            print("Finally, apply the new netplan configuration:\n")
        runner.run(["netplan", "apply"], root=True)
    elif (os.path.exists("/etc/network/interfaces.d/")):
        # Debian approach
        if (dry):
            util.fill_print("Finally, restart the networking service and "
                            "bring up the interfaces:")
            print()
        runner.run(["systemctl", "restart", "networking"], root=True)
    elif (os.path.exists("/etc/sysconfig/network-scripts")):
        # CentOS/Fedora/RHEL approach
        if (dry):
            print(textwrap.fill("Finally, bring up the interfaces:") + "\n")

    if (which("netplan") is None):
        for net_if in net_ifs:
            runner.run(["ifup", net_if], root=True)


def check_ips(net_ifs, ip_addrs):
    """Check if IPs of one or multiple DVB network interface(s) are OK

    Args:
        net_ifs   : List of DVB network interface names
        ip_addrs  : List of IP addresses for the dvbnet interface's subnet mask
        verbose   : Controls verbosity

    """
    for net_if, ip_addr in zip(net_ifs, ip_addrs):
        has_ip, ip_ok = _check_ip(net_if, ip_addr)
        if (not has_ip):
            raise ValueError(
                "Interface {} does not have an IP address".format(net_if))
        elif (has_ip and not ip_ok):
            raise ValueError("Interface {} IP is not {}".format(
                net_if, ip_addr))


def rm_ip(ifname, dry=False):
    """Remove the static IP configuration of a given interface"""
    runner.set_dry(dry)

    # Remove conf file for network interface (next time the interface could
    # have a different number)
    netplan_file = os.path.join("/etc/netplan/",
                                "blocksat-" + ifname + ".yaml")
    net_file = os.path.join("/etc/network/interfaces.d/", ifname + ".conf")
    ifcfg_file = os.path.join("/etc/sysconfig/network-scripts/",
                              "ifcfg-" + ifname)

    if (which("netplan") is not None):
        cfg_file = netplan_file
    elif (os.path.exists(net_file)):
        cfg_file = net_file
    elif (os.path.exists(ifcfg_file)):
        cfg_file = ifcfg_file
    else:
        cfg_file = None

    if (cfg_file is not None and os.path.exists(cfg_file)):
        runner.run(["rm", cfg_file], root=True)
        if (not dry):
            logger.info("Removed configuration file {}".format(cfg_file))


def compute_rx_ips(sat_ip, n_ips, subnet="/29"):
    """Compute Rx IPs within the same subnet as the satellite Tx

    Args:
        sat_ip : satellite IP in CIDR notation
        n_ips  : Request number of IPs

    Returns:
        ips list of IPs

    """
    sat_ip_split = [x for x in sat_ip.split(".")]
    assert (len(sat_ip_split) == 4)
    base_ip = ".".join(sat_ip_split[0:3])
    sat_ip_term = int(sat_ip[-1])
    base_offset = 3  # 3 reserved IPs for Tx host and modulator
    assert (n_ips < 5)  # 5 IPs remaining for user equipment
    ips = list()
    for i in range(0, n_ips):
        rx_ip_term = sat_ip_term + base_offset + i
        ips.append(base_ip + "." + str(rx_ip_term) + subnet)
    return ips
