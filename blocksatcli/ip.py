"""Configure IP Address of DVB Interfaces"""
from ipaddress import IPv4Interface
import os, subprocess, logging
from . import util
import textwrap
from shutil import which
logger = logging.getLogger(__name__)


def _check_debian_net_interfaces_d(is_root):
    """Check if /etc/network/interfaces.d/ is included as source-directory

    If the distribution doesn't have the `/etc/network/interface` directory,
    just return.

    """
    if_file  = "/etc/network/interfaces"

    if (not os.path.exists(if_file)):
        return

    if_dir   = "/etc/network/interfaces.d/"
    src_line = "source /etc/network/interfaces.d/*"

    if (not is_root):
        print(textwrap.fill("Make sure directory "
                            "\"{}\" "
                            "is considered as source for network "
                            "interface configurations. "
                            "Check if your \"{}\" file "
                            "contains the following line:".format(
                                if_dir, if_file
                            )))
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


def _add_to_netplan(ifname, addr_with_prefix, is_root):
    """Create configuration file at /etc/netplan/"""
    assert("/" in addr_with_prefix)
    cfg_dir = "/etc/netplan/"

    cfg = ("network:\n"
           "  version: 2\n"
           "  renderer: networkd\n"
           "  ethernets:\n"
           "    {0}:\n"
           "      dhcp4: no\n"
           "      optional: true\n"
           "      addresses: [{1}]\n").format(
               ifname, addr_with_prefix)

    fname  = "blocksat-" + ifname + ".yaml"
    path   = os.path.join(cfg_dir, fname)

    if (not is_root):
        print(textwrap.fill("Create a file named {} at {} and add the "
                            "following to it:".format(fname, cfg_dir)))
        print("\n" + cfg + "\n")
        return

    with open(path, 'w') as fd:
        fd.write(cfg)

    print("Created configuration file {} in {}".format(fname, cfg_dir))


def _add_to_interfaces_d(ifname, addr, netmask, is_root):
    """Create configuration file at /etc/network/interfaces.d/"""
    if_dir = "/etc/network/interfaces.d/"
    cfg = ("iface {0} inet static\n"
           "    address {1}\n"
           "    netmask {2}\n").format(ifname, addr, netmask)
    fname  = ifname + ".conf"
    path   = os.path.join(if_dir, fname)

    if (not is_root):
        print(textwrap.fill("Create a file named {} at {} and add the "
                            "following to it:".format(fname, if_dir)))
        print("\n" + cfg + "\n")
        return

    with open(path, 'w') as fd:
        fd.write(cfg)

    print("Created configuration file {} in {}".format(fname, if_dir))


def _add_to_sysconfig_net_scripts(ifname, addr, netmask, is_root):
    """Create configuration file at /etc/sysconfig/network-scripts/"""
    cfg_dir = "/etc/sysconfig/network-scripts/"
    cfg = ("NM_CONTROLLED=\"yes\"\n"
           "DEVICE=\"{0}\"\n"
           "BOOTPROTO=none\n"
           "ONBOOT=\"no\"\n"
           "IPADDR={1}\n"
           "NETMASK={2}\n").format(ifname, addr, netmask)

    fname  = "ifcfg-" + ifname
    path   = os.path.join(cfg_dir, fname)

    if (not is_root):
        print(textwrap.fill("Create a file named {} at {} and add the "
                            "following to it:".format(fname, cfg_dir)))
        print("\n" + cfg + "\n")
        return

    with open(path, 'w') as fd:
        fd.write(cfg)

    print("Created configuration file {} in {}".format(fname, cfg_dir))


def _set_static_iface_ip(ifname, ipv4_if, is_root):
    """Set static IP address for target network interface

    Args:
        ifname  : Network device name
        ipv4_if : IPv4Interface object with the target interface address
        is_root : (bool) whether running as root

    """
    isinstance(ipv4_if, IPv4Interface)
    addr                = str(ipv4_if.ip)
    addr_with_prefix    = ipv4_if.with_prefixlen
    netmask             = str(ipv4_if.netmask)

    if (which("netplan") is not None):
        _add_to_netplan(ifname, addr_with_prefix, is_root)
    elif (os.path.exists("/etc/network/interfaces.d/")):
        _add_to_interfaces_d(ifname, addr, netmask, is_root)
    elif (os.path.exists("/etc/sysconfig/network-scripts")):
        _add_to_sysconfig_net_scripts(ifname, addr, netmask, is_root)
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
    except subprocess.CalledProcessError as e:
        return False, False

    has_ip = False
    ip_ok  = False
    for line in res.splitlines():
        if "inet" in line.decode() and "inet6" not in line.decode():
            has_ip    = True
            # Check if IP matches target
            inet_info = line.decode().split()
            inet_if   = IPv4Interface(inet_info[1])
            target_if = IPv4Interface(ip_addr)
            ip_ok     = (inet_if == target_if)
            break

    return has_ip, ip_ok


