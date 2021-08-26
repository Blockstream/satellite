"""SDR Receiver Wrapper"""
import logging
import subprocess
import textwrap
import threading
from argparse import ArgumentDefaultsHelpFormatter
from shutil import which

from . import config, defs, util, dependencies, monitoring, tsp

logger = logging.getLogger(__name__)
runner = util.ProcessRunner(logger)


def _tune_max_pipe_size(pipesize):
    """Tune the maximum size of pipes"""
    if (not which("sysctl")):
        logging.error("Couldn't tune max-pipe-size. Please check how to tune "
                      "it in your OS.")
        return False

    ret = subprocess.check_output(["sysctl", "fs.pipe-max-size"])
    current_max = int(ret.decode().split()[-1])

    if (current_max < pipesize):
        cmd = ["sysctl", "-w", "fs.pipe-max-size=" + str(pipesize)]
        print(
            textwrap.fill("The maximum pipe size that is currently "
                          "configured in your OS is of {} bytes, which is "
                          "not sufficient for the receiver application. "
                          "It will be necessary to run the following command "
                          "as root:".format(current_max),
                          width=80))
        print("\n" + " ".join(cmd) + "\n")

        if (not util._ask_yes_or_no("Is that OK?", default="y")):
            print("Abort")
            return False

        res = runner.run(cmd, root=True)
        return (res.returncode == 0)
    else:
        return True


# Rx status metrics printed by leandvb
rx_stat_map = {
    'SS': {  # based on the AGC but not calibrated to dBm (unitless)
        'key': 'level',
        'unit': None
    },
    'MER': {
        'key': 'snr',
        'unit': 'dB'
    },
    'VBER': {  # measured based on the BCH decoder output
        'key': 'ber',
        'unit': None
    }
}


def _get_monitor(args):
    """Create an object of the Monitor class

    Args:
        args      : SDR parser arguments
        sat_name  : Satellite name

    """
    # If debugging leandvb, don't echo the logs to stdout, otherwise the
    # logs get mixed on the console and it becomes hard to read them.
    echo = (args.debug_dvbs2 == 0)

    # Force scrolling logs if tsp is configured to print to stdout
    scrolling = tsp.prints_to_stdout(args) or args.log_scrolling

    return monitoring.Monitor(args.cfg_dir,
                              logfile=args.log_file,
                              scroll=scrolling,
                              echo=echo,
                              min_interval=args.log_interval,
                              server=args.monitoring_server,
                              port=args.monitoring_port,
                              report=args.report,
                              report_opts=monitoring.get_report_opts(args),
                              utc=args.utc)


def _monitor_demod_info(info_pipe, monitor):
    """Monitor leandvb's demodulator information

    Continuously read the demodulator information printed by leandvb into the
    descriptor pointed by --fd-info, which is tied to an unnamed pipe
    file. Then, feed the information into the monitor object.

    Args:
        info_pipe : Pipe object pointing to the pipe file that is used as
                    leandvb's --fd-info descriptor
        monitor   : Object of the Monitor class used to handle receiver
                    monitoring and logging

    """
    assert (isinstance(info_pipe, util.Pipe))

    # "Standard" status format accepted by the Monitor class
    status = {'lock': (False, None), 'level': None, 'snr': None, 'ber': None}

    while True:
        line = info_pipe.readline()

        if "FRAMELOCK" in line:
            status['lock'] = (line.split()[-1] == "1", None)

        for metric in rx_stat_map:
            if metric in line:
                val = float(line.split()[-1])
                unit = rx_stat_map[metric]['unit']
                key = rx_stat_map[metric]['key']
                status[key] = (val, unit)

        # If unlocked, clear the status metrics that depend on receiver locking
        # (they will show garbage if unlocked). If locked, just make sure that
        # all the required metrics are filled in the status dictionary.
        ready = True
        for metric in rx_stat_map:
            key = rx_stat_map[metric]['key']
            if status['lock'][0]:
                if key not in status or status[key] is None:
                    ready = False
            else:
                if (key in status):
                    del status[key]

        if (not ready):
            continue

        monitor.update(status)


