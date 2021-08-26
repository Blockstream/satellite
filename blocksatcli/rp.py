"""Reverse path settings"""
import logging
import os
from argparse import ArgumentDefaultsHelpFormatter

from . import util

logger = logging.getLogger(__name__)
runner = util.ProcessRunner(logger)


def _read_filter(ifname, nodry=False):
    safe_ifname = ifname.replace(".", "/")
    cmd = ["sysctl", "net.ipv4.conf." + safe_ifname + ".rp_filter"]
    res = runner.run(cmd, capture_output=True, nodry=nodry, nocheck=True)
    if (res is None or res.stdout == b''):
        return -1  # dry run or the interface does not exist
    else:
        return int(res.stdout.decode().split()[-1])


def _write_filter(ifname, val):
    assert (val == "1" or val == "0")
    safe_ifname = ifname.replace(".", "/")
    cmd = [
        "sysctl", "-w", "net.ipv4.conf." + safe_ifname + ".rp_filter=" + val
    ]

    action = "Enabling" if val == "1" else "Disabling"
    if (not runner.dry):
        print("{} the RP filter on interface \"{}\"".format(action, ifname))
    runner.run(cmd, root=True)


def _rm_filter(ifname):
    _write_filter(ifname, "0")


def _add_filter(ifname):
    _write_filter(ifname, "1")


def _set_filters(dvb_ifs):
    """Disable reverse-path (RP) filtering for the DVB interface

    There are two layers of RP filters, one specific to the network interface
    and a higher level that controls the configurations for all network
    interfaces. This function disables RP filtering on the top layer (for all
    interfaces) but then enables RP filtering individually on all interfaces,
    except the DVB-S2 interface of interst. This way, in the end, only the
    DVB-S2 interface has RP filtering disabled.

    If the top layer RP filter (the "all" rule) is already disabled, this
    function disables only the target DVB-S2 interface. This strategy is
    especially useful when multiple DVB-S2 interfaces are attached to the
    host. If one of them has already disabled the "all" rule, this function
    disables only the incoming DVB-S2 interface and doesn't re-enable the RP
    filters of the other interfaces, otherwise it would end up reactivating the
    filter for the other DVB-S2 interface(s).

    Args:
        dvb_ifs : List of target DVB-S2 network interfaces.

    """
    assert (isinstance(dvb_ifs, list))

    # If the "all" rule is already disabled, disable only the target DVB-S2
    # interface.
    if (_read_filter("all", nodry=True) == 0):
        if (not runner.dry):
            print("RP filter for \"all\" interfaces is already disabled")

        for dvb_if in dvb_ifs:
            _rm_filter(dvb_if)

    # If the "all" rule is enabled, disable it, and manually enable the RP
    # filtering on all other interfaces.
    else:
        # Check interfaces
        ifs = os.listdir("/proc/sys/net/ipv4/conf/")

        # Enable all RP filters
        for interface in ifs:
            if (interface == "all" or interface == "lo"
                    or interface in dvb_ifs):
                continue

            # Enable the RP filter if not enabled already.
            if (_read_filter(interface, nodry=True) > 0):
                if (not runner.dry):
                    print("RP filter is already enabled on interface %s" %
                          (interface))
            else:
                _add_filter(interface)

        # Disable the overall RP filter
        _rm_filter("all")

        # And disable RP filtering on the DVB interface
        for dvb_if in dvb_ifs:
            _rm_filter(dvb_if)


def set_filters(dvb_ifs, prompt=True, dry=False):
    """Disable reverse-path (RP) filtering for the DVB interfaces

    Args:
        dvb_ifs : list of DVB network interfaces
        prompt  : Whether to prompt user before applying a configuration
        dry     : Dry run mode

    """
    assert (isinstance(dvb_ifs, list))
    runner.set_dry(dry)
    util._print_header("Reverse Path Filters")

    # Check if the RP filters are already configured properly
    rp_filters_set = list()
    rp_filters_set.append(_read_filter("all", nodry=True) == 0)
    for dvb_if in dvb_ifs:
        rp_filters_set.append(_read_filter(dvb_if, nodry=True) == 0)

    if (all(rp_filters_set)):
        print("Current RP filtering configurations are already OK")
        print("Skipping...")
        return

    util.fill_print("It will be necessary to reconfigure some reverse path \
    (RP) filtering rules applied by the Linux kernel. This is required to \
    prevent the filtering of the one-way Blockstream Satellite traffic.")

    if (runner.dry):
        util.fill_print("The following command(s) would be executed to \
        reconfigure the RP filters:")

    if (runner.dry or (not prompt) or util._ask_yes_or_no("OK to proceed?")):
        _set_filters(dvb_ifs)
    else:
        print("RP filtering configuration cancelled")


def subparser(subparsers):
    """Parser for rp command"""
    p = subparsers.add_parser('reverse-path',
                              aliases=['rp'],
                              description="Set reverse path filters",
                              help='Set reverse path filters',
                              formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-i',
                   '--interface',
                   required=True,
                   help='Network interface')
    p.add_argument('-y',
                   '--yes',
                   default=False,
                   action='store_true',
                   help="Default to answering Yes to configuration prompts")
    p.add_argument("--dry-run",
                   action='store_true',
                   default=False,
                   help="Print all commands but do not execute them")
    p.set_defaults(func=run)
    return p


def run(args):
    """Call function that sets reverse path filters

    Handles the reverse-path subcommand

    """
    set_filters([args.interface], prompt=(not args.yes), dry=args.dry_run)
