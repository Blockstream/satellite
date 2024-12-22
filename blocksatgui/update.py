from packaging.version import Version

from blocksatcli import update

from . import __version__
from .utils import get_default_cfg_dir
from .components import messagebox


def show_available_updates(parent=None):
    """Show available GUI update if any"""
    pkg_info = update.get_package_info("blocksat-gui")

    if pkg_info is None:
        return

    blocksat_dir = get_default_cfg_dir()
    update_gui = update.UpdateCache(blocksat_dir, pkg_info['name'])
    if (update_gui.has_update()
            and update_gui.new_version() > Version(__version__)):
        versions = update_gui.has_update()
        msg = ("New version available for {}.\n"
               "Current version: {}.\n"
               "Latest version: {}".format(pkg_info['name'], versions[0],
                                           versions[1]))
    else:
        msg = "Blocksat-GUI is up-to-date"

    messagebox.Message(parent=parent,
                       title="Blocksat GUI updates",
                       msg=msg,
                       msg_type="info")


def check_gui_updates():
    """Check blocksat GUI updates"""
    blocksat_dir = get_default_cfg_dir()
    update.check_package_updates(blocksat_dir, "blocksat-gui", __version__)