def _set_ip(net_if, ip_addr, verbose):
    """Set the IP of the DVB network interface

    Args:
        net_if    : DVB network interface name
        ip_addr   : Target IP address for the DVB interface slash subnet mask
        verbose   : Controls verbosity

    """
    is_root       = (os.geteuid() == 0)
    inet_if       = IPv4Interface(ip_addr)

    # Flush previous IP
    if (not is_root):
        print("Flush any IP address from {}:\n".format(net_if))
    res = util.run_or_print_root_cmd(["ip", "address", "flush", "dev", net_if],
                                     logger)

    # Configure new static IP
    _set_static_iface_ip(net_if, inet_if, is_root)


def set_ips(net_ifs, ip_addrs, verbose=True):
    """Set IPs of one or multiple DVB network interface(s

    Args:
        net_ifs   : List of DVB network interface names
        ip_addrs  : List of IP addresses for the DVB interface slash subnet mask
        verbose   : Controls verbosity

    """
    if (verbose):
        util._print_header("Interface IP Address")

    is_root = os.geteuid() == 0
    if (not is_root):
        print("Set static IP addresses on dvbnet interfaces.\n")

    # Configure static IP addresses
    if (which("netplan") is None):
        _check_debian_net_interfaces_d(is_root)

    for net_if, ip_addr in zip(net_ifs, ip_addrs):
        _set_ip(net_if, ip_addr, verbose)

    # Bring up interfaces
    if (which("netplan") is not None):
        if (not is_root):
            print("Finally, apply the new netplan configuration:\n")
        util.run_or_print_root_cmd(["netplan", "apply"], logger)
    elif (os.path.exists("/etc/network/interfaces.d/")):
        # Debian approach
        if (not is_root):
            print(textwrap.fill("Finally, restart the networking service and "
                                "bring up the interfaces:") + "\n")
        util.run_or_print_root_cmd(["systemctl", "restart", "networking"],
                                   logger)
    elif (os.path.exists("/etc/sysconfig/network-scripts")):
        # CentOS/Fedora/RHEL approach
        if (not is_root):
            print(textwrap.fill("Finally, bring up the interfaces:") + "\n")

    if (which("netplan") is None):
        for net_if in net_ifs:
            util.run_or_print_root_cmd(["ifup", net_if], logger)


def check_ips(net_ifs, ip_addrs):
    """Check if IPs of one or multiple DVB network interface(s) are OK

    Args:
        net_ifs   : List of DVB network interface names
        ip_addrs  : List of IP addresses for the DVB interface slash subnet mask
        verbose   : Controls verbosity

    """
    for net_if, ip_addr in zip(net_ifs, ip_addrs):
        has_ip, ip_ok = _check_ip(net_if, ip_addr)
        if (not has_ip):
            raise ValueError("Interface {} does not have an IP address".format(
                net_if))
        elif (has_ip and not ip_ok):
            raise ValueError("Interface {} IP is not {}".format(net_if,
                                                                ip_addr))


def rm_ip(ifname):
    """Remove the static IP configuration of a given interface"""
    # Remove conf file for network interface (next time the interface could have
    # a different number)
    netplan_file = os.path.join("/etc/netplan/", "blocksat-" + ifname + ".yaml")
    net_file     = os.path.join("/etc/network/interfaces.d/", ifname + ".conf")
    ifcfg_file   = os.path.join("/etc/sysconfig/network-scripts/",
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
        res = util.run_or_print_root_cmd(["rm", cfg_file])
        print("Removed configuration file {}".format(cfg_file))


def compute_rx_ips(sat_ip, n_ips, subnet="/29"):
    """Compute Rx IPs within the same subnet as the satellite Tx

    Args:
        sat_ip : satellite IP in CIDR notation
        n_ips  : Request number of IPs

    Returns:
        ips list of IPs

    """
    sat_ip_split = [x for x in sat_ip.split(".")]
    assert(len(sat_ip_split) == 4)
    base_ip     = ".".join(sat_ip_split[0:3])
    sat_ip_term = int(sat_ip[-1])
    base_offset = 3 # 3 reserved IPs for Tx host and modulator

    ips = list()
    for i in range(0, n_ips):
        rx_ip_term = sat_ip_term + base_offset + i
        ips.append(base_ip + "." + str(rx_ip_term) + subnet)
    return ips


