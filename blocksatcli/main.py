#!/usr/bin/env python3
import logging, os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from . import defs, config, util, instructions, gqrx, bitcoin, sdr, rp, \
    firewall, standalone, usb


__version__ = "0.1.0"


def main():
    """Main - parse command-line arguments and call subcommands
    """
    default_cfg_dir = os.path.join(os.path.expanduser("~"), ".blocksat")
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

    cfg_parser   = config.subparser(subparsers)
    inst_parser  = instructions.subparser(subparsers)
    usb_parser   = usb.subparser(subparsers)
    stdl_parser  = standalone.subparser(subparsers)
    rp_parser    = rp.subparser(subparsers)
    fwall_parser = firewall.subparser(subparsers)
    gqrx_parser  = gqrx.subparser(subparsers)
    bit_parser   = bitcoin.subparser(subparsers)
    sdr_parser   = sdr.subparser(subparsers)

    args = parser.parse_args()
    if (args.debug):
        logging.basicConfig(level=logging.DEBUG)
        logging.debug('[Debug Mode]')
    else:
        logging.basicConfig(level=logging.INFO)

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
