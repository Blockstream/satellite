import json
import logging
import os
import subprocess
import threading
from datetime import datetime, timedelta
from distutils.version import StrictVersion
from shutil import which

from .cache import Cache

logger = logging.getLogger(__name__)


class UpdateCache(Cache):
    """Update cache handler

    Creates a cache file containing update information. This file is verified
    before checking pip for updates, as it provides a faster interface.

    """
    def __init__(self, cfg_dir):
        """UpdateCache constructor

        Args:
            cfg_dir : Directory where the .update is located/created

        """
        super().__init__(cfg_dir, filename=".update")

    def last_check(self):
        """Return the datetime corresponding to the last update verification"""
        return datetime.strptime(self.data['last_check'],
                                 '%Y-%m-%d %H:%M:%S.%f')

    def save(self, cli_update=None):
        """Save information into the update cache file

        Args:
            cli_update : Version of a new CLI version available for update,
                         if any

        """
        self.data['last_check'] = datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S.%f')
        self.data['cli_update'] = cli_update
        super().save()

    def has_update(self):
        """Returns whether there is an update available for the CLI"""
        return 'cli_update' in self.data and \
            self.data['cli_update'] is not None

    def new_version(self):
        """Get the new version available for an update

        Note: This method should be called only if there is a new update, as
            confirmed by "has_update". Otherwise, it will throw an exception.

        """
        return StrictVersion(self.data['cli_update'][1])

    def recommend_update(self):
        """Print information regarding the recommended update"""
        if (self.data['cli_update'] is None):
            return
        print("\nUpdate available for blocksat-cli")
        print("Current version: {}.\nLatest version: {}.".format(
            self.data['cli_update'][0], self.data['cli_update'][1]))
        print("Please run:\n\n    pip3 install blocksat-cli --upgrade\n\n")


def _check_pip_updates(cfg_dir, cli_version):
    """Check if the CLI has updates available via pip

    Args:
        cfg_dir     : Directory where the .update is located/created
        cli_version : Current version of the CLI

    """
    logger.debug("Checking blocksat-cli updates")

    # Save the new pip verification timestamp on the cache file
    update_cache = UpdateCache(cfg_dir)
    update_cache.save()

    # Is blocksat-cli installed?
    res = subprocess.run(["pip3", "show", "blocksat-cli"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    found = (res.returncode == 0)

    # If the CLI was not installed via pip, don't check updates
    if (not found):
        logger.debug("Could not find blocksat-cli installed via pip3")
        return

    # Is the CLI outdated?
    try:
        outdated_list = json.loads(
            subprocess.check_output(
                ["pip3", "list", "--outdated", "--format", "json"],
                stderr=subprocess.DEVNULL).decode())
    except subprocess.CalledProcessError:
        # Don't break if the command fails. It could be a problem on pip. For
        # example, there is a bug in which pip throws a TypeError on the "list
        # --outdated" command saying: '>' not supported between instances of
        # 'Version' and 'Version'
        logger.warning("Failed to check blocksat-cli updates.")
        return

    cli_outdated = False
    for package in outdated_list:
        if (package['name'] == "blocksat-cli"):
            cli_outdated = True
            # Save the available update on the cache file
            update_cache.save((package['version'], package['latest_version']))
            logger.debug("Update available for blocksat-cli")

    if (not cli_outdated):
        logger.debug("blocksat-cli is up-to-date")
        # Clear a potential update flag on the cache file
        update_cache.save()


def check_cli_updates(args, cli_version):
    """Check if the CLI has updates available

    Check the cache file first. If the cache is old enough, check updates
    through the pip interface. The cache file can be verified very quickly,
    whereas the verification through pip can be rather slow.

    Args:
        args        : Arguments from parent argument parser
        cli_version : Current version of the CLI

    """

    # If pip is not available, assume the CLI was not installed via pip
    if (not which("pip3")):
        logger.debug("pip3 unavailable")
        return

    # Create the configuration directory if it does not exist
    if not os.path.exists(args.cfg_dir):
        os.makedirs(args.cfg_dir, exist_ok=True)

    # Check the update cache file first
    update_cache = UpdateCache(args.cfg_dir)

    # If the cache file says there is an update available, check whether the
    # current version is already the updated one. If not, recommend the update.
    if (update_cache.has_update()):
        if (update_cache.new_version() > StrictVersion(cli_version)):
            # Not updated yet. Recommend it.
            update_cache.recommend_update()
        else:
            # Already updated. Clear the update flag.
            update_cache.save()
        return

    # If the last update verification was still recent (less than a day ago),
    # do not check pip. Avoid the unnecessary spawning of the pip-checking
    # thread.
    if (update_cache.data):
        time_since_last_check = (datetime.now() - update_cache.last_check())
        if (time_since_last_check < timedelta(days=1)):
            logger.debug(
                "Last update check was less than a day ago: {}".format(
                    str(time_since_last_check)))
            return

    # Check pip updates on a thread. This verification can be slow, so it is
    # better not to block.
    t = threading.Thread(target=_check_pip_updates,
                         args=(args.cfg_dir, cli_version))
    t.start()
