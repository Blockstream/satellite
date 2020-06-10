#!/usr/bin/env python3
import logging, os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from . import defs, config, util, instructions, gqrx, bitcoin, sdr, rp, \
    firewall, standalone, usb, dependencies
from os import environ
import platform


__version__ = "0.1.6"


def main():
    """Main - parse command-line arguments and call subcommands
    """
    assert(platform.system() == 'Linux'), \
        "blocksat-cli currently only supports Linux"
    sudo_user       = environ.get('SUDO_USER')
    user            = sudo_user if sudo_user is not None else ""
    home            = os.path.expanduser("~" + user)
    default_cfg_dir = os.path.join(home, ".blocksat")

    parser = ArgumentParser(prog="blocksat-cli",
                            description="Blockstream Satellite Command-Line Interface",
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Set debug mode')
    parser.add_argument('--cfg-file',
                        default="config.json",
                        help="Configuration file name")
    parser.add_argument('--cfg-dir',
                        default=default_cfg_dir,
                        help="Directory to use for configuration files")
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s {}'.format(__version__))

    subparsers = parser.add_subparsers(title='subcommands',
                                       help='Target sub-command')

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

    args = parser.parse_args()
    log_format = '%(levelname)s: %(message)s'
    if (args.debug):
        logging.basicConfig(level=logging.DEBUG, format=log_format)
        logging.debug('[Debug Mode]')
    else:
        logging.basicConfig(level=logging.INFO, format=log_format)

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
