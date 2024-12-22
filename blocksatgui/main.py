#!/usr/bin/env python3

import logging
import platform
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from packaging.version import Version

from . import __version__
from .components import messagebox
from .daemon import daemon
from .qt import QApplication

logger = logging.getLogger(__name__)


def display_error_message(title: str, description: str):
    """Display an error message dialog and exit the application"""
    QApplication(sys.argv)  # necessary to display the dialog
    messagebox.Message(parent=None, title=title, msg=description)
    sys.exit(1)


# Blocksat-GUI works by providing a graphical interface to the Blocksat-CLI
# functionality, and it does not work without it. Therefore, start the GUI
# checking if blocksat-cli is installed on the system.
try:
    from blocksatcli import __version__ as cli_version
except (ImportError, ModuleNotFoundError):
    display_error_message(
        title="Blockstream Satellite GUI error",
        description=(
            "Blocksat GUI could not be initialized because blocksat-cli "
            "is missing. Please make sure blocksat-cli is installed on "
            "your system."))


def get_parser():
    parser = ArgumentParser(
        prog="blocksat-gui",
        description="Blockstream Satellite Graphical Interface",
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d",
                        "--debug",
                        action="store_true",
                        help="Set debug mode")
    parser.add_argument("-v",
                        "--version",
                        action="version",
                        version="%(prog)s {}".format(__version__),
                        help="Show version and exit")

    subparsers = parser.add_subparsers(title='subcommands',
                                       help='Target sub-command',
                                       dest='subcommand')
    daemon.subparser(subparsers)

    return parser


def main():

    parser = get_parser()
    args = parser.parse_args()
    logging_fmt = '%(asctime)s %(levelname)-8s %(name)s %(message)s' if \
                  args.debug else '%(asctime)s %(levelname)-8s %(message)s'
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format=logging_fmt,
                        datefmt='%Y-%m-%d %H:%M:%S')

    if platform.system() != "Linux":
        display_error_message(
            title="Blockstream Satellite",
            description=("Operating system not supported. The application is "
                         "currently Linux-only."))

    # Check if the GUI and CLI has matching versions.
    if Version(__version__) < Version(cli_version):
        display_error_message(
            title="Blockstream Satellite GUI error",
            description=(
                "Blockstream Satellite GUI v.{} is imcompatible with the "
                "current CLI installed on the system (blocksat-cli v.{}). "
                "Please update the GUI to match the CLI version.".format(
                    __version__, cli_version)))

    # Run the subcommand if it exists and do not run the main app.
    if hasattr(args, 'func'):
        args.func(args)
        sys.exit(0)

    # After all checks are done, import the main app and initialize it.
    from .app import init_app
    init_app()


if __name__ == "__main__":
    main()
