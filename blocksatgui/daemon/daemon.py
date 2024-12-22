import logging
from argparse import ArgumentDefaultsHelpFormatter

from blocksatcli import util

from ..components import viewer
from . import config, dependencies

logger = logging.getLogger(__name__)


def add_run_opts(parser):
    parser.add_argument(
        "-y",
        "--yes",
        action='store_true',
        default=False,
        help="Non-interactive mode. Answers \"yes\" automatically \
                                to installation prompts")
    parser.add_argument("--dry-run",
                        action='store_true',
                        default=False,
                        help="Print all commands but do not execute them")


def subparser(subparsers):

    p1 = subparsers.add_parser('config',
                               aliases=['cfg'],
                               description="Configure the GUI",
                               help='Configure the GUI',
                               formatter_class=ArgumentDefaultsHelpFormatter)
    add_run_opts(p1)
    p1.set_defaults(func=configure)

    p2 = subparsers.add_parser('dependencies',
                               aliases=['deps'],
                               description="Install GUI dependencies",
                               help='Install GUI dependencies')
    add_run_opts(p2)
    p2.set_defaults(func=deps)


def configure(args):
    view = viewer.CliViewer()
    runner = util.ProcessRunner(logger, args.dry_run)
    runner.set_auth_manager("sudo")
    config.install(view, runner, logger, args.dry_run, not args.yes)


def deps(args):
    dependencies.install(args)
