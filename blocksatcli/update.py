import json
import logging
import os
import subprocess
import sys
import threading
from datetime import datetime, timedelta
from shutil import which

from packaging.version import Version

from . import dependencies, util
from .cache import Cache

logger = logging.getLogger(__name__)
runner = util.ProcessRunner(logger)

BLOCKSAT_PKG_LIST = ["blocksat-cli", "blocksat-gui", "blocksat"]
BLOCKSAT_BINARY_NAME = "blockstream-satellite"


class UpdateCache(Cache):
    """Update cache handler

    Creates a cache file containing update information. This file is verified
    before checking pip for updates, as it provides a faster interface.

    """

    def __init__(self, cfg_dir, pkg_name):
        """UpdateCache constructor

        Args:
            cfg_dir : Directory where the .update is located/created.
            pkg_name: Name of the blocksat package to track (blocksat-cli,
                blocksat-gui or blocksat).

        """
        assert (pkg_name in BLOCKSAT_PKG_LIST)
        self.pkg_name = pkg_name

        super().__init__(cfg_dir, filename=".update")
        self._check_and_update_format()

    def _check_and_update_format(self):
        """Update the format of the .update file if necessary

        - Format before version 2.5.0:
            {
                "last_check": "timestamp",
                "cli_update": ("current_version", "new_version")
            }

        - Format introduced on version 2.5.0:
            {
                "package_name_1": {
                    "last_check": "timestamp",
                    "update": ("current_version", "new_version")
                },
                ...
                package_name_n": {
                    "last_check": "timestamp",
                    "update": ("current_version", "new_version")
                },
                "last_check": "timestamp",
                "cli_update": ("current_version", "new_version")
            }

        Note: The last two fields ("last_check" and "cli_update") are kept also
        out of the nested dictionaries for compatibility in case the old CLI
        version (< 2.5.0) is executed with the same ~/.blocksat/.update file.

        """
        if not self.data:
            return  # Nothing to do. No data on the .update file.

        if any([key in self.data for key in BLOCKSAT_PKG_LIST]):
            return  # Nothing to do. New format already.

        logger.debug(
            "Old format detected on .update file. Updating the format...")

        # If the .update file has the old format, then it must have been
        # generated by the blocksat-cli package, as it was the only one
        # available at the time. Copy the info into a nested dictionary:
        pkg_name = "blocksat-cli"
        self.set(pkg_name + '.last_check', self.get('last_check'))
        self.set(pkg_name + '.update', self.get('cli_update'))

    def last_check(self):
        """Return the datetime corresponding to the last update verification"""
        return datetime.strptime(self.get(self.pkg_name + '.last_check'),
                                 '%Y-%m-%d %H:%M:%S.%f')

    def save(self, pkg_update=None):
        """Save information into the update cache file

        Args:
            pkg_update : Tuple with the current package version and the new
                package version available for update via pip. None when no
                update is available.

        """
        self.load()
        last_check = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        self.set(self.pkg_name + '.last_check', last_check)
        self.set(self.pkg_name + '.update', pkg_update)

        # Keep compatibility with the old .update format (used before v2.5.0)
        if self.pkg_name in ['blocksat', 'blocksat-cli']:
            self.set('last_check', last_check)
            self.set('cli_update', pkg_update)

        super().save()

    def has_update(self):
        """Returns whether there is an update available for the package"""
        return self.get(self.pkg_name + '.update')

    def new_version(self):
        """Get the new version available for update

        Note: This method should be called only after confirming an update is
            available by calling the "has_update" method. Otherwise, it will
            throw an exception.

        """
        return Version(self.get(self.pkg_name + '.update')[1])

    def clear(self):
        """Clear the cache"""
        self.data = {}
        super().save()  # Clear the cache file

    def recommend_update(self):
        """Print information regarding the recommended update"""
        update_info = self.get(self.pkg_name + '.update')

        if (update_info is None):
            return

        manager = get_current_package_manager()

        print(f"\nUpdate available for {self.pkg_name}")
        print("Current version: {}.\nAvailable version: {}.".format(
            update_info[0], update_info[1]))
        print("Please run: \n")

        if manager == "pip":
            print("\n    pip3 install {} --upgrade\n\n".format(self.pkg_name))
        elif manager == "apt":
            print("\n    apt install --only-upgrade {}".format(
                BLOCKSAT_BINARY_NAME))
        elif manager in ["dnf", "yum"]:
            print("\n    {} upgrade {}\n\n".format(manager,
                                                   BLOCKSAT_BINARY_NAME))


