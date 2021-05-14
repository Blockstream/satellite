import logging
import os
import subprocess
from pathlib import Path

from . import defs
from . import util

logger = logging.getLogger(__name__)


def add_to_parser(parser):
    p = parser.add_argument_group('tsduck options')
    p.add_argument('-l',
                   '--local-address',
                   default="127.0.0.1",
                   help='IP address of the local interface on which to '
                   'listen for UDP datagrams unpacked from MPE')
    p.add_argument('--tsp-buffer-size-mb',
                   default=1.0,
                   type=float,
                   help='Input buffer size in MB')
    p.add_argument('--tsp-max-flushed-packets',
                   default=10,
                   type=int,
                   help='Maximum number of packets processed by a tsp '
                   'processor')
    p.add_argument('--tsp-max-input-packets',
                   default=10,
                   type=int,
                   help='Maximum number of packets received at a time from '
                   'the tsp input plugin')
    p.add_argument(
        '--ts-monitor-bitrate',
        nargs='?',
        const=1,
        type=int,
        help='Monitor the MPEG TS bitrate. Specify the bitrate '
        'reporting period in seconds to override the default period '
        'of %(const)s sec')
    p.add_argument('--ts-monitor-sequence',
                   default=False,
                   action='store_true',
                   help='Monitor MPEG TS sequence discontinuities')
    g1 = p.add_mutually_exclusive_group()
    g1.add_argument(
        '--ts-file',
        nargs='?',
        const='blocksat.ts',
        help='Save MPEG TS packets on a file for future analysis. Specify the '
        'file name by argument to override the default name of \"%(const)s\"')
    g1.add_argument(
        '--ts-dump',
        action='store_true',
        help='Dump the contents of the incoming MPEG TS packets to stdout')
    p.add_argument('--ts-dump-opts',
                   nargs='+',
                   default=['--no-pager', '--headers-only'],
                   help='tsdump options used when option --ts-dump is enabled')
    p.add_argument('--ts-analysis',
                   nargs='?',
                   const="ts-analysis.txt",
                   help='Analyze MPEG transport stream and save report on '
                   'program termination. Specify the analysis file name to '
                   'override the default name of \"%(const)s\"')


class Tsp():
    """Interface to the transport stream processor (tsp) application

    Prepares a tsp command based on command-line options and executes the
    process.

    """
    def __init__(self):
        self.cmd = []
        self.proc = None
        self.dump_proc = None
        self.ts_dump = False
        self.ts_dump_opts = []

    def gen_cmd(self, args, in_plugin=None):
        """Generate the tsp command

        Args:
            in_plugin : List with input plugin command to be used by tsp.

        Rerturns:
            Boolean indicating whether a valid command was generated.

        """
        # cache the request for TS dumping
        self.ts_dump = args.ts_dump
        self.ts_dump_opts = args.ts_dump_opts

        self.cmd = cmd = [
            "tsp", "--realtime", "--buffer-size-mb",
            str(args.tsp_buffer_size_mb), "--max-flushed-packets",
            str(args.tsp_max_flushed_packets), "--max-input-packets",
            str(args.tsp_max_input_packets)
        ]

        if (in_plugin):
            cmd.extend(in_plugin)

        if (args.ts_analysis):
            logger.info("MPEG-TS analysis will be saved on file {}".format(
                args.ts_analysis))
            if (not util._ask_yes_or_no("Proceed?", default="y")):
                return False
            cmd.extend(["-P", "analyze", "-o", args.ts_analysis])

        if (args.ts_monitor_bitrate):
            cmd.extend([
                "-P", "bitrate_monitor", "-p",
                str(args.ts_monitor_bitrate), "--min", "0"
            ])

        if (args.ts_monitor_sequence):
            cmd.extend(["-P", "continuity"])

        cmd.extend([
            "-P", "mpe", "--pid", "-".join([str(pid) for pid in defs.pids]),
            "--udp-forward", "--local-address", args.local_address
        ])

        # Output the MPEG TS stream to one of the following:
        #   a) a file;
        #   b) stdout (if using --ts-dump);
        #   c) /dev/null (default).
        if (args.ts_file is not None):
            logger.info("MPEG TS output will be saved on file {}".format(
                args.ts_file))
            if (not util._ask_yes_or_no("Proceed?", default="y")):
                return False
            cmd.extend(["-O", "file", args.ts_file])
        elif (not args.ts_dump):
            cmd.extend(["-O", "drop"])

        return True

    def run(self, stdin=None):
        """Run tsp

        Args:
            in_plugin : List with input plugin command to be used by tsp.
            stdin : Stdin to attach to the tsp process.

        Rerturns:
            Boolean indicating whether the process is running succesfully.

        """
        # Create a .tsduck.lastcheck file on the home directory to skip the
        # TSDuck version check.
        Path(os.path.join(util.get_home_dir(), ".tsduck.lastcheck")).touch()

        # When tsdump is enabled, hook tsp and tspdump through a pipe file (tsp
        # on the write side and tsdump on the read side)
        if (self.ts_dump):
            info_pipe = util.Pipe()
            stdout = info_pipe.w_fo
        else:
            stdout = None

        self.proc = subprocess.Popen(self.cmd, stdin=stdin, stdout=stdout)

        if (self.ts_dump):
            tsdump_cmd = ['tsdump']
            tsdump_cmd.extend(self.ts_dump_opts)
            self.dump_proc = subprocess.Popen(tsdump_cmd, stdin=info_pipe.r_fo)


def prints_to_stdout(args):
    """Check if tsp is configured to print to stdout"""
    return args.ts_monitor_bitrate or args.ts_monitor_sequence or \
        args.ts_dump
