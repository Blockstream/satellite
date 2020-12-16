"""Manage software dependencies"""
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from . import config, defs, util
import sys, os, subprocess, logging, glob, json
from shutil import which
from pprint import pformat
import platform, distro, requests
from distutils.version import LooseVersion
logger = logging.getLogger(__name__)


def _download_file(url, destdir, dry_run):
    filename   = url.split('/')[-1]
    local_path = os.path.join(destdir, url.split('/')[-1])

    if (dry_run):
        print("Download: {}".format(url))
        print("Save at: {}".format(destdir))
        return

    logger.debug("Download {} and save at {}".format(filename, destdir))
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk:
                f.write(chunk)
    return local_path


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


def _check_pkg_repo():
    """Check if Blockstream Satellite's binary package repository is enabled

    Returns:
        (bool) True if the repository is already enabled

    """
    found = False
    if (which("apt")):
        apt_sources = glob.glob("/etc/apt/sources.list.d/*")
        apt_sources.append("/etc/apt/sources.list")
        cmd = ["grep", "blockstream/satellite"]
        cmd.extend(apt_sources)
        res = util.run_and_log(cmd, stdout=subprocess.DEVNULL, nocheck=True,
                               logger=logger)
        found = (res.returncode == 0)
    elif (which("dnf")):
        pkgs  = util.run_and_log(
            util.root_cmd(["dnf", "copr", "list", "--enabled"]),
            logger=logger,
            output=True
        )
        found =  ("copr.fedorainfracloud.org/blockstream/satellite" in pkgs)
    elif (which("yum")):
        yum_sources = glob.glob("/etc/yum.repos.d/*")
        cmd = ["grep", "blockstream/satellite"]
        cmd.extend(yum_sources)
        res = util.run_and_log(cmd, stdout=subprocess.DEVNULL, nocheck=True,
                               logger=logger)
        found = (res.returncode == 0)
    else:
        raise RuntimeError("Could not find a supported package manager")

    if (found):
        logger.debug("blockstream/satellite repository already enabled")

    return found


def _enable_pkg_repo(interactive, dry):
    """Enable Blockstream Satellite's binary package repository"""
    cmds = list()
    if (which("apt")):
        cmd = ["add-apt-repository", "ppa:blockstream/satellite"]
        if (not interactive):
            cmd.append("-y")
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
        if (dry):
            print(" ".join(util.root_cmd(cmd)))
        else:
            util.run_and_log(util.root_cmd(cmd), logger=logger)


def _update_pkg_repo(interactive, dry):
    """Update APT's package index

    NOTE: this function updates APT only. On dnf/yum, there is no need to run an
    update manually. The tool (dnf/yum) updates the package index automatically
    when an install/upgrade command is called.

    """

    if (not which("apt")):
        return

    cmd = ["apt", "update"]
    if (not interactive):
        cmd.append("-y")

    if (dry):
        print(" ".join(util.root_cmd(cmd)))
    else:
        util.run_and_log(util.root_cmd(cmd), logger=logger)


