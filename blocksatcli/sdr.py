"""SDR Receiver Wrapper"""
from argparse import ArgumentDefaultsHelpFormatter
from . import config, defs, util
import subprocess, logging, textwrap, os
logger = logging.getLogger(__name__)


def _tune_max_pipe_size(pipesize):
    """Tune the maximum size of pipes"""
    try:
        subprocess.check_output(["which", "sysctl"])
    except subprocess.CalledProcessError:
        logging.error("Couldn't tune max-pipe-size. Please check how to tune "
                      "it in your OS.")
        return False

    ret = subprocess.check_output(["sysctl", "fs.pipe-max-size"])
    current_max = int(ret.decode().split()[-1])

    if (current_max < pipesize):
        cmd = util.root_cmd(["sysctl", "-w",
                             "fs.pipe-max-size=" + str(pipesize)])

        print(textwrap.fill("The maximum pipe size that is currently "
                            "configured in your OS is of {} bytes, which is "
                            "not sufficient for the demodulator application. "
                            "It will be necessary to run the following command "
                            "as root:".format(current_max), width=80))
        print("\n" + " ".join(cmd) + "\n")

        if (not util._ask_yes_or_no("Is that OK?", default="y")):
            print("Abort")
            return False

        return subprocess.check_output(cmd)
    else:
        return True


def _check_apps(tsp_disabled, bindir):
    """Check if required apps are installed"""
    try:
        subprocess.check_output(["which", "rtl_sdr"])
    except subprocess.CalledProcessError:
        logging.error("Couldn't find rtl_sdr. Is it installed?")
        return False

    if (not os.path.isfile(os.path.join(bindir, "leandvb"))):
        logging.error("Couldn't find leandvb. Is it installed?")
        return False

    if (not os.path.isfile(os.path.join(bindir, "ldpc_tool"))):
        logging.error("Couldn't find ldpc_tool. Is it installed?")
        return False

    if (tsp_disabled):
        return True

    if (not os.path.isfile(os.path.join(bindir, "tsp"))):
        logging.error("Couldn't find tsp. Is it installed?")
        return False

    return True


