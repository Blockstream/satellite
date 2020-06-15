"""Manage software dependencies"""
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from . import config, defs, util
import os, subprocess, logging
from shutil import which
from pprint import pformat
logger = logging.getLogger(__name__)


def _enable_pkg_repo():
    """Enable Blockstream Satellite's binary package repository"""
    if (which("apt")):
        util.run_and_log(util.root_cmd(
            ["add-apt-repository", "ppa:blockstream/satellite"]), logger)
        util.run_and_log(util.root_cmd(
            ["apt", "update"]), logger)
    elif (which("dnf")):
        util.run_and_log(util.root_cmd(
            ["dnf", "copr", "enable", "blockstream/satellite"]), logger)
    else:
        raise RuntimeError("Could not find a supported package manager")


def _install_packages(apt_list, dnf_list, interactive):
    """Install binary packages"""
    util._print_sub_header("Binary Dependencies")
    if (which("apt")):
        manager = "apt"
        cmd = ["apt-get", "install"]
        cmd.extend(apt_list)
    elif (which("dnf")):
        manager = "dnf"
        cmd = ["dnf", "install"]
        cmd.extend(dnf_list)
    else:
        raise RuntimeError("Could not find a supported package manager")

    if (not interactive):
        cmd.append("-y")

    util.run_and_log(util.root_cmd(cmd), logger)


def _install_sdr(srcdir, usrdir, interactive=True, update=False):
    util._print_header("Installing SDR Dependencies")

    bindir = os.path.join(usrdir, "bin")

    if (os.geteuid() != 0):
        util.fill_print("Some commands require root access and will prompt "
                        "for password")

    # Mainstream binary packages
    apt_pkg_list = ["software-properties-common", "git", "make", "g++",
                    "libx11-dev", "gqrx-sdr", "rtl-sdr"]
    dnf_pkg_list = ["dnf-plugins-core", "git", "make", "g++", "libX11-devel",
                    "gqrx", "rtl-sdr"]
    _install_packages(apt_pkg_list, dnf_pkg_list, interactive)

    # Enable our binary package repository and install our binary packages
    _enable_pkg_repo()
    _install_packages(["tsduck"], ["tsduck"], interactive)

    # leansdr build
    util._print_sub_header("leansdr")
    leansdr_dir     = os.path.join(srcdir, "leansdr")
    leansdr_app_dir = os.path.join(leansdr_dir, "src", "apps")

    is_update = update
    if (not is_update) and os.path.exists(leansdr_dir):
        is_update = True
        print("leansdr build directory already exists. Checking for updates...")
    elif is_update and (not os.path.exists(leansdr_dir)):
        is_update = False
        print("leansdr build directory does no exist. Installing...")

    if (is_update):
        util.run_and_log(["git", "pull", "origin", "master"],
                         logger, cwd=leansdr_dir)
        util.run_and_log(["git", "submodule", "update"],
                         logger, cwd=leansdr_dir)
    else:
        util.run_and_log(["git", "clone", "--recursive",
                          "https://github.com/Blockstream/leansdr.git"],
                         logger, cwd=srcdir)

    nproc = int(subprocess.check_output(["nproc"]).decode().rstrip())
    nproc_arg = "-j" + str(nproc)

    util.run_and_log(["make", nproc_arg], logger, cwd=leansdr_app_dir)
    util.run_and_log(["install", "leandvb", bindir],
                     logger, cwd=leansdr_app_dir)

    # LDPC
    util._print_sub_header("LDPC Tool")
    ldpc_dir = os.path.join(leansdr_dir, "LDPC")
    util.run_and_log(["make", nproc_arg, "CXX=g++", "ldpc_tool"], logger,
                     cwd=ldpc_dir)
    util.run_and_log(["install", "ldpc_tool", bindir],
                     logger, cwd=ldpc_dir)


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

    srcdir = os.path.join(args.cfg_dir, "src")
    usrdir = os.path.join(args.cfg_dir, "usr")
    bindir = os.path.join(usrdir, "bin")

    if not os.path.exists(srcdir):
        os.makedirs(srcdir)

    if not os.path.exists(usrdir):
        os.makedirs(usrdir)

    if not os.path.exists(bindir):
        os.makedirs(bindir)

    if (target == defs.sdr_setup_type):
        _install_sdr(srcdir, usrdir, interactive=(not args.yes),
                     update=args.update)
    else:
        print("Installation of dependencies no supported yet "
              "for {} demodulator setup".format(info['setup']['type']))