def subparser(subparsers):
    """Parser for sdr command"""
    p = subparsers.add_parser('sdr',
                              description="Launch SDR receiver",
                              help='Launch SDR receiver',
                              formatter_class=ArgumentDefaultsHelpFormatter)

    # Monitoring options
    monitoring.add_to_parser(p)

    rtl_p = p.add_argument_group('rtl_sdr options')
    rtl_p.add_argument('--sps',
                       default=2.0,
                       type=float,
                       help='Samples per symbol, or, equivalently, the '
                       'target oversampling ratio')
    rtl_p.add_argument('--rtl-idx',
                       default=0,
                       type=int,
                       help='RTL-SDR device index')
    rtl_p.add_argument('-g',
                       '--gain',
                       default=40,
                       type=float,
                       help='RTL-SDR Rx gain')
    rtl_p.add_argument('-f',
                       '--iq-file',
                       default=None,
                       help='File to read IQ samples from instead of reading '
                       'from the RTL-SDR in real-time')

    ldvb_p = p.add_argument_group('leandvb options')
    ldvb_p.add_argument(
        '-n',
        '--n-helpers',
        default=6,
        type=int,
        help='Number of instances of the external LDPC decoder \
                        to spawn as child processes')
    ldvb_p.add_argument(
        '-d',
        '--debug-dvbs2',
        action='count',
        default=0,
        help="Debug leandvb's DVB-S2 decoding. Use it multiple "
        "times to increase the debugging level")
    ldvb_p.add_argument('-v',
                        '--verbose',
                        default=False,
                        action='store_true',
                        help='leandvb in verbose mode')
    ldvb_p.add_argument('--gui',
                        default=False,
                        action='store_true',
                        help='GUI mode')
    ldvb_p.add_argument('--derotate',
                        default=0,
                        type=float,
                        help='Frequency offset correction to apply in kHz')
    ldvb_p.add_argument('--fastlock',
                        default=False,
                        action='store_true',
                        help='leandvb fast lock mode')
    ldvb_p.add_argument('--rrc-rej',
                        default=30,
                        type=int,
                        help='leandvb RRC rej parameter')
    ldvb_p.add_argument('-m',
                        '--modcod',
                        choices=defs.modcods.keys(),
                        default='qpsk3/5',
                        metavar='',
                        help="DVB-S2 modulation and coding (MODCOD) scheme. "
                        "Choose from: " + ", ".join(defs.modcods.keys()))
    ldvb_p.add_argument('--ldpc-dec',
                        default="ext",
                        choices=["int", "ext"],
                        help="LDPC decoder to use (internal or external)")
    ldvb_p.add_argument('--ldpc-bf',
                        default=100,
                        help='Max number of iterations used by the internal \
                        LDPC decoder when not using an external LDPC tool')
    ldvb_p.add_argument('--ldpc-iterations',
                        default=25,
                        help='Max number of iterations used by the external \
                        LDPC decoder when using an external LDPC tool')
    ldvb_p.add_argument('--framesizes',
                        type=int,
                        default=1,
                        choices=[0, 1, 2, 3],
                        help="Bitmask of desired frame sizes (1=normal, \
                        2=short)")
    ldvb_p.add_argument('--no-tsp',
                        default=False,
                        action='store_true',
                        help='Feed leandvb output to stdout instead of tsp')
    ldvb_p.add_argument('--pipe-size',
                        default=32,
                        type=int,
                        help='Size in Mbytes of the input pipe file read by \
                        leandvb')

    # TSDuck Options
    tsp.add_to_parser(p)

    p.set_defaults(func=run, record=False)

    subsubparsers = p.add_subparsers(title='subcommands',
                                     help='Target sub-command')
    # IQ recording
    p2 = subsubparsers.add_parser(
        'rec',
        description="Record IQ samples instead of "
        "feeding them into leandvb",
        help='Record IQ samples',
        formatter_class=ArgumentDefaultsHelpFormatter)
    p2.add_argument('-f',
                    '--iq-file',
                    default="blocksat.iq",
                    help='File on which to save IQ samples received with '
                    'the RTL-SDR.')
    p2.set_defaults(record=True)

    return p


