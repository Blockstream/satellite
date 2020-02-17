"""Bitcoin .conf generator"""
import os
from argparse import ArgumentDefaultsHelpFormatter
from blocksat import config, defs, util
import textwrap
import argparse


def _udpmulticast(dev, src_addr, dst_addr=defs.fibre_dst_addr, trusted="1",
                  label=""):
    """Return the udpmulticast configuration line for bitcoin.conf"""
    return "udpmulticast=" + dev + "," + dst_addr + "," + src_addr + "," + trusted + "," + label


def subparser(subparsers):
    """Argument parser of bitcoin-conf command"""
    p = subparsers.add_parser('bitcoin-conf',
                              description="Generate Bitcoin configuration file",
                              help='Generate Bitcoin configuration file',
                              formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-d', '--datadir', default=None,
                   help='Path to the data directory where the generated '
                   'bitcoin.conf will be saved')
    p.set_defaults(func=configure)

    return subparser


def configure(args):
    """Generate bitcoin.conf configuration"""
    info = config.read_cfg_file()

    if (info is None):
        return

    util._print_header("Bitcoin Conf Generator")

    if args.datadir is None:
        home = os.path.expanduser("~")
        path = os.path.join(home, ".bitcoin")
    else:
        path = args.datadir

    conf_file = "bitcoin.conf"
    abs_path  = os.path.join(path, conf_file)

    cfg = ("debug=udpnet\n"
           "debug=udpmulticast\n"
           "udpmulticastloginterval=10\n")

    if (info['setup']['type'] == defs.sdr_setup_type):
        cfg += _udpmulticast(dev="lo",
                             src_addr="127.0.0.1",
                             label="leandvb") + "\n"
    elif (info['setup']['type'] == defs.linux_usb_setup_type):
        cfg += _udpmulticast(dev="dvb0_0",
                             src_addr=info['sat']['ip'],
                             label="tbs5927_lowspeed") + "\n"
        cfg += _udpmulticast(dev="dvb0_1",
                             src_addr=info['sat']['ip'],
                             label="tbs5927_highspeed") + "\n"
    elif (info['setup']['type'] == defs.standalone_setup_type):
        cfg += _udpmulticast(dev=info['setup']['netdev'],
                             src_addr=info['sat']['ip'],
                             label="s400") + "\n"
    else:
        raise ValueError("Unknown setup type")

    print("Save {} at {}/".format(conf_file, path))

    if (not util._ask_yes_or_no("Proceed?")):
        print("Aborted")
        return

    if not os.path.exists(path):
        os.makedirs(path)

    if os.path.exists(abs_path):
        if (not util._ask_yes_or_no("File already exists. Overwrite?")):
            print("Aborted")
            return

    with open(abs_path, "w") as file:
        file.write(cfg)

    print("Saved")

    if (info['setup']['type'] == defs.linux_usb_setup_type):
        print("\n" + textwrap.fill(
            ("NOTE: {} was configured assuming the DVB-S2 net interfaces will "
             "be named dvb0_0 and dvb0_1. You can check if this is the case "
             "after launching the system. If it isn't, please update {} "
             "accordingly.").format(conf_file, conf_file)))
    elif (info['setup']['type'] == defs.standalone_setup_type):
        print("\n" + textwrap.fill(
            ("NOTE: {} was configured assuming the S400 will be connected to "
             "interface {}. If this isn't the case anymore, please update {} "
             "accordingly.").format(
                 conf_file, info['setup']['netdev'], conf_file)))

