#!/usr/bin/env python3
"""
Set reverse-path filters
"""
import argparse
from launch import set_rp_filters


def main():
    parser = argparse.ArgumentParser("Set reverse path filters")
    parser.add_argument('-i', '--interface',
                        default="dvb0_0",
                        help='DVB network interface ' +
                        '(default: dvb0_0)')
    args      = parser.parse_args()
    # Set RP filters
    set_rp_filters(args.interface)

if __name__ == '__main__':
    main()
