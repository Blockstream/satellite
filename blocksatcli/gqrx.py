"""Generate gqrx configurations"""
import os
from argparse import ArgumentDefaultsHelpFormatter
from . import config, util
import textwrap


def subparser(subparsers):  # pragma: no cover
    p = subparsers.add_parser('gqrx-conf',
                              aliases=['gqrx'],
                              description="Generate gqrx configurations",
                              help='Generate gqrx configurations',
                              formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-p',
                   '--path',
                   default=None,
                   help='Path where gqrx configuration file should be saved')
    p.add_argument('-y',
                   '--yes',
                   action='store_true',
                   default=False,
                   help='Non-interactive mode. Answers \"yes\" automatically \
                   to configuration prompts"')

    p.set_defaults(func=configure)

    return subparser


def configure(args):
    """Configure GQRX"""
    interactive = not args.yes
    info = config.read_cfg_file(args.cfg, args.cfg_dir)

    if (info is None):
        return

    util.print_header("Gqrx Conf Generator")

    if args.path is None:
        home = os.path.expanduser("~")
        path = os.path.join(home, ".config", "gqrx")
    else:
        path = args.path

    conf_file = "default.conf"
    abs_path = os.path.join(path, conf_file)

    default_gains = r'@Variant(\0\0\0\b\0\0\0\x2\0\0\0\x6\0L\0N\0\x41\0\0' + \
        r'\0\x2\0\0\x1\x92\0\0\0\x4\0I\0\x46\0\0\0\x2\0\0\0\xcc)'

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
    gains={}
    lnb_lo={}
    sample_rate=2400000

    [receiver]
    demod=0
    """.format(
        int(info['freqs']['dl'] * 1e6),
        default_gains,
        int(info['freqs']['lo'] * 1e6),
    )

    print("Save {} at {}/".format(conf_file, path))

    if (interactive and not util.ask_yes_or_no("Proceed?")):
        print("Aborted")
        return

    if not os.path.exists(path):
        os.makedirs(path)

    if os.path.exists(abs_path):
        if (interactive
                and not util.ask_yes_or_no("File already exists. Overwrite?")):
            print("Aborted")
            return

    with open(abs_path, "w") as file:
        file.write(textwrap.dedent(cfg))

    print("Saved")
