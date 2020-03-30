"""Standalone Demodulator"""
from argparse import ArgumentDefaultsHelpFormatter
from . import rp, firewall, defs


def subparser(subparsers):
    p = subparsers.add_parser('standalone',
                              description="Configure host to receive \
                              data from standalone DVB-S2 demodulator",
                              help='Configure host to receive from \
                              standalone DVB-S2 demodulator',
                              formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-i', '--interface', required = True,
                   help='Network interface')
    p.set_defaults(func=cfg_standalone)
    return p

def cfg_standalone(args):
    """Configurations for standalone DVB demodulator
    """
    rp.set_rp_filters([args.interface])
    firewall.configure([args.interface], defs.src_ports, igmp=True)