class Package():

    def __init__(self, name, manager, version):
        self.name = name
        self.version = version
        self.manager = manager
        self.new_version = None

    def _parse_upgrade_list(self, upgrade_list):
        """Return new version from the current package if available"""
        if self.manager not in ["apt", "dnf", "yum"]:
            return

        for line in upgrade_list:
            if self.name not in line:
                continue

            if self.manager == "apt" and 'upgradable from' not in line:
                continue

            if self.manager in ["dnf", "yum"] and 'updates' not in line:
                continue

            line_split = line.split()
            version = line_split[1].replace(']', '')
            # Get only the software version. Remove epoch and package version
            # (used on binary distribution).
            software_v = version.split(':')[-1]  # Remove epoch
            software_v = software_v.split('-')[0]
            software_v = software_v.split('+')[0]
            software_v = software_v.split('~')[0]

            return software_v

    def _check_binary_updates(self):
        """Check package updates via the binary package manager"""
        if self.manager in ["dnf", "yum"]:
            cmd_check_update = [self.manager, "check-update", self.name]
        else:
            cmd_check_update = ["apt", "list", "--upgradable", self.name]

        # Update the package list before checking for upgrades.
        try:
            dependencies.update_pkg_repo(interactive=False,
                                         stdout=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            logger.warning(
                f"Failed to update the {self.manager} package lists.")
            return

        res = runner.run(cmd_check_update,
                         root=True,
                         capture_output=True,
                         nocheck=True)

        if res.returncode != 0:
            logger.warning(f"Failed to check {self.name} updates.")
            return

        upgradable_list = res.stdout.decode().split('\n')
        self.new_version = self._parse_upgrade_list(upgradable_list)

    def _check_pip_updates(self):
        """Check if the package has updates available via pip"""
        try:
            outdated_list = json.loads(
                subprocess.check_output(
                    ["pip3", "list", "--outdated", "--format", "json"],
                    stderr=subprocess.DEVNULL).decode())
        except subprocess.CalledProcessError:
            # Don't break if the command fails. It could be a problem on pip.
            # For example, there is a bug in which pip throws a TypeError on
            # the "list --outdated" command saying: '>' not supported between
            # instances of 'Version' and 'Version'
            logger.warning(f"Failed to check {self.name} updates.")
            return

        for package in outdated_list:
            if (package['name'] == self.name):
                # Save the available update on the cache file
                self.new_version = package['latest_version']
                logger.debug(f"Update available for {package['name']}")
                break

    def is_upgradable(self):
        """Check if the package has updates"""
        if self.manager != "pip":
            self._check_binary_updates()
        else:
            self._check_pip_updates()

        return True if self.new_version is not None else False


def get_current_package_manager():
    """Return the package manager used in the current installation"""
    this_file = os.path.realpath(__file__)
    root_path = os.path.dirname(this_file)
    site_dir = os.path.dirname(root_path)

    if '/usr/lib' in root_path:
        try:
            return dependencies.get_pkg_manager()
        except RuntimeError:
            logger.error("Could not found the package manager from the "
                         "current installation.")
    else:
        for path in sys.path:
            if site_dir in path:
                return 'pip' if which("pip3") else None

    # Not installed
    return None


def get_package_info(pkg_name):
    """Return the correct package name and manager of the current package

    This function tries to assert the name of the current blocksat package and
    the package manager used to install it. For example, the package
    'blocksat-cli' and 'blocksat-gui' can be installed individually or
    together. Thus, the correct name of the package depends on the way it was
    installed:

        1) From binary package manager:
            In this case, for the binary package manager, the package is called
            "blockstream-satellite". For the python manager (pip) the package
            will be called "blocksat".

        2) From PyPI:
            In this case, the CLI package is called "blocksat-cli" and the GUI
            package is called "blocksat-gui".

        3) From source:
            In this case, the user may install the package via the main
            setup.py file, which installs the CLI and GUI together in a package
            called "blocksat", or run "make install", which installs the CLI
            and GUI packages separately. In any case, this function attempts to
            retrieve the appropriate package information.

    Args:
        pkg_name: Name of the blocksat package (blocksat-gui, blocksat-cli, or
            blocksat).

    Return:
        dict: Dictionary with the correct package 'name' and 'manager'.

    """
    assert (pkg_name in ["blocksat-cli", "blocksat-gui"])

    manager = get_current_package_manager()
    if not manager:
        return

    pkg_options = []

    if manager != "pip":
        # If the package manager is not pip, the package was installed via the
        # binary package manager. In this case, the only option is the package
        # called "blocksat".
        pkg_options.append("blocksat")
    else:
        # If the package was installed using pip, give preference to the
        # individual packages (i.e., blocksat-cli or blocksat-gui). If the
        # individual package version is not installed, check the package called
        # "blocksat" which contains both packages.
        pkg_options.extend([pkg_name, "blocksat"])

    for pkg in pkg_options:
        if dependencies.check_python_packages([pkg]):
            logger.debug(f"Found {pkg} installed via pip3")
            return {'name': pkg, 'manager': manager}

    logger.error("Could not find any Blocksat package installed")


def _check_updates(cfg_dir, pkg_info, pkg_version):
    """Check if the package has updates available

    Args:
        cfg_dir     : Directory where the .update file is located/created.
        pkg_info    : Dictionary with the blocksat package information.
        pkg_version : Current version of the Blocksat package

    """
    logger.info(
        f"Checking {pkg_info['name']} updates via {pkg_info['manager']}")

    # Save the new pip verification timestamp on the cache file
    update_cache = UpdateCache(cfg_dir, pkg_info['name'])
    update_cache.save()

    pkg = Package(name=pkg_info['name'],
                  manager=pkg_info['manager'],
                  version=pkg_version)

    if pkg.is_upgradable():
        # Save the available update on the cache file
        update_cache.save((pkg.version, pkg.new_version))
        logger.debug(f"Update available for {pkg.name}")
    else:
        logger.debug(f"{pkg.name} is up-to-date")
        # Clear a potential update flag on the cache file
        update_cache.save()

    return pkg


def check_package_updates(cfg_dir, pkg_name, pkg_version):
    """Check if the Blocksat package has updates available

    Check the cache file first. If the cache is old enough, check updates
    through the pip interface. The cache file can be verified very quickly,
    whereas the verification through pip can be rather slow.

    Args:
        cfg_dir     : User's configuration directory.
        pkg_name    : Name of the Blocksat package.
        pkg_version : Current version of the Blocksat package.

    """
    # Create the configuration directory if it does not exist
    if not os.path.exists(cfg_dir):
        os.makedirs(cfg_dir, exist_ok=True)

    pkg_info = get_package_info(pkg_name)
    if pkg_info is None:
        return

    # Check the update cache file first
    update_cache = UpdateCache(cfg_dir, pkg_info['name'])

    # If the cache file says there is an update available, check whether the
    # current version is already the updated one. If not, recommend the update.
    if (update_cache.has_update()):
        if (update_cache.new_version() > Version(pkg_version)):
            # Not updated yet. Recommend it.
            update_cache.recommend_update()
        else:
            # Already updated. Clear the update flag.
            update_cache.save()
        return

    # If the last update verification was still recent (less than a day ago),
    # do not check. Avoid the unnecessary spawning of the update-checking
    # thread.
    if (pkg_info['name'] in update_cache.data):
        time_since_last_check = (datetime.now() - update_cache.last_check())
        if (time_since_last_check < timedelta(days=1)):
            logger.debug(
                "Last update check was less than a day ago: {}".format(
                    str(time_since_last_check)))
            return

    # Check updates on a thread. This verification can be slow, so it is
    # better not to block.
    t = threading.Thread(target=_check_updates,
                         args=(cfg_dir, pkg_info, pkg_version))
    t.start()
