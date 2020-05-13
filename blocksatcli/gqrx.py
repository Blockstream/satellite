"""Generate gqrx configurations"""
import os
from argparse import ArgumentDefaultsHelpFormatter
from . import config, util
import textwrap
import argparse


def subparser(subparsers):
    p = subparsers.add_parser('gqrx-conf', aliases=['gqrx'],
                              description="Generate gqrx configurations",
                              help='Generate gqrx configurations',
                              formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-p', '--path', default=None,
                   help='Path where gqrx configuration file should be saved')

    p.set_defaults(func=configure)

    return subparser


def configure(args):
    """Configure GQRX"""
    info = config.read_cfg_file(args.cfg_file, args.cfg_dir)

    if (info is None):
        return

    util._print_header("Gqrx Conf Generator")

    if args.path is None:
        home = os.path.expanduser("~")
        path = os.path.join(home, ".config", "gqrx")
    else:
        path = args.path

    conf_file = "default.conf"
    abs_path  = os.path.join(path, conf_file)

    cfg = """
    [General]
    configversion=2

    [fft]
    averaging=80
    db_ranges_locked=true
    pandapter_min_db=-90
    waterfall_min_db=-90

    [input]
    bandwidth=1000000
    device="rtl=0"
    frequency={}
    lnb_lo={}
    sample_rate=2400000

    [receiver]
    demod=0
    """.format(
        int(info['freqs']['dl']*1e6),
        int(info['freqs']['lo']*1e6),
    )

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
        file.write(textwrap.dedent(cfg))

    print("Saved")

