"""Reverse path settings"""
from argparse import ArgumentDefaultsHelpFormatter
import subprocess, os
from . import util


def _read_filter(ifname, stdout=False):
    safe_ifname = ifname.replace(".", "/")
    cmd = ["sysctl", "net.ipv4.conf." + safe_ifname + ".rp_filter"]
    if (stdout):
        print(" ".join(cmd))
        return
    return subprocess.check_output(cmd).split()[-1].decode()


def _write_filter(ifname, val):
    assert(val == "1" or val == "0")
    safe_ifname = ifname.replace(".", "/")
    cmd = ["sysctl", "-w", "net.ipv4.conf." + safe_ifname + ".rp_filter=" + val]

    # Run if root, print if normal user
    if (os.geteuid() == 0):
        action = "Enabling" if val == "1" else "Disabling"
        print("{} RP filter on interface {}".format(action, ifname))
        subprocess.check_output(cmd)
    else:
        print(" ".join(cmd))

def _rm_filter(ifname):
    _write_filter(ifname, "0")


def _add_filter(ifname):
    _write_filter(ifname, "1")


def _check_rp_filters(dvb_if):
    """Check if reverse-path (RP) filters are configured on the interface

    Args:
        dvb_if : DVB network interface

    Return:
        True when configuration is already OK.

    """

    # Check current configuration of DVB interface and "all" rule:
    dvb_cfg = _read_filter(dvb_if)
    all_cfg = _read_filter("all")

    return (dvb_cfg == "0" and all_cfg == "0")


def _set_filters(dvb_ifs, non_root):
    """Disable reverse-path (RP) filtering for the DVB interface

    There are two layers of RP filters, one specific to the network interface
    and a higher level that controls the configurations for all network
    interfaces. This function disables RP filtering on the top layer (for all
    interfaces), but then enables RP filtering individually for each interface,
    except the DVB interface. This way, in the end only the DVB interface has RP
    filtering disabled.

    Args:
        dvb_ifs : DVB network interfaces

    """
    assert(isinstance(dvb_ifs, list))

    # Check "all" rule:
    all_cfg = _read_filter("all")

    # If "all" rule is already disabled, it is only necessary to disable the
    # target interface
    if (all_cfg == "0"):
        if (not non_root):
            print("RP filter for \"all\" interfaces is already disabled")
        for dvb_if in dvb_ifs:
            _rm_filter(dvb_if)
        if (non_root):
            print()
            util.fill_print(
                "NOTE: this assumes the RP filter for \"all\" \
                interfaces is already disabled. You can check this by running:"
            )
            _read_filter("all", stdout=True)

    # If "all" rule is enabled, we will need to disable it. Also to preserve
    # RP filtering on all other interfaces, we will enable them manually.
    else:
        # Check interfaces
        ifs = os.listdir("/proc/sys/net/ipv4/conf/")

        # Enable all RP filters
        for interface in ifs:
            if (interface == "all" or interface == "lo" or
                interface in dvb_ifs):
                continue

            # Check current configuration
            current_cfg = _read_filter(interface)

            if (int(current_cfg) > 0):
                if (not non_root):
                    print("RP filter is already enabled on interface %s" %(
                        interface))
            else:
                _add_filter(interface)

        # Disable the overall RP filter
        _rm_filter("all")

        # And disable RP filtering on the DVB interface
        for dvb_if in dvb_ifs:
            _rm_filter(dvb_if)


def set_filters(dvb_ifs, prompt=True):
    """Disable reverse-path (RP) filtering for the DVB interfaces

    Args:
        dvb_ifs : list of DVB network interfaces
        prompt  : Whether to prompt user before applying a configuration

    """
    assert(isinstance(dvb_ifs, list))

    print("\n----------------------------- Reverse Path Filters " +
          "-----------------------------")

    # Check if RP filters are already configured properly
    if (os.geteuid() == 0):
        rp_filters_set = list()
        for dvb_if in dvb_ifs:
            rp_filters_set.append(_check_rp_filters(dvb_if))

        if (all(rp_filters_set)):
            print("Current RP filtering configurations are already OK")
            print("Skipping...")
            return

    util.fill_print("Blocksat traffic is one-way and thus reverse path (RP) \
    filtering must be disabled.")

    # For a non-root user, just run without asking. It is not going to run the
    # command anyway, just print it to stdout.
    non_root = os.geteuid() != 0
    if (non_root):
        util.fill_print("To configure RP filters, run blocksat-cli as root or \
        run the following commands on your own:")
    else:
        util.fill_print(
            "The automatic solution disables RP filtering on the DVB interface \
            and enables RP filtering on all other interfaces.")

    if (non_root or (not prompt) or util._ask_yes_or_no("OK to proceed?")):
        _set_filters(dvb_ifs, non_root)
    else:
        print("RP filtering configuration cancelled")


def subparser(subparsers):
    """Parser for rp command"""
    p = subparsers.add_parser('reverse-path', aliases=['rp'],
                              description="Set reverse path filters",
                              help='Set reverse path filters',
                              formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-i', '--interface', required = True,
                   help='Network interface')
    p.set_defaults(func=run)
    return p


def run(args):
    """Call function that sets reverse path filters

    Handles the reverse-path subcommand

    """
    set_filters([args.interface])