def subparser(subparsers):
    """Parser for sdr command"""
    p = subparsers.add_parser('sdr',
                              description="Launch SDR receiver",
                              help='Launch SDR receiver',
                              formatter_class=ArgumentDefaultsHelpFormatter)

    rtl_p = p.add_argument_group('rtl_sdr options')
    rtl_p.add_argument('--sps', default=2.0, type=float,
                       help='Samples per symbol, or, equivalently, the '
                           'target oversampling ratio')
    rtl_group = rtl_p.add_mutually_exclusive_group()
    rtl_group.add_argument('-g', '--gain', default=40, type=float,
                           help='RTL-SDR Rx gain')
    rtl_group.add_argument('-f', '--iq-file', default=None,
                           help='File to read IQ samples from instead of reading '
                           'from the RTL-SDR in real-time')

    ldvb_p = p.add_argument_group('leandvb options')
    ldvb_p.add_argument('-n', '--n-helpers', default=6, type=int,
                        help='Number of instances of the external LDPC decoder \
                        to spawn as child processes')
    ldvb_p.add_argument('-d', '--debug-ts', action='count', default=0,
                        help="Activate debugging on leandvb. Use it multiple "
                        "times to increase the debugging level")
    ldvb_p.add_argument('-v', '--verbose', default=False, action='store_true',
                        help='leandvb in verbose mode')
    ldvb_p.add_argument('--gui', default=False, action='store_true',
                        help='GUI mode')
    ldvb_p.add_argument('--derotate', default=0, type=float,
                        help='Frequency offset correction to apply in kHz')
    ldvb_p.add_argument('--fastlock', default=False, action='store_true',
                        help='leandvb fast lock mode')
    ldvb_p.add_argument('--rrc-rej', default=30, type=int,
                        help='leandvb RRC rej parameter')
    ldvb_p.add_argument('-m', '--modcod', default="low",
                        choices=["low", "high"],
                        help="Choose low-throughput vs high-throughput MODCOD")
    ldvb_p.add_argument('--ldpc-dec', default="ext", choices=["int", "ext"],
                        help="LDPC decoder to use (internal or external)")
    ldvb_p.add_argument('--ldpc-bf', default=100,
                        help='Max number of iterations used by the internal \
                        LDPC decoder when not using an external LDPC tool')
    ldvb_p.add_argument('--ldpc-iterations', default=25,
                        help='Max number of iterations used by the external \
                        LDPC decoder when using an external LDPC tool')
    ldvb_p.add_argument('--framesizes', type=int, default=1, choices=[0,1,2,3],
                        help="Bitmask of desired frame sizes (1=normal, \
                        2=short)")
    ldvb_p.add_argument('--no-tsp', default=False, action='store_true',
                        help='Feed leandvb output to stdout instead of tsp')
    ldvb_p.add_argument('--pipe-size', default=32, type=int,
                        help='Size in Mbytes of the input pipe file read by \
                        leandvb')

    tsp_p = p.add_argument_group('tsduck options')
    tsp_p.add_argument('--buffer-size-mb', default=1.0, type=float,
                       help='Input buffer size in MB')
    tsp_p.add_argument('--max-flushed-packets', default=10, type=int,
                       help='Maximum number of packets processed by a tsp '
                       'processor')
    tsp_p.add_argument('--max-input-packets', default=10, type=int,
                       help='Maximum number of packets received at a time from '
                       'the tsp input plugin ')
    tsp_p.add_argument('-p', '--bitrate-period', default=1, type=int,
                       help='Period of bitrate reports in seconds')
    tsp_p.add_argument('-l', '--local-address', default="127.0.0.1",
                       help='IP address of the local interface on which to '
                       'listen for UDP datagrams')
    tsp_p.add_argument('-a', '--analyze', default=False, action='store_true',
                       help='Analyze transport stream and save report on '
                       'program termination')
    tsp_p.add_argument('--analyze-file', default="ts-analysis.txt",
                       action='store_true',
                       help='File on which to save the MPEG-TS analysis.')
    tsp_p.add_argument('--no-bitrate-monitoring', default=False,
                       action='store_true',
                       help='Disable bitrate monitoring')
    tsp_p.add_argument('--monitor-ts', default=False,
                       action='store_true',
                       help='Mnitor MPEG TS sequence discontinuities')
    p.set_defaults(func=run,
                   record=False)

    subsubparsers = p.add_subparsers(title='subcommands',
                                     help='Target SDR sub-command')
    # IQ recording
    p2 = subsubparsers.add_parser('rec',
                                  description="Record IQ samples instead of "
                                  "feeding them into leandvb",
                                  help='Record IQ samples',
                                  formatter_class=ArgumentDefaultsHelpFormatter)
    p2.add_argument('-f', '--iq-file', default="blocksat.iq",
                    help='File on which to save IQ samples received with '
                    'the RTL-SDR.')
    p2.set_defaults(record=True)

    return p


