"""Bitcoin .conf generator"""
import os
from argparse import ArgumentDefaultsHelpFormatter
from . import config, defs, util
import textwrap


class Cfg:
    def __init__(self, cfg=None):
        self.cfg = {} if cfg is None else cfg

    def add_opt(self, key, val):
        """Add key-value pair to configuration dictionary"""

        # The options that appear more than once become lists on the
        # resulting dictionary.
        if (key in self.cfg):
            # If this key is not a list yet in the dictionary, make it a list
            if (not isinstance(self.cfg[key], list)):
                if (val == self.cfg[key]):
                    return  # identical value found

                new_val = list()
                new_val.append(self.cfg[key])
                new_val.append(val)
                self.cfg[key] = new_val
            else:
                if (val in self.cfg[key]):
                    return  # identical value found

                self.cfg[key].append(val)
        else:
            self.cfg[key] = val

    def load_text_cfg(self, text):
        """Load configuration from text"""
        for line in text.splitlines():
            key = line.split("=")[0]
            val = line.split("=")[1]
            self.add_opt(key, val)

    def text(self):
        """Export configuration to text version"""
        text = ""
        for k in self.cfg:
            if (isinstance(self.cfg[k], list)):
                for e in self.cfg[k]:
                    text += k + "=" + e + "\n"
            else:
                text += k + "=" + self.cfg[k] + "\n"
        return text


def _udpmulticast(dev,
                  src_addr,
                  dst_addr=defs.btc_dst_addr,
                  trusted="1",
                  label=""):
    """Return the udpmulticast configuration line for bitcoin.conf"""
    return dev + "," + dst_addr + "," + src_addr + "," + trusted + "," + label


def _gen_cfgs(info, interface):
    """Generate configurations"""
    cfg = Cfg()
    cfg.add_opt("debug", "udpnet")
    cfg.add_opt("debug", "udpmulticast")
    cfg.add_opt("udpmulticastloginterval", "600")

    if (info['setup']['type'] == defs.sdr_setup_type):
        src_addr = "127.0.0.1"
        label = "blocksat-sdr"
    elif (info['setup']['type'] == defs.linux_usb_setup_type):
        src_addr = info['sat']['ip']
        label = "blocksat-tbs"
    elif (info['setup']['type'] == defs.standalone_setup_type):
        src_addr = info['sat']['ip']
        label = "blocksat-s400"
    elif (info['setup']['type'] == defs.sat_ip_setup_type):
        src_addr = "127.0.0.1"
        label = "blocksat-sat-ip"
    else:
        raise ValueError("Unknown setup type")

    cfg.add_opt("udpmulticast",
                _udpmulticast(dev=interface, src_addr=src_addr, label=label))

    return cfg


def subparser(subparsers):
    """Argument parser of bitcoin-conf command"""
    p = subparsers.add_parser(
        'bitcoin-conf',
        aliases=['btc'],
        description="Generate Bitcoin configuration file",
        help='Generate Bitcoin configuration file',
        formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-d',
                   '--datadir',
                   default=None,
                   help='Path to the data directory where the generated '
                   'bitcoin.conf will be saved')
    p.add_argument('--stdout',
                   action='store_true',
                   default=False,
                   help='Print the generated bitcoin.conf file to the '
                   'standard output instead of saving the file')
    p.add_argument('--concat',
                   action='store_true',
                   default=False,
                   help='Concatenate configurations to pre-existing '
                   'bitcoin.conf file')
    p.set_defaults(func=configure)

    return subparser


def configure(args):
    """Generate bitcoin.conf configuration"""
    info = config.read_cfg_file(args.cfg, args.cfg_dir)

    if (info is None):
        return

    if (not args.stdout):
        util._print_header("Bitcoin Conf Generator")

    if args.datadir is None:
        home = os.path.expanduser("~")
        path = os.path.join(home, ".bitcoin")
    else:
        path = args.datadir

    conf_file = "bitcoin.conf"
    abs_path = os.path.join(path, conf_file)

    # Network interface
    ifname = config.get_net_if(info)

    # Generate configuration object
    cfg = _gen_cfgs(info, ifname)

    # Load and concatenate pre-existing configurations
    if args.concat and os.path.exists(abs_path):
        with open(abs_path, "r") as fd:
            prev_cfg_text = fd.read()
            cfg.load_text_cfg(prev_cfg_text)

    # Export configurations to text format
    cfg_text = cfg.text()

    # Print configurations to stdout and don't save them
    if (args.stdout):
        print(cfg_text)
        return

    # Proceed to saving configurations
    print("Save {} at {}/".format(conf_file, path))

    if (not util._ask_yes_or_no("Proceed?")):
        print("Aborted")
        return

    if not os.path.exists(path):
        os.makedirs(path)

    if os.path.exists(abs_path) and not args.concat:
        if (not util._ask_yes_or_no("File already exists. Overwrite?")):
            print("Aborted")
            return

    with open(abs_path, "w") as fd:
        fd.write(cfg_text)

    print("Saved")

    if (info['setup']['type'] == defs.linux_usb_setup_type):
        print()
        util.fill_print(
            "NOTE: {} was configured assuming the dvbnet interface is "
            "named {}. You can check if this is the case after launching the "
            "receiver by running:".format(conf_file, ifname))
        print("    ip link show | grep dvb\n")
        util.fill_print("If the dvb interfaces are numbered differently, "
                        "please update {} accordingly.".format(conf_file))
    elif (info['setup']['type'] == defs.standalone_setup_type):
        print("\n" + textwrap.fill(
            ("NOTE: {0} was configured assuming the Novra S400 receiver will "
             "be connected to interface {1}. If this is not the case anymore, "
             "please update {0} accordingly.").format(conf_file, ifname)))
