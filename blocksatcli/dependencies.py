"""Manage software dependencies"""
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from . import config, defs, util
import os, subprocess, logging
from shutil import which
from pprint import pformat
logger = logging.getLogger(__name__)


def _enable_pkg_repo(interactive):
    """Enable Blockstream Satellite's binary package repository"""
    if (which("apt")):
        cmd = ["add-apt-repository", "ppa:blockstream/satellite"]
        if (not interactive):
            cmd.append("-y")
        util.run_and_log(util.root_cmd(cmd), logger)

        cmd = ["apt", "update"]
        if (not interactive):
            cmd.append("-y")
        util.run_and_log(util.root_cmd(cmd), logger)
    elif (which("dnf")):
        cmd = ["dnf", "copr", "enable", "blockstream/satellite"]
        if (not interactive):
            cmd.append("-y")
        util.run_and_log(util.root_cmd(cmd), logger)
    else:
        raise RuntimeError("Could not find a supported package manager")


def _install_packages(apt_list, dnf_list, interactive=True, update=False):
    """Install binary packages"""
    if (which("apt")):
        manager = "apt"
        cmd = ["apt-get", "install"]
        if (update):
            cmd.append("--only-upgrade")
        cmd.extend(apt_list)
    elif (which("dnf")):
        manager = "dnf"
        if (update):
            cmd = ["dnf", "upgrade"]
        else:
            cmd = ["dnf", "install"]
        cmd.extend(dnf_list)
    else:
        raise RuntimeError("Could not find a supported package manager")

    if (not interactive):
        cmd.append("-y")

    util.run_and_log(util.root_cmd(cmd), logger)


def _install_sdr(interactive=True, update=False):
    util._print_header("Installing SDR Dependencies")

    if (os.geteuid() != 0):
        util.fill_print("Some commands require root access and will prompt "
                        "for password")

    # Mainstream binary packages
    apt_pkg_list = ["software-properties-common", "gqrx-sdr", "rtl-sdr"]
    dnf_pkg_list = ["dnf-plugins-core", "gqrx", "rtl-sdr"]
    _install_packages(apt_pkg_list, dnf_pkg_list, interactive, update)

    # Enable our binary package repository and install our binary packages
    _enable_pkg_repo(interactive)
    _install_packages(["leandvb", "tsduck"], ["leandvb", "tsduck"],
                      interactive,
                      update)


def _print_help(args):
    """Re-create argparse's help menu"""
    parser     = ArgumentParser()
    subparsers = parser.add_subparsers(title='', help='')
    parser     = subparser(subparsers)
    print(parser.format_help())


def subparser(subparsers):
    """Parser for install command"""
    p = subparsers.add_parser('dependencies', aliases=['deps'],
                              description="Manage dependencies",
                              help='Manage dependencies',
                              formatter_class=ArgumentDefaultsHelpFormatter)

    p.set_defaults(func=_print_help)
    p.add_argument("--target",
                   choices=["sdr"],
                   default=None,
                   help="Target setup type for installation of dependencies")
    p.add_argument("-y", "--yes",
                   action='store_true',
                   default=False,
                   help="Non-interactive mode. Answers \"yes\" automatically \
                   to binary package installation prompts")

    subsubp = p.add_subparsers(title='subcommands',
                               help='Target sub-command')

    p1 = subsubp.add_parser('install',
                            description="Install software dependencies",
                            help='Install software dependencies')
    p1.set_defaults(func=run, update=False)

    p1 = subsubp.add_parser('update',
                            description="Update software dependencies",
                            help='Update software dependencies')
    p1.set_defaults(func=run, update=True)

    return p


def run(args):
    """Run installations"""
    if (args.target is not None):
        target_map = {
            "sdr" : defs.sdr_setup_type
        }
        target = target_map[args.target]
    else:
        info = config.read_cfg_file(args.cfg_file, args.cfg_dir)
        if (info is None):
            return
        target = info['setup']['type']

    if (target == defs.sdr_setup_type):
        _install_sdr(interactive=(not args.yes), update=args.update)
    else:
        print("Installation of dependencies no supported yet "
              "for {} demodulator setup".format(info['setup']['type']))


