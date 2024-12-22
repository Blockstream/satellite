import logging
import os
import sys

from blocksatcli import util, dependencies
from blocksatcli.dependencies import (check_python_packages, install_packages,
                                      install_packages_pip)

logger = logging.getLogger(__name__)
util.ProcessRunner.set_auth_manager("pkexec")


def _detect_venv():
    """Detect if running inside a virtual environment"""
    return hasattr(sys, 'real_prefix') or sys.base_prefix != sys.prefix


def _detect_root_install():
    """Detect if installed with root user"""
    return os.path.abspath(__file__).startswith("/usr/")


def check_dependencies():
    """Check if all dependencies are installed"""
    deps = ["dbus-python"]
    if not _detect_root_install() and not _detect_venv():
        deps.append("PyGObject")
    return check_python_packages(deps)


def install(args):
    """Install dependencies to run Blocksatd

    The Blocksat Daemon requires the dbus-python package and either the
    PyGObject or PySide package to run the main loop. Also, the blocksatd
    daemon should always be started by the root user, with the dependencies
    available to the root user.

    Depending on the GUI installation method, the dependencies are installed
    using either the system package manager (apt/dnf) or pip. The following
    scenarios are considered:

    1. GUI installed via pip (without sudo):
        - pip installation: not used.
        - apt/dnf installation: dbus and PyGObject.
        - Main loop runner: PyGObject.
        - Note: The PySide package will not be installed without sudo.

    2. GUI installed with pip (with sudo):
        - pip installation: dbus.
        - apt/dnf installation: not used.
        - Main loop runner: PySide.

    3. GUI installed with pip in a virtual environment:
        - pip installation: dbus.
        - apt/dnf installation: not used.
        - Main loop runner: PySide.
        - Note: The root and non-root user will use the same installed packages
          located in the virtual environment.

    4. GUI installed as a system package:
        - pip installation: not used.
        - apt/dnf installation: dbus.
        - Main loop runner: PySide.

    Args:
        args: List of arguments

    """
    if args is None:
        interactive = set_dry_run = False
    else:
        interactive = (not args.yes)
        set_dry_run = args.dry_run

    # Configure the subprocess runner from the CLI dependencies module
    dependencies.runner.set_dry(set_dry_run)

    # Check if all dependencies are installed
    if check_dependencies():
        logger.info("All dependencies are installed.")
        return

    # On a virtual env, it does not suffice to install python3-dbus globally
    # via package manager. If the venv is isolated, it still won't be able to
    # find the package. In this case, install it via pip in the virtual env.
    if _detect_venv():
        logger.info(
            "Virtual environment detected. The dbus module (dbus-python) "
            "will be installed via pip. Additional packages need to be "
            "installed to build dbus-python using pip.")

        # Install dbus dependency to install it via pip
        dbus_python_deps = {
            'apt': ["libdbus-1-dev", "libglib2.0-dev"],
            'dnf': [
                "dbus-devel", "dbus-daemon", "glib2-devel", "gcc",
                "python3-devel"
            ],
            'yum': [
                "dbus-devel", "dbus-daemon", "glib2-devel", "gcc",
                "python3-devel"
            ]
        }

        install_packages_pip(["meson", "cmake", "ninja", "patchelf"])

        install_packages(apt_list=dbus_python_deps['apt'],
                         dnf_list=dbus_python_deps['dnf'],
                         yum_list=dbus_python_deps['yum'],
                         interactive=False)

        install_packages_pip(["dbus-python"])
        return

    packages = {
        'apt': ["python3-dbus"],
        'dnf': ["python3-dbus"],
        'yum': ["python3-dbus"]
    }

    if not _detect_root_install() and not _detect_venv():
        # Install PyGObject if not running as root and not in a virtual env
        packages['apt'].append("python3-gi")
        packages['dnf'].append("python3-gobject")
        packages['yum'].append("python3-gobject")

    # Install using system package manager
    install_packages(apt_list=packages['apt'],
                     dnf_list=packages['dnf'],
                     yum_list=packages['yum'],
                     interactive=interactive)
