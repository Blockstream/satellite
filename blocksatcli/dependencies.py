"""Manage software dependencies"""
import glob
import logging
import os
import platform
import subprocess
import sys
import tempfile
import textwrap
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from distutils.version import LooseVersion
from shutil import which

import distro

from . import config, defs, util

logger = logging.getLogger(__name__)
runner = util.ProcessRunner(logger)

target_map = {
    "sdr": defs.sdr_setup_type,
    "usb": defs.linux_usb_setup_type,
    "standalone": defs.standalone_setup_type,
    "sat-ip": defs.sat_ip_setup_type
}
supported_distros = ["ubuntu", "debian", "raspbian", "fedora", "centos"]


def _check_distro(setup_type):
    """Check if distribution is supported"""
    if (distro.id() in supported_distros):
        return

    base_url = defs.user_guide_url + "doc/"
    instructions_url = {
        defs.sdr_setup_type: "sdr.md",
        defs.linux_usb_setup_type: "tbs.md",
        defs.standalone_setup_type: "s400.md",
        defs.sat_ip_setup_type: "sat-ip.md"
    }
    full_url = base_url + instructions_url[setup_type]
    logger.error("{} is not a supported Linux distribution".format(
        distro.name()))
    logger.info(
        textwrap.fill("Please, refer to the {} receiver setup "
                      "instructions at {}".format(setup_type, full_url)))
    raise ValueError("Unsupported Linux distribution")


def _get_apt_repo(distro_id):
    """Find the APT package repository for the given distro"""
    if distro_id == "ubuntu":
        apt_repo = "ppa:blockstream/satellite"
    elif distro_id in ["debian", "raspbian"]:
        apt_repo = ("https://aptly.blockstream.com/"
                    "satellite/{}/").format(distro_id)
    else:
        raise ValueError("Unsupported distribution {}".format(distro_id))
    return apt_repo


def _check_pkg_repo(distro_id):
    """Check if Blockstream Satellite's binary package repository is enabled

    Args:
        distro_id: Linux distribution ID

    Returns:
        (bool) True if the repository is already enabled

    """
    found = False
    if (which("apt")):
        apt_repo = _get_apt_repo(distro_id)
        grep_str = apt_repo.replace("ppa:", "")
        apt_sources = glob.glob("/etc/apt/sources.list.d/*")
        apt_sources.append("/etc/apt/sources.list")
        cmd = ["grep", grep_str]
        cmd.extend(apt_sources)
        res = runner.run(cmd, stdout=subprocess.DEVNULL, nocheck=True)
        found = (res.returncode == 0)
    elif (which("dnf")):
        res = runner.run(["dnf", "copr", "list", "--enabled"],
                         root=True,
                         capture_output=True)
        pkgs = res.stdout.decode().splitlines()
        found = ("copr.fedorainfracloud.org/blockstream/satellite" in pkgs)
    elif (which("yum")):
        yum_sources = glob.glob("/etc/yum.repos.d/*")
        cmd = ["grep", "blockstream/satellite"]
        cmd.extend(yum_sources)
        res = runner.run(cmd, stdout=subprocess.DEVNULL, nocheck=True)
        found = (res.returncode == 0)
    else:
        raise RuntimeError("Could not find a supported package manager")

    if (found):
        logger.debug("blockstream/satellite repository already enabled")

    return found


