"""Manage software dependencies"""
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from . import config, defs, util
import os, subprocess, logging
from shutil import which
from pprint import pformat
import distro
logger = logging.getLogger(__name__)


def _check_distro(supported_distros, setup_type):
    """Check if distribution is supported"""
    base_url = "https://github.com/Blockstream/satellite/blob/master/doc/"
    instructions_url = {
        defs.sdr_setup_type : "sdr.md",
        defs.linux_usb_setup_type : "tbs.md"
    }
    full_url = base_url + instructions_url[setup_type]
    if (distro.id() not in supported_distros):
        print("{} is not a supported Linux distribution for "
              "the {} setup".format(distro.name(), setup_type))
        util.fill_print("Please, refer to {} receiver setup instructions at "
                        "{}".format(setup_type, full_url))
        raise ValueError("Unsupported Linux distribution")


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
    elif (which("yum")):
        cmd = ["yum", "copr", "enable", "blockstream/satellite"]
        if (not interactive):
            cmd.append("-y")
        util.run_and_log(util.root_cmd(cmd), logger)
    else:
        raise RuntimeError("Could not find a supported package manager")


def _install_packages(apt_list, dnf_list, yum_list, interactive=True,
                      update=False):
    """Install binary packages

    Args:
        apt_list    : List of package names for installation via apt
        dnf_list    : List of package names for installation via dnf
        dnf_list    : List of package names for installation via yum
        interactive : Whether to run an interactive install (w/ user prompting)
        update      : Whether to update pre-installed packages instead


    """
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
    elif (which("yum")):
        manager = "yum"
        if (update):
            cmd = ["yum", "upgrade"]
        else:
            cmd = ["yum", "install"]
        cmd.extend(yum_list)
    else:
        raise RuntimeError("Could not find a supported package manager")

    env = None
    if (not interactive):
        cmd.append("-y")
        if (manager == "apt"):
            env = os.environ.copy()
            env["DEBIAN_FRONTEND"] = "noninteractive"

    util.run_and_log(util.root_cmd(cmd), logger, env=env)


def _install_common(interactive=True, update=False):
    """Install dependencies that are common to all setups"""
    util._print_header("Installing Common Dependencies")
    apt_pkg_list = ["software-properties-common"]
    dnf_pkg_list = ["dnf-plugins-core"]
    yum_pkg_list = ["yum-plugin-copr"]

    if distro.id() == "centos":
        dnf_pkg_list.append("epel-release")
        yum_pkg_list.append("epel-release")

    _install_packages(apt_pkg_list, dnf_pkg_list, yum_pkg_list, interactive,
                      update)
    # Enable our binary package repository
    _enable_pkg_repo(interactive)


def _install_sdr(interactive=True, update=False):
    """Install SDR dependencies"""
    util._print_header("Installing SDR Dependencies")
    apt_pkg_list = ["gqrx-sdr", "rtl-sdr", "leandvb", "tsduck"]
    dnf_pkg_list = ["gqrx", "rtl-sdr", "leandvb", "tsduck"]
    yum_pkg_list = ["rtl-sdr", "leandvb", "tsduck"]
    # NOTE: leandvb and tsduck come from our repository. Also, note gqrx is not
    # available on CentOS (hence not included on the yum list).
    _install_packages(apt_pkg_list, dnf_pkg_list, yum_pkg_list, interactive,
                      update)


def _install_usb(interactive=True, update=False):
    """Install USB receiver dependencies"""
    util._print_header("Installing USB Demodulator Dependencies")
    apt_pkg_list = ["python3", "iproute2", "iptables", "dvb-apps", "dvb-tools"]
    dnf_pkg_list = ["python3", "iproute", "iptables", "dvb-apps", "v4l-utils"]
    yum_pkg_list = ["python3", "iproute", "iptables", "dvb-apps", "v4l-utils"]
    # NOTE: the only package from our repository is dvb-apps in the specific
    # case of dnf (RPM) installation, because dvb-apps is not available on the
    # mainstream fc31/32 repository
    _install_packages(apt_pkg_list, dnf_pkg_list, yum_pkg_list, interactive,
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
                   choices=["sdr", "usb"],
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
            "sdr" : defs.sdr_setup_type,
            "usb" : defs.linux_usb_setup_type
        }
        target = target_map[args.target]
    else:
        info = config.read_cfg_file(args.cfg_file, args.cfg_dir)
        if (info is None):
            return
        target = info['setup']['type']

    # Check if demodulator setup supports automatic installation of dependencies
    if (target not in [defs.sdr_setup_type, defs.linux_usb_setup_type]):
        raise ValueError("Installation of dependencies not supported yet "
                         "for {} demodulator setup".format(
                             info['setup']['type']))

    if (os.geteuid() != 0):
        util.fill_print("Some commands require root access and will prompt "
                        "for password")

    # Interactive installation? I.e., requires user to press "y/n"
    interactive = (not args.yes)

    # Common dependencies (regardless of setup)
    _install_common(interactive=interactive, update=args.update)

    if (target == defs.sdr_setup_type):
        # The SDR packages are only available to the distributions below:
        _check_distro(["ubuntu", "fedora", "centos"],
                      defs.sdr_setup_type)
        _install_sdr(interactive=interactive, update=args.update)
    elif (target == defs.linux_usb_setup_type):
        _install_usb(interactive=interactive, update=args.update)