def run(args):
    info = config.read_cfg_file(args.cfg, args.cfg_dir)

    if (info is None):
        return

    pipe_size_bytes = int(args.pipe_size * (2**20))
    if (not _tune_max_pipe_size(pipe_size_bytes)):
        return

    # Check if all dependencies are installed
    apps = ["rtl_sdr"]
    if not args.record:
        apps.extend(["leandvb", "ldpc_tool"])
    if not args.no_tsp:
        apps.append("tsp")
    if (not dependencies.check_apps(apps)):
        return

    # Receiver configs
    l_band_freq = info['freqs']['l_band'] * 1e6
    sym_rate = defs.sym_rate[info['sat']['alias']]
    samp_rate = args.sps * sym_rate
    modcod = str(2**defs.modcods[args.modcod])  # bit mask

    assert(samp_rate < 2.4e6), \
        "Sample rate of {} exceeds the RTL-SDR limit".format(samp_rate)

    # Derotate up to the CFO recovery range on leandvb. If the desired
    # derotation exceeds the CFO correction range, change the L-band frequency
    # directly on the RTL instead.
    cfo_corr_range = (sym_rate / 4)
    derotate = args.derotate * 1e3
    while (derotate > cfo_corr_range):
        derotate -= cfo_corr_range
        l_band_freq += cfo_corr_range
    while (derotate < -cfo_corr_range):
        derotate += cfo_corr_range
        l_band_freq -= cfo_corr_range

    if (args.iq_file is None or args.record):
        rtl_cmd = [
            "rtl_sdr", "-g",
            str(args.gain), "-f",
            str(l_band_freq), "-s",
            str(samp_rate), "-d",
            str(args.rtl_idx)
        ]
        if (args.record):
            bytes_per_sec = (2 * samp_rate) / (2**20)
            logger.info("IQ recording will be saved on file {}".format(
                args.iq_file))
            logger.info(
                textwrap.fill("NOTE: the file will grow by approximately "
                              "{} MB per second.".format(bytes_per_sec)))
            if (not util._ask_yes_or_no("Proceed?", default="y")):
                return
            rtl_cmd.append(args.iq_file)
        else:
            rtl_cmd.append("-")

    ldvb_cmd = [
        "leandvb", "--nhelpers",
        str(args.n_helpers), "-f",
        str(samp_rate), "--sr",
        str(sym_rate), "--roll-off",
        str(defs.rolloff), "--standard", "DVB-S2", "--sampler", "rrc",
        "--rrc-rej",
        str(args.rrc_rej), "--modcods", modcod, "--framesizes",
        str(args.framesizes)
    ]
    if (args.iq_file is None):
        ldvb_cmd.extend(["--inpipe", str(pipe_size_bytes)])
    if (args.debug_dvbs2 > 0):
        ldvb_cmd.extend(("-d " * args.debug_dvbs2).split())
    if (args.ldpc_dec == "ext"):
        ldvb_cmd.extend([
            "--ldpc-helper",
            which("ldpc_tool"), "--ldpc-iterations",
            str(args.ldpc_iterations)
        ])
    else:
        ldvb_cmd.extend(["--ldpc-bf", str(args.ldpc_bf)])
    if (args.gui):
        ldvb_cmd.append("--gui")
    if (args.verbose):
        ldvb_cmd.append("-v")
    if (args.fastlock):
        ldvb_cmd.append("--fastlock")
    if (derotate != 0.0):
        ldvb_cmd.extend(["--derotate", str(int(derotate))])

    ldvb_stderr = None if (args.debug_dvbs2 > 0) else subprocess.DEVNULL

    logger.debug("Run:")

    # If recording IQ samples, run the rtl_sdr only
    if (args.record):
        p1 = subprocess.Popen(rtl_cmd)
        try:
            p1.communicate()
        except KeyboardInterrupt:
            p1.kill()
        return

    # Create unnamed pipe to receive real-time demodulation information from
    # leandvb (via --fd-info). Collect this information on a daemon thread.
    if (args.iq_file is None):
        info_pipe = util.Pipe()
        fd_info = str(info_pipe.w_fd)
        ldvb_cmd.extend(["--fd-info", fd_info])

        monitor = _get_monitor(args)

        t = threading.Thread(target=_monitor_demod_info,
                             args=(info_pipe, monitor),
                             daemon=True)
        t.start()

    # Prepare and validate the tsp command
    tsp_handler = tsp.Tsp()
    if (not tsp_handler.gen_cmd(args)):
        return

    if (args.iq_file is None):
        full_cmd = "> " + " ".join(rtl_cmd) + " | \\\n" + \
                    " ".join(ldvb_cmd)
        p1 = subprocess.Popen(rtl_cmd, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(ldvb_cmd,
                              stdin=p1.stdout,
                              stdout=subprocess.PIPE,
                              stderr=ldvb_stderr,
                              pass_fds=[fd_info])
    else:
        full_cmd = "> " + " ".join(ldvb_cmd) + " < " + args.iq_file
        fd_iq_file = open(args.iq_file)
        p2 = subprocess.Popen(ldvb_cmd,
                              stdin=fd_iq_file,
                              stdout=subprocess.PIPE,
                              stderr=ldvb_stderr)

    if (not args.no_tsp):
        full_cmd += " | \\\n" + " ".join(tsp_handler.cmd)
        logger.debug(full_cmd)
        tsp_handler.run(stdin=p2.stdout)
        try:
            tsp_handler.proc.communicate()
        except KeyboardInterrupt:
            tsp_handler.proc.kill()
            p2.kill()
            p1.kill()
    else:
        logger.debug(full_cmd)
        try:
            p2.communicate()
        except KeyboardInterrupt:
            p2.kill()
            p1.kill()

    print()