def _enable_pkg_repo(distro_id, interactive):
    """Enable Blockstream Satellite's binary package repository

    Args:
        distro_id: Linux distribution ID
        interactive: Interactive mode

    """
    cmds = list()
    if (which("apt")):
        apt_repo = _get_apt_repo(distro_id)

        # On debian, add the apt repository through "add-apt-repository". On
        # raspbian, where "add-apt-repository" does not work, manually add a
        # file into /etc/apt/sources.list.d/.
        if distro_id == "raspbian":
            release_codename = distro.codename()
            apt_list_filename = "blockstream-satellite-{}-{}.list".format(
                distro_id, release_codename)
            apt_list_file = os.path.join("/etc/apt/sources.list.d/",
                                         apt_list_filename)
            apt_component = "main"
            apt_file_content = "deb {0} {1} {2}\n# deb-src {0} {1} {2}".format(
                apt_repo, release_codename, apt_component)
            # In execution mode, create a temporary file and move it to
            # /etc/apt/sources.list.d/. With that, only the move command needs
            # root permissions, whereas the temporary file does not. In dry-run
            # mode, print an equivalent echo command.
            if (runner.dry):
                cmd = [
                    "echo", "-e",
                    repr(apt_file_content), ">>", apt_list_file
                ]
            else:
                tmp_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
                with tmp_file as fd:
                    fd.write(apt_file_content)
                cmd = ["mv", tmp_file.name, apt_list_file]
        else:
            cmd = ["add-apt-repository", apt_repo]
            if (not interactive):
                cmd.append("-y")

        cmds.append(cmd)

        if distro_id in ["debian", "raspbian"]:
            cmd = [
                "apt-key", "adv", "--keyserver", "keyserver.ubuntu.com",
                "--recv-keys", defs.blocksat_pubkey
            ]
            cmds.append(cmd)

        cmd = ["apt", "update"]
        if (not interactive):
            cmd.append("-y")
        cmds.append(cmd)
    elif (which("dnf")):
        cmd = ["dnf", "copr", "enable", "blockstream/satellite"]
        if (not interactive):
            cmd.append("-y")
        cmds.append(cmd)
    elif (which("yum")):
        cmd = ["yum", "copr", "enable", "blockstream/satellite"]
        if (not interactive):
            cmd.append("-y")
        cmds.append(cmd)
    else:
        raise RuntimeError("Could not find a supported package manager")

    for cmd in cmds:
        runner.run(cmd, root=True)


def _update_pkg_repo(interactive):
    """Update APT's package index

    NOTE: this function updates APT only. On dnf/yum, there is no need to run
    an update manually. The tool (dnf/yum) updates the package index
    automatically when an install/upgrade command is called.

    """

    if (not which("apt")):
        return

    cmd = ["apt", "update"]
    if (not interactive):
        cmd.append("-y")

    runner.run(cmd, root=True)


