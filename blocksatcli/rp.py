"""Reverse path settings"""
from argparse import ArgumentDefaultsHelpFormatter
import subprocess, os
from . import util


def _check_rp_filters(dvb_if):
    """Check if reverse-path (RP) filters are configured on the interface

    Args:
        dvb_if : DVB network interface

    Return:
        True when configuration is already OK.

    """

    # Sysctl-ready interface name: replace a dot (for VLAN interface) with slash
    sysctl_dvb_if = dvb_if.replace(".", "/")

    # Check current configuration of DVB interface and "all" rule:
    dvb_cfg =  subprocess.check_output([
        "sysctl",
        "net.ipv4.conf." + sysctl_dvb_if + ".rp_filter"
    ]).split()[-1].decode()
    all_cfg =  subprocess.check_output([
        "sysctl",
        "net.ipv4.conf.all.rp_filter"
    ]).split()[-1].decode()

    return (dvb_cfg == "0" and all_cfg == "0")


def _set_rp_filters(dvb_if):
    """Disable reverse-path (RP) filtering for the DVB interface

    There are two layers of RP filters, one specific to the network interface
    and a higher level that controls the configurations for all network
    interfaces. This function disables RP filtering on the top layer (for all
    interfaces), but then enables RP filtering individually for each interface,
    except the DVB interface. This way, in the end only the DVB interface has RP
    filtering disabled.

    Args:
        dvb_if : DVB network interface

    """

    # Sysctl-ready interface name: replace a dot (for VLAN interface) with slash
    sysctl_dvb_if = dvb_if.replace(".", "/")

    # Check "all" rule:
    all_cfg =  subprocess.check_output([
        "sysctl",
        "net.ipv4.conf.all.rp_filter"
    ]).split()[-1].decode()


    # If "all" rule is already disabled, it is only necessary to disable the
    # target interface
    if (all_cfg == "0"):
        print("RP filter for \"all\" interfaces is already disabled")
        print("Disabling RP filter on interface %s" %(dvb_if))
        subprocess.check_output([
            "sysctl",
            "-w",
            "net.ipv4.conf." + sysctl_dvb_if + ".rp_filter=0"
        ])
    # If "all" rule is enabled, we will need to disable it. Also to preserve
    # RP filtering on all other interfaces, we will enable them manually.
    else:
        # Check interfaces
        ifs = os.listdir("/proc/sys/net/ipv4/conf/")

        # Enable all RP filters
        for interface in ifs:
            if (interface == "all" or interface == dvb_if):
                continue

            # Again, /proc/sys uses dot on VLANs normally, but sysctl does
            # not. Instead, it substitutes with slash. Replace here before using
            sysctl_interface = interface.replace(".", "/")

            # Check current configuration
            current_cfg =  subprocess.check_output([
                "sysctl",
                "net.ipv4.conf." + sysctl_interface + ".rp_filter"
            ]).split()[-1].decode()

            if (int(current_cfg) > 0):
                print("RP filter is already enabled on interface %s" %(
                    interface))
            else:
                print("Enabling RP filter on interface %s" %(interface))
                subprocess.check_output([
                    "sysctl",
                    "-w",
                    "net.ipv4.conf." + sysctl_interface + ".rp_filter=1"
                ])

        # Disable the overall RP filter
        print("Disabling RP filter on \"all\" rule")
        subprocess.check_output([
            "sysctl",
            "-w",
            "net.ipv4.conf.all.rp_filter=0"
        ])

        # And disable RP filtering on the DVB interface
        print("Disabling RP filter on interface %s" %(dvb_if))
        subprocess.check_output([
            "sysctl",
            "-w",
            "net.ipv4.conf." + sysctl_dvb_if + ".rp_filter=0"
        ])


def set_rp_filters(dvb_ifs):
    """Disable reverse-path (RP) filtering for the DVB interfaces

    Args:
        dvb_ifs : list of DVB network interfaces

    """
    assert(isinstance(dvb_ifs, list))

    print("\n----------------------------- Reverse Path Filters " +
          "-----------------------------")

    # Check if RP filters are already configured properly
    rp_filters_set = list()
    for dvb_if in dvb_ifs:
        rp_filters_set.append(_check_rp_filters(dvb_if))

    if (all(rp_filters_set)):
        print("Current RP filtering configurations are already OK")
        print("Skipping...")
        return

    print("Blocksat traffic is one-way and thus reverse path (RP) filtering " +
          "must be\ndisabled. The automatic solution disables RP filtering " +
          "on the DVB interface and\nenables RP filtering on all other " +
          "interfaces.")

    if (util._ask_yes_or_no("OK to proceed?")):
        for dvb_if in dvb_ifs:
            _set_rp_filters(dvb_if)
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
    set_rp_filters([args.interface])