def _install_packages(apt_list, dnf_list, yum_list, interactive=True,
                      update=False, dry=False):
    """Install binary packages

    Args:
        apt_list    : List of package names for installation via apt
        dnf_list    : List of package names for installation via dnf
        dnf_list    : List of package names for installation via yum
        interactive : Whether to run an interactive install (w/ user prompting)
        update      : Whether to update pre-installed packages instead
        dry         : Print commands instead of executing them


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

    if (dry):
        print(" ".join(util.root_cmd(cmd)))
    else:
        util.run_and_log(util.root_cmd(cmd), logger=logger, env=env)


def _install_common(interactive=True, update=False, dry=False, btc=False):
    """Install dependencies that are common to all setups"""
    util._print_header("Installing Common Dependencies")
    apt_pkg_list = ["software-properties-common"]
    dnf_pkg_list = ["dnf-plugins-core"]
    yum_pkg_list = ["yum-plugin-copr"]

    if distro.id() == "centos":
        dnf_pkg_list.append("epel-release")
        yum_pkg_list.append("epel-release")

    _install_packages(apt_pkg_list, dnf_pkg_list, yum_pkg_list, interactive,
                      update, dry)

    # Enable our binary package repository
    if dry or (not _check_pkg_repo()):
        _enable_pkg_repo(interactive, dry)

    # Install bitcoin-satellite
    if (btc):
        apt_pkg_list = ["bitcoin-satellite", "bitcoin-satellite-qt",
                        "bitcoin-satellite-tx"]
        dnf_pkg_list = ["bitcoin-satellite", "bitcoin-satellite-qt"]
        yum_pkg_list = ["bitcoin-satellite", "bitcoin-satellite-qt"]

        if (which("dnf")):
            # dnf matches partial package names, and so it seems that when
            # bitcoin-satellite and bitcoin-satellite-qt are installed in one
            # go, only the latter gets installed. The former is matched to
            # bitcoin-satellite-qt and assumed as installed. Hence, as a
            # workaround, install the two packages separately.
            for pkg in dnf_pkg_list:
                _install_packages(apt_pkg_list, [pkg], [pkg],
                                  interactive, update, dry)
        else:
            _install_packages(apt_pkg_list, [], yum_pkg_list,
                              interactive, update, dry)



def _install_sdr(interactive=True, update=False, dry=False):
    """Install SDR dependencies"""
    util._print_header("Installing SDR Dependencies")
    apt_pkg_list = ["gqrx-sdr", "rtl-sdr", "leandvb", "tsduck"]
    dnf_pkg_list = ["gqrx", "rtl-sdr", "leandvb", "tsduck"]
    yum_pkg_list = ["rtl-sdr", "leandvb", "tsduck"]
    # NOTE: leandvb and tsduck come from our repository. Also, note gqrx is not
    # available on CentOS (hence not included on the yum list).
    _install_packages(apt_pkg_list, dnf_pkg_list, yum_pkg_list, interactive,
                      update, dry)


def _install_usb(interactive=True, update=False, dry=False):
    """Install USB receiver dependencies"""
    util._print_header("Installing USB Receiver Dependencies")
    apt_pkg_list = ["iproute2", "iptables", "dvb-apps", "dvb-tools"]
    dnf_pkg_list = ["iproute", "iptables", "dvb-apps", "v4l-utils"]
    yum_pkg_list = ["iproute", "iptables", "dvb-apps", "v4l-utils"]
    # NOTE: the only package from our repository is dvb-apps in the specific
    # case of dnf (RPM) installation, because dvb-apps is not available on the
    # mainstream fc31/32 repository
    _install_packages(apt_pkg_list, dnf_pkg_list, yum_pkg_list, interactive,
                      update, dry)


def _install_standalone(interactive=True, update=False, dry=False):
    """Install standalone receiver dependencies"""
    util._print_header("Installing Standalone Receiver Dependencies")
    apt_pkg_list = ["iproute2", "iptables"]
    dnf_pkg_list = ["iproute", "iptables"]
    yum_pkg_list = ["iproute", "iptables"]
    _install_packages(apt_pkg_list, dnf_pkg_list, yum_pkg_list, interactive,
                      update, dry)


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
    p.add_argument("-y", "--yes",
                   action='store_true',
                   default=False,
                   help="Non-interactive mode. Answers \"yes\" automatically \
                   to binary package installation prompts")
    p.add_argument("--dry-run",
                   action='store_true',
                   default=False,
                   help="Prints all commands but does not execute them")

    subsubp = p.add_subparsers(title='subcommands',
                               help='Target sub-command')

    p1 = subsubp.add_parser('install',
                            description="Install software dependencies",
                            help='Install software dependencies')
    p1.add_argument("--target",
                    choices=["sdr", "usb", "standalone"],
                    default=None,
                    help="Target setup type for installation of dependencies")
    p1.add_argument("--btc",
                    action='store_true',
                    default=False,
                    help="Install bitcoin-satellite")
    p1.set_defaults(func=run, update=False)

    p2 = subsubp.add_parser('update', aliases=['upgrade'],
                            description="Update software dependencies",
                            help='Update software dependencies')
    p2.add_argument("--target",
                    choices=["sdr", "usb", "standalone"],
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

    if (args.target is not None):
        target_map = {
            "sdr"        : defs.sdr_setup_type,
            "usb"        : defs.linux_usb_setup_type,
            "standalone" : defs.standalone_setup_type
        }
        target = target_map[args.target]
    else:
        info = config.read_cfg_file(args.cfg, args.cfg_dir)
        if (info is None):
            return
        target = info['setup']['type']

    if (os.geteuid() != 0 and not args.dry_run):
        util.fill_print("Some commands require root access and will prompt "
                        "for password")

    if (args.dry_run):
        util._print_header("Dry Run Mode")

    # Update package index
    _update_pkg_repo(interactive, args.dry_run)

    # Common dependencies (regardless of setup)
    _install_common(interactive=interactive, update=args.update,
                    dry=args.dry_run, btc=args.btc)

    if (target == defs.sdr_setup_type):
        # The SDR packages are only available to the distributions below:
        _check_distro(["ubuntu", "fedora", "centos"],
                      defs.sdr_setup_type)
        _install_sdr(interactive=interactive, update=args.update,
                     dry=args.dry_run)
    elif (target == defs.linux_usb_setup_type):
        _install_usb(interactive=interactive, update=args.update,
                     dry=args.dry_run)
    elif (target == defs.standalone_setup_type):
        _install_standalone(interactive=interactive, update=args.update,
                            dry=args.dry_run)
    else:
        raise ValueError("Unexpected receiver target")


def drivers(args):
    # Interactive installation? I.e., requires user to press "y/n"
    interactive = (not args.yes)

    if (os.geteuid() != 0 and not args.dry_run):
        util.fill_print("Some commands require root access and will prompt "
                        "for password")

    if (args.dry_run):
        util._print_header("Dry Run Mode")

    runner = util.ProcessRunner(logger, args.dry_run)

    # Install pre-requisites
    linux_release  = platform.release()
    linux_headers  = "linux-headers-" + linux_release
    kernel_devel   = "kernel-devel-" + linux_release
    kernel_headers = "kernel-headers-" + linux_release
    apt_pkg_list   = ["make", "gcc", "git", "patch", "patchutils",
                     "libproc-processtable-perl",
                     linux_headers]
    dnf_pkg_list   = ["make", "gcc", "git", "patch", "patchutils",
                      "perl-Proc-ProcessTable", "perl-Digest-SHA",
                      "perl-File-Copy-Recursive", kernel_devel,
                      kernel_headers]
    yum_pkg_list   =  dnf_pkg_list

    # On dnf, not always the kernel-devel/headers package will be available for
    # the same version as the current kernel. Check:
    dnf_update_required = False
    if (which("dnf")):
        res_d = runner.run(["dnf", "list", kernel_devel],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           nocheck = True)
        res_h = runner.run(["dnf", "list", kernel_headers],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           nocheck = True)
        if (not args.dry_run):
            kernel_devel_unavailable   = (res_d.returncode != 0)
            kernel_headers_unavailable = (res_h.returncode != 0)
            dnf_update_required        = kernel_devel_unavailable or \
                                         kernel_headers_unavailable
            if (kernel_devel_unavailable):
                print("Could not find package {}".format(kernel_devel))
            if (kernel_headers_unavailable):
                print("Could not find package {}".format(kernel_headers))

    # If the target kernel-devel/kernel-headers versions are not available for
    # the current release, suggest to run dnf update:
    if (dnf_update_required):
        res = runner.run(["dnf", "list", "--upgrades", "kernel"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         nocheck = True)
        kernel_update_available = (res.returncode == 0)
        if (kernel_update_available):
            print("Kernel update required")
            if (util._ask_yes_or_no("OK to run \"dnf update\"?")):
                cmd = ["dnf", "update"]
                runner.run(util.root_cmd(cmd))
                print("Please reboot to load the new kernel and try the " +
                      "command below again:")
                print("\n  blocksat-cli deps tbs-drivers\n")
                sys.exit(1)
                return
        else:
            logger.error("Could not find an available kernel update")
            sys.exit(1)
            return

    _update_pkg_repo(interactive, args.dry_run)
    _install_packages(apt_pkg_list, dnf_pkg_list, yum_pkg_list,
                      interactive=interactive, update=False, dry=args.dry_run)

    # Clone the driver repositories
    driver_src_dir  = os.path.join(args.cfg_dir, "src", "tbsdriver")
    media_build_dir = os.path.join(driver_src_dir, "media_build")
    media_dir       = os.path.join(driver_src_dir, "media")

    if not os.path.exists(driver_src_dir):
        os.makedirs(driver_src_dir)

    if os.path.exists(media_build_dir):
        runner.run(["git", "pull", "origin", "master"], cwd = media_build_dir)
    else:
        runner.run(["git", "clone",
                    "https://github.com/tbsdtv/media_build.git"],
                   cwd = driver_src_dir)

    if os.path.exists(media_dir):
        runner.run(["git", "pull", "origin", "latest"], cwd = media_dir)
    else:
        runner.run(["git", "clone", "--depth=1",
                    "https://github.com/tbsdtv/linux_media.git",
                    "-b", "latest", "./media"], cwd = driver_src_dir)

    # Build the media drivers
    nproc = int(subprocess.check_output(["nproc"]).decode().rstrip())
    nproc_arg = "-j" + str(nproc)

    runner.run(["make", "cleanall"], cwd = media_build_dir)
    runner.run(["make", "dir", "DIR=../media"], cwd = media_build_dir)
    runner.run(["make", "allyesconfig"], cwd = media_build_dir)

    # FIXME: Temporary workaround for error "modpost: "__devm_regmap_init_sccb"
    # ov9650.ko undefined!": disable ov9650 from the build. The problem was
    # observed on kernel versions 5.3.7 and 5.7.7. Apply the workaround for any
    # version < 5.8.
    if (distro.id() == "fedora" and
        LooseVersion(linux_release) < LooseVersion('5.8')):
        runner.run(["sed", "-i",
                    "s/CONFIG_VIDEO_OV9650=m/CONFIG_VIDEO_OV9650=n/g",
                    "v4l/.config"], cwd = media_build_dir)

    runner.run(["make", nproc_arg], cwd = media_build_dir)

    # Delete the previous Media Tree installation
    media_lib_path = "/lib/modules/" + linux_release + \
                     "/kernel/drivers/media/"
    runner.run(
        util.root_cmd(["rm", "-rf", media_lib_path]),
        cwd = media_build_dir
    )

    # Install the new Media Tree
    runner.run(util.root_cmd(["make", "install"]), cwd = media_build_dir)

    # Download the firmware
    tbs_linux_url = "https://www.tbsdtv.com/download/document/linux/"
    fw_tarball    = "tbs-tuner-firmwares_v1.0.tar.bz2"
    fw_url        = tbs_linux_url + fw_tarball
    _download_file(fw_url, driver_src_dir, args.dry_run)

    # Install the firmware
    runner.run(util.root_cmd(["tar", "jxvf", fw_tarball, "-C",
                              "/lib/firmware/"]), cwd = driver_src_dir)

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