def run(args):
    info = config.read_cfg_file(args.cfg_file, args.cfg_dir)

    if (info is None):
        return

    bindir = os.path.join(args.cfg_dir, "usr", "bin")

    pipe_size_bytes = int(args.pipe_size * (2**20))
    if (not _tune_max_pipe_size(pipe_size_bytes)):
        return

    if (not _check_apps((args.no_tsp or args.record), bindir)):
        print("\nTo install software dependencies, run:")
        print("""
        blocksat-cli deps install
        """)
        return

    # Demodulator configs
    l_band_freq = info['freqs']['l_band']*1e6
    modcod      = defs.low_rate_modcod if args.modcod == "low" else \
                  defs.high_rate_modcod
    sym_rate    = defs.sym_rate[info['sat']['alias']]
    samp_rate   = args.sps*sym_rate

    assert(samp_rate < 2.4e6), \
        "Sample rate of {} exceeds the RTL-SDR limit".format(samp_rate)

    # Derotate up to the CFO recovery range on leandvb. If the desired
    # derotation exceeds the CFO correction range, change the L-band frequency
    # directly on the RTL instead.
    cfo_corr_range = (sym_rate / 4)
    derotate       = args.derotate*1e3
    while (derotate > cfo_corr_range):
        derotate    -= cfo_corr_range
        l_band_freq += cfo_corr_range
    while (derotate < -cfo_corr_range):
        derotate    += cfo_corr_range
        l_band_freq -= cfo_corr_range

    if (args.iq_file is None or args.record):
        rtl_cmd = ["rtl_sdr", "-g", str(args.gain), "-f",
                   str(l_band_freq), "-s", str(samp_rate)]
        if (args.record):
            bytes_per_sec = (2*samp_rate)/(2**20)
            print("IQ recording will be saved on file {}".format(
                args.iq_file))
            print(textwrap.fill("NOTE: the file will grow by approximately "
                                "{} MB per second.".format(bytes_per_sec)))
            if (not util._ask_yes_or_no("Proceed?", default="y")):
                return
            rtl_cmd.append(args.iq_file)
        else:
            rtl_cmd.append("-")

    ldvb_path = os.path.join(bindir, "leandvb")
    ldvb_cmd  = [ldvb_path, "--nhelpers", str(args.n_helpers), "-f",
                str(samp_rate), "--sr", str(sym_rate), "--roll-off",
                str(defs.rolloff), "--standard", "DVB-S2", "--sampler", "rrc",
                "--rrc-rej", str(args.rrc_rej), "--modcods", modcod,
                "--framesizes", str(args.framesizes), "--inpipe",
                str(pipe_size_bytes)]
    if (args.debug_ts == 1):
        ldvb_cmd.append("-d")
    elif (args.debug_ts > 1):
        ldvb_cmd.extend(["-d", "-d"])
    if (args.ldpc_dec == "ext"):
        ldpc_tool_path = os.path.join(bindir, "ldpc_tool")
        ldvb_cmd.extend(["--ldpc-helper", ldpc_tool_path,
                         "--ldpc-iterations", str(args.ldpc_iterations)])
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

    ldvb_stderr = None if (args.debug_ts > 0) else subprocess.DEVNULL

    # Input
    tsp_path = os.path.join(bindir, "tsp")
    tsp_cmd  = [tsp_path, "--realtime", "--buffer-size-mb",
                str(args.buffer_size_mb), "--max-flushed-packets",
                str(args.max_flushed_packets), "--max-input-packets",
                str(args.max_input_packets)]
    # MPEG-TS Analyzer
    if (args.analyze):
        print("MPEG-TS analysis will be saved on file {}".format(
            args.analyze_file))
        if (not util._ask_yes_or_no("Proceed?", default="y")):
            return
        tsp_cmd.extend(["-P", "analyze", "-o", args.analyze_file])
    if (not args.no_bitrate_monitoring):
        # Monitor Bitrate
        tsp_cmd.extend(["-P", "bitrate_monitor", "-p",
                        str(args.bitrate_period), "--min", "0"])
    if (args.monitor_ts):
        # Monitor MPEG TS discontinuities
        tsp_cmd.extend(["-P", "continuity"])

    # MPE plugin
    tsp_cmd.extend(["-P", "mpe", "--pid",
                    "-".join([str(pid) for pid in defs.pids]), "--udp-forward",
                    "--local-address", args.local_address])
    # Output
    tsp_cmd.extend(["-O", "drop"])

    logger.debug("Run:")

    if (args.record):
        p1 = subprocess.Popen(rtl_cmd)
        try:
            p1.communicate()
        except KeyboardInterrupt:
            p1.kill()
        return
    elif (args.iq_file is None):
        full_cmd  = "> " + " ".join(rtl_cmd) + " | \\\n" + \
                    " ".join(ldvb_cmd)
        p1 = subprocess.Popen(rtl_cmd, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(ldvb_cmd, stdin=p1.stdout, stdout=subprocess.PIPE,
                              stderr=ldvb_stderr)
    else:
        full_cmd   = "> " + " ".join(ldvb_cmd) + " < " + args.iq_file
        fd_iq_file = open(args.iq_file)
        p2 = subprocess.Popen(ldvb_cmd, stdin=fd_iq_file,
                              stdout=subprocess.PIPE,
                              stderr=ldvb_stderr)
    if (not args.no_tsp):
        full_cmd += " | \\\n" + " ".join(tsp_cmd)
        logger.debug(full_cmd)
        p3 = subprocess.Popen(tsp_cmd, stdin=p2.stdout)
        try:
            p3.communicate()
        except KeyboardInterrupt:
            p3.kill()
            p2.kill()
            p1.kill()
    else:
        logger.debug(full_cmd)
        try:
            p2.communicate()
        except KeyboardInterrupt:
            p2.kill()
            p1.kill()


