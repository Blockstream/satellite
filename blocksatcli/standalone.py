"""Standalone Demodulator"""
from argparse import ArgumentDefaultsHelpFormatter
from . import rp, firewall, defs, config


def subparser(subparsers):
    p = subparsers.add_parser('standalone',
                              description="Configure host to receive \
                              data from standalone DVB-S2 demodulator",
                              help='Configure host to receive from \
                              standalone DVB-S2 demodulator',
                              formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-i', '--interface',
                    default=None,
                    help='Network interface connected to the standalone \
                    demodulator')
    p.add_argument('-y', '--yes', default=False, action='store_true',
                   help="Default to answering Yes to configuration prompts")
    p.set_defaults(func=cfg_standalone)
    return p

def cfg_standalone(args):
    """Configurations for standalone DVB demodulator
    """
    # User info
    user_info = config.read_cfg_file(args.cfg_file, args.cfg_dir)

    if 'netdev' not in user_info['setup']:
        assert(args.interface is not None), \
            ("Please specify the network interface through option "
             "\"-i/--interface\"")

    interface = args.interface if (args.interface is not None) else \
                user_info['setup']['netdev']

    rp.set_filters([interface], prompt=(not args.yes))
    firewall.configure([interface], defs.src_ports, igmp=True,
                       prompt=(not args.yes))


