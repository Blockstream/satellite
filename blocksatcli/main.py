#!/usr/bin/env python3

__version__ = "0.4.0"

import logging
import os
import platform
import time
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from . import config, util, instructions, gqrx, bitcoin, sdr, rp, \
    firewall, standalone, usb, satip, dependencies, update
from .api import api


def main():
    """Main - parse command-line arguments and call subcommands
    """
    default_cfg_dir = os.path.join(util.get_home_dir(), ".blocksat")

    parser = ArgumentParser(
        prog="blocksat-cli",
        description="Blockstream Satellite Command-Line Interface",
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d',
                        '--debug',
                        action='store_true',
                        help='Set debug mode')
    parser.add_argument('--cfg',
                        default="config",
                        help="Target configuration set")
    parser.add_argument('--cfg-dir',
                        default=default_cfg_dir,
                        help="Directory to use for configuration files")
    parser.add_argument('--utc',
                        action='store_true',
                        help="Print log timestamps in UTC")
    parser.add_argument('-v',
                        '--version',
                        action='version',
                        version='%(prog)s {}'.format(__version__))

    subparsers = parser.add_subparsers(title='subcommands',
                                       help='Target sub-command',
                                       dest='subcommand')

    config.subparser(subparsers)
    instructions.subparser(subparsers)
    dependencies.subparser(subparsers)
    usb.subparser(subparsers)
    standalone.subparser(subparsers)
    rp.subparser(subparsers)
    firewall.subparser(subparsers)
    gqrx.subparser(subparsers)
    bitcoin.subparser(subparsers)
    sdr.subparser(subparsers)
    api.subparser(subparsers)
    satip.subparser(subparsers)

    args = parser.parse_args()

    # Filter commands that are Linux-only
    if (args.subcommand not in ["cfg", "instructions", "api", "btc"]):
        assert(platform.system() == 'Linux'), \
            "Command {} is currently Linux-only".format(args.subcommand)

    # Logging
    logging_fmt = '%(asctime)s %(levelname)-8s %(name)s %(message)s' if \
                  args.debug else '%(asctime)s %(levelname)-8s %(message)s'
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format=logging_fmt,
                        datefmt='%Y-%m-%d %H:%M:%S')
    if (args.utc):
        logging.Formatter.converter = time.gmtime
    logging.debug('[Debug Mode]')

    # Check CLI updates
    update.check_cli_updates(args, __version__)

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