def _install_packages(apt_list,
                      dnf_list,
                      yum_list,
                      interactive=True,
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

    runner.run(cmd, root=True, env=env)


def _install_common(interactive=True, update=False, btc=False):
    """Install dependencies that are common to all setups"""
    util._print_header("Installing Common Dependencies")
    apt_pkg_list = ["software-properties-common"]
    dnf_pkg_list = ["dnf-plugins-core"]
    yum_pkg_list = ["yum-plugin-copr"]

    # "gnupg" is installed as a dependency of "software-properties-common" on
    # Ubuntu. In contrast, it is not a dependency on Debian. Hence, add it
    # explicitly to the list. Add also "dirmngr", which may not be
    # automatically installed with gnupg (it is only automatically installed
    # from buster onwards). Lastly, add "apt-transport-https" to fetch debian
    # and raspbian packages from Aptly using HTTPS.
    distro_id = distro.id()
    if distro_id in ["debian", "raspbian"]:
        apt_pkg_list.extend(["gnupg", "dirmngr", "apt-transport-https"])

    if distro_id == "centos":
        dnf_pkg_list.append("epel-release")
        yum_pkg_list.append("epel-release")

    _install_packages(apt_pkg_list, dnf_pkg_list, yum_pkg_list, interactive,
                      update)

    # Enable our binary package repository
    if runner.dry or (not _check_pkg_repo(distro_id)):
        _enable_pkg_repo(distro_id, interactive)

    # Install bitcoin-satellite
    if (btc):
        apt_pkg_list = [
            "bitcoin-satellite", "bitcoin-satellite-qt", "bitcoin-satellite-tx"
        ]
        dnf_pkg_list = ["bitcoin-satellite", "bitcoin-satellite-qt"]
        yum_pkg_list = ["bitcoin-satellite", "bitcoin-satellite-qt"]

        if (which("dnf")):
            # dnf matches partial package names, and so it seems that when
            # bitcoin-satellite and bitcoin-satellite-qt are installed in one
            # go, only the latter gets installed. The former is matched to
            # bitcoin-satellite-qt and assumed as installed. Hence, as a
            # workaround, install the two packages separately.
            for pkg in dnf_pkg_list:
                _install_packages(apt_pkg_list, [pkg], [pkg], interactive,
                                  update)
        else:
            _install_packages(apt_pkg_list, [], yum_pkg_list, interactive,
                              update)


def _install_specific(target, interactive=True, update=False):
    """Install setup-specific dependencies"""
    key = next(key for key, val in target_map.items() if val == target)
    pkg_map = {
        'sdr': {
            'apt': ["gqrx-sdr", "rtl-sdr", "leandvb", "tsduck"],
            'dnf': ["gqrx", "rtl-sdr", "leandvb", "tsduck"],
            'yum': ["rtl-sdr", "leandvb", "tsduck"]
        },
        'usb': {
            'apt': ["iproute2", "iptables", "dvb-apps", "dvb-tools"],
            'dnf': ["iproute", "iptables", "dvb-apps", "v4l-utils"],
            'yum': ["iproute", "iptables", "dvb-apps", "v4l-utils"]
        },
        'standalone': {
            'apt': ["iproute2", "iptables"],
            'dnf': ["iproute", "iptables"],
            'yum': ["iproute", "iptables"]
        },
        'sat-ip': {
            'apt': ["iproute2", "tsduck"],
            'dnf': ["iproute", "tsduck"],
            'yum': ["iproute", "tsduck"]
        }
    }
    # NOTE:
    # - leandvb and tsduck come from our repository. Also, note gqrx is not
    #   available on CentOS (hence not included on the yum list).
    # - In the USB setup, the only package from our repository is dvb-apps in
    #   the specific case of dnf (RPM) installation, given that dvb-apps is not
    #   available on the latest mainstream fedora repositories.

    util._print_header("Installing {} Receiver Dependencies".format(target))
    _install_packages(pkg_map[key]['apt'], pkg_map[key]['dnf'],
                      pkg_map[key]['yum'], interactive, update)


def _print_help(args):
    """Re-create argparse's help menu"""
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(title='', help='')
    parser = subparser(subparsers)
    print(parser.format_help())


def subparser(subparsers):
    """Parser for install command"""
    p = subparsers.add_parser('dependencies',
                              aliases=['deps'],
                              description="Manage dependencies",
                              help='Manage dependencies',
                              formatter_class=ArgumentDefaultsHelpFormatter)

    p.set_defaults(func=_print_help)
    p.add_argument("-y",
                   "--yes",
                   action='store_true',
                   default=False,
                   help="Non-interactive mode. Answers \"yes\" automatically \
                   to binary package installation prompts")
    p.add_argument("--dry-run",
                   action='store_true',
                   default=False,
                   help="Print all commands but do not execute them")

    subsubp = p.add_subparsers(title='subcommands', help='Target sub-command')

    p1 = subsubp.add_parser('install',
                            description="Install software dependencies",
                            help='Install software dependencies')
    p1.add_argument("--target",
                    choices=list(target_map.keys()),
                    default=None,
                    help="Target setup type for installation of dependencies")
    p1.add_argument("--btc",
                    action='store_true',
                    default=False,
                    help="Install bitcoin-satellite")
    p1.set_defaults(func=run, update=False)

    p2 = subsubp.add_parser('update',
                            aliases=['upgrade'],
                            description="Update software dependencies",
                            help='Update software dependencies')
    p2.add_argument("--target",
                    choices=list(target_map.keys()),
                    default=None,
                    help="Target setup type for the update of dependencies")
    p2.add_argument("--btc",
                    action='store_true',
                    default=False,
                    help="Update bitcoin-satellite")
    p2.set_defaults(func=run, update=True)

    p3 = subsubp.add_parser('tbs-drivers',
                            description="Install TBS USB receiver drivers",
                            help='Install TBS USB receiver drivers')
    p3.set_defaults(func=drivers)

    return p


def run(args):
    """Run installations"""

    # Interactive installation? I.e., requires user to press "y/n"
    interactive = (not args.yes)

    # Configure the subprocess runner
    runner.set_dry(args.dry_run)

    if (args.target is not None):
        target = target_map[args.target]
    else:
        info = config.read_cfg_file(args.cfg, args.cfg_dir)
        if (info is None):
            return
        target = info['setup']['type']

    _check_distro(target)

    if (os.geteuid() != 0 and not args.dry_run):
        util.fill_print("Some commands require root access and may prompt "
                        "for a password")

    if (args.dry_run):
        util._print_header("Dry Run Mode")

    # Update package index
    _update_pkg_repo(interactive)

    # Common dependencies (regardless of setup)
    _install_common(interactive=interactive, update=args.update, btc=args.btc)

    # Install setup-specific dependencies
    _install_specific(target, interactive=interactive, update=args.update)


def drivers(args):
    # Interactive installation? I.e., requires user to press "y/n"
    interactive = (not args.yes)

    # Configure the subprocess runner
    runner.set_dry(args.dry_run)

    if (os.geteuid() != 0 and not args.dry_run):
        util.fill_print("Some commands require root access and may prompt "
                        "for a password")

    if (args.dry_run):
        util._print_header("Dry Run Mode")

    # Install pre-requisites
    linux_release = platform.release()
    linux_headers = "linux-headers-" + linux_release
    kernel_devel = "kernel-devel-" + linux_release
    kernel_headers = "kernel-headers-" + linux_release
    apt_pkg_list = [
        "make", "gcc", "git", "patch", "patchutils",
        "libproc-processtable-perl", linux_headers
    ]
    dnf_pkg_list = [
        "make", "gcc", "git", "patch", "patchutils", "perl-Proc-ProcessTable",
        "perl-Digest-SHA", "perl-File-Copy-Recursive", kernel_devel,
        kernel_headers
    ]
    yum_pkg_list = dnf_pkg_list

    # On dnf, not always the kernel-devel/headers package will be available for
    # the same version as the current kernel. Check:
    dnf_update_required = False
    if (which("dnf")):
        res_d = runner.run(["dnf", "list", kernel_devel],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           nocheck=True)
        res_h = runner.run(["dnf", "list", kernel_headers],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           nocheck=True)
        if (not args.dry_run):
            kernel_devel_unavailable = (res_d.returncode != 0)
            kernel_headers_unavailable = (res_h.returncode != 0)
            dnf_update_required = kernel_devel_unavailable or \
                kernel_headers_unavailable
            if (kernel_devel_unavailable):
                print("Could not find package {}".format(kernel_devel))
            if (kernel_headers_unavailable):
                print("Could not find package {}".format(kernel_headers))

    # If the target kernel-devel/kernel-headers versions are not available for
    # the current release, suggest to run dnf update first. If no update is
    # available, and kernel-headers is the one that has a version mismatch (it
    # typically is), try with the version that is available.
    if (dnf_update_required):
        res = runner.run(["dnf", "list", "--upgrades", "kernel"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         nocheck=True)
        kernel_update_available = (res.returncode == 0)
        if (kernel_update_available):
            print("Kernel update required")
            if (util._ask_yes_or_no("OK to run \"dnf update\"?")):
                cmd = ["dnf", "update"]
                if (not interactive):
                    cmd.append("-y")
                runner.run(cmd, root=True)
                print("Please reboot to load the new kernel and try the " +
                      "command below again:")
                print("\n  blocksat-cli deps tbs-drivers\n")
                sys.exit(1)
                return

        # Fall back to the default kernel-headers package
        if kernel_headers_unavailable:
            print("Trying with the default kernel-headers package")
            dnf_pkg_list.remove(kernel_headers)
            dnf_pkg_list.append("kernel-headers")
        else:
            # Break if kernel-devel is missing for the current version and
            # there is no upgrade available.
            logger.error("Could not find an available kernel update")
            sys.exit(1)
            return

    _update_pkg_repo(interactive)
    _install_packages(apt_pkg_list,
                      dnf_pkg_list,
                      yum_pkg_list,
                      interactive=interactive,
                      update=False)

    # Clone the driver repositories
    driver_src_dir = os.path.join(args.cfg_dir, "src", "tbsdriver")
    media_build_dir = os.path.join(driver_src_dir, "media_build")
    media_dir = os.path.join(driver_src_dir, "media")

    if not os.path.exists(driver_src_dir):
        os.makedirs(driver_src_dir)

    if os.path.exists(media_build_dir):
        runner.run(["git", "pull", "origin", "master"], cwd=media_build_dir)
    else:
        runner.run(
            ["git", "clone", "https://github.com/tbsdtv/media_build.git"],
            cwd=driver_src_dir)

    if os.path.exists(media_dir):
        runner.run(["git", "pull", "origin", "latest"], cwd=media_dir)
    else:
        runner.run([
            "git", "clone", "--depth=1",
            "https://github.com/tbsdtv/linux_media.git", "-b", "latest",
            "./media"
        ],
                   cwd=driver_src_dir)

    # Build the media drivers
    nproc = int(subprocess.check_output(["nproc"]).decode().rstrip())
    nproc_arg = "-j" + str(nproc)

    runner.run(["make", "cleanall"], cwd=media_build_dir)
    runner.run(["make", "dir", "DIR=../media"], cwd=media_build_dir)
    runner.run(["make", "allyesconfig"], cwd=media_build_dir)

    # FIXME: Temporary workaround for error "modpost: "__devm_regmap_init_sccb"
    # ov9650.ko undefined!": disable ov9650 from the build. The problem was
    # observed on kernel versions 5.3.7 and 5.7.7. Apply the workaround for any
    # version < 5.8.
    if (distro.id() == "fedora"
            and LooseVersion(linux_release) < LooseVersion('5.8')):
        runner.run([
            "sed", "-i", "s/CONFIG_VIDEO_OV9650=m/CONFIG_VIDEO_OV9650=n/g",
            "v4l/.config"
        ],
                   cwd=media_build_dir)

    runner.run(["make", nproc_arg], cwd=media_build_dir)

    # Delete the previous Media Tree installation
    media_lib_path = "/lib/modules/" + linux_release + \
                     "/kernel/drivers/media/"
    runner.run(["rm", "-rf", media_lib_path], root=True, cwd=media_build_dir)

    # Install the new Media Tree
    runner.run(["make", "install"], root=True, cwd=media_build_dir)

    # Download the firmware
    tbs_linux_url = "https://www.tbsdtv.com/download/document/linux/"
    fw_tarball = "tbs-tuner-firmwares_v1.0.tar.bz2"
    fw_url = tbs_linux_url + fw_tarball
    util.download_file(fw_url, driver_src_dir, args.dry_run, logger=logger)

    # Install the firmware
    runner.run(["tar", "jxvf", fw_tarball, "-C", "/lib/firmware/"],
               root=True,
               cwd=driver_src_dir)

    if (not args.dry_run):
        print("Installation completed successfully. Please reboot now.")


def check_apps(apps):
    """Check if required apps are installed"""
    for app in apps:
        if (not which(app)):
            logging.error("Couldn't find {}. Is it installed?".format(app))
            print("\nTo install software dependencies, run:")
            print("""
            blocksat-cli deps install
            """)
            return False
    # All apps are installed
    return True
