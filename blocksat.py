#!/usr/bin/env python3
import logging
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from blocksat import defs, config, util, instructions, gqrx, bitcoin, sdr, rp, \
    firewall, standalone, usb


def main():
    """Main - parse command-line arguments and call subcommands
    """
    parser = ArgumentParser(prog="blocksat",
                            description="Blockstream Satellite CLI",
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Set debug mode')
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s 1.0')

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
