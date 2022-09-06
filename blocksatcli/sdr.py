"""SDR Receiver Wrapper"""
import json
import logging
import subprocess
import sys
import textwrap
import threading
import time
from argparse import ArgumentDefaultsHelpFormatter
from shutil import which

import requests

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

        if (not util.ask_yes_or_no("Is that OK?", default="y")):
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
    # If debugging the demodulator, don't echo the logs to stdout, otherwise
    # the logs get mixed on the console and it becomes hard to read them.
    # Similarly, don't echo the logs if outputting the MPEG-TS to stdout,
    # otherwise the logs would be mixed with the TS bytes.
    no_echo = args.debug_demod > 0 or args.no_tsp

    # Force scrolling logs if tsp is configured to print to stdout
    scrolling = tsp.prints_to_stdout(args) or args.log_scrolling

    return monitoring.Monitor(args.cfg_dir,
                              logfile=args.log_file,
                              scroll=scrolling,
                              echo=(not no_echo),
                              min_interval=args.log_interval,
                              server=args.monitoring_server,
                              port=args.monitoring_port,
                              report=args.report,
                              report_opts=monitoring.get_report_opts(args),
                              utc=args.utc)


def _monitor_leandvb(info_pipe, monitor):
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


def _monitor_grdvbs2rx(monitor):
    """Monitor gr-dvbs2rx's demodulator information

    Args:
        monitor : Object of the Monitor class used to handle receiver
                  monitoring and logging

    """
    mon_server_url = "http://localhost:9004"
    while True:
        time.sleep(1)

        try:
            rv = requests.get(mon_server_url)
        except requests.exceptions.ConnectionError:
            continue

        try:
            json_resp = rv.json()
        except json.decoder.JSONDecodeError:
            continue

        status = {'lock': (json_resp['lock'], None)}
        if json_resp['snr'] is not None:
            status['snr'] = (json_resp['snr'], 'dB')
        if json_resp['fec']['fer'] is not None:
            status['fer'] = (json_resp['fec']['fer'], None)
        if json_resp['mpeg-ts']['per'] is not None:
            status['per'] = (json_resp['mpeg-ts']['per'], None)
            status['pkt_err'] = (int(json_resp['mpeg-ts']['per'] *
                                     json_resp['mpeg-ts']['packets']), None)
        monitor.update(status)


def _stringify_cmd(cmd):
    return [str(x) for x in cmd]


def _get_rtl_sdr_cmd(args, l_band_freq, samp_rate, output='-'):
    cmd = [
        "rtl_sdr", "-g", args.gain, "-f", l_band_freq, "-s", samp_rate, "-d",
        args.rtl_idx, output
    ]
    return _stringify_cmd(cmd)


def _get_leandvb_cmd(args, samp_rate, sym_rate, pipe_size_bytes, derotate,
                     spec_inversion):
    if spec_inversion:
        logger.warning("Leandvb does not support spectrum inversion")

    modcod = str(2**defs.modcods[args.modcod])  # bit mask

    cmd = [
        "leandvb", "--nhelpers", args.n_helpers, "-f", samp_rate, "--sr",
        sym_rate, "--roll-off", defs.rolloff, "--standard", "DVB-S2",
        "--sampler", "rrc", "--rrc-rej", args.rrc_rej, "--modcods", modcod,
        "--framesizes", 1 if defs.fecframe_size == 'normal' else 2
    ]
    if (args.iq_file is None):
        cmd.extend(["--inpipe", pipe_size_bytes])
    if (args.debug_demod > 0):
        cmd.extend(("-d " * args.debug_demod).split())
    if (args.ldpc_dec == "ext"):
        cmd.extend([
            "--ldpc-helper",
            which("ldpc_tool"), "--ldpc-iterations", args.ldpc_iterations
        ])
    else:
        cmd.extend(["--ldpc-bf", args.ldpc_bf])
    if (args.gui):
        cmd.append("--gui")
    if (args.verbose):
        cmd.append("-v")
    if (args.fastlock):
        cmd.append("--fastlock")
    if (derotate != 0.0):
        cmd.extend(["--derotate", int(derotate)])

    if args.leandvb_opts is not None:
        cmd.extend(args.leandvb_opts.split(","))

    # The command to be printed on a debug log (so that the user can replicate
    # the subprocess cascading on a shell) excludes the --fd-info option below.
    # Otherwise, the user would need to open the descriptor manually.
    print_cmd = cmd.copy()

    # Create unnamed pipe to receive real-time demodulation information from
    # leandvb (via --fd-info). Collect this information on a daemon thread.
    if (args.iq_file is None):
        info_pipe = util.Pipe()
        cmd.extend(["--fd-info", info_pipe.w_fd])
        monitor = _get_monitor(args)
        t = threading.Thread(target=_monitor_leandvb,
                             args=(info_pipe, monitor),
                             daemon=True)
        t.start()
    else:
        info_pipe = None

    return _stringify_cmd(cmd), info_pipe, _stringify_cmd(print_cmd)


def _get_grdvbs2rx_app_cmd(args, l_band_freq, samp_rate, sym_rate,
                           spec_inversion):
    cmd = ['dvbs2-rx']

    if args.iq_file is not None:
        cmd.extend([
            '--source', 'file', '--in-file', args.iq_file, '--in-iq-format',
            'u8'
        ])
    else:
        cmd.extend([
            '--source', 'rtl', '--rtl-idx', args.rtl_idx, '--rtl-gain',
            args.gain
        ])

    out_pipe = util.Pipe()

    cmd.extend([
        '--out-fd', out_pipe.w_fd, '--freq', l_band_freq, '--samp-rate',
        samp_rate, '--sym-rate', sym_rate, '--rolloff', defs.rolloff,
        '--modcod', args.modcod, '--frame-size', defs.fecframe_size,
        '--pilots', 'on' if defs.pilots else 'off', '--ldpc-iterations',
        args.ldpc_iterations
    ])

    if spec_inversion:
        cmd.append('--spectral-inversion')

    if (args.debug_demod > 0):
        cmd.extend(["-d", args.debug_demod])
        cmd.extend(['--log-stats', '--log-period', 10])

    if (args.gui):
        cmd.append("--gui")

    if args.dvbs2rx_opts is not None:
        cmd.extend(args.dvbs2rx_opts.split(","))

    if (args.iq_file is None):
        cmd.append('--mon-server')
        monitor = _get_monitor(args)
        t = threading.Thread(target=_monitor_grdvbs2rx,
                             args=(monitor, ),
                             daemon=True)
        t.start()

    return _stringify_cmd(cmd), out_pipe


def _record_iq_samples(args, l_band_freq, samp_rate):
    mb_per_sec = (2 * samp_rate) / (2**20)
    logger.info("IQ recording will be saved on file {}".format(args.iq_file))
    logger.info(
        "The file will grow by approximately {:.2f} MB per second.".format(
            mb_per_sec))
    if (not util.ask_yes_or_no("Proceed?", default="y")):
        return

    rtl_cmd = _get_rtl_sdr_cmd(args, l_band_freq, samp_rate, args.iq_file)
    logger.debug("> " + " ".join(rtl_cmd))

    p1 = subprocess.Popen(rtl_cmd)
    try:
        p1.wait()
    except KeyboardInterrupt:
        p1.kill()


def subparser(subparsers):  # pragma: no cover
    """Parser for sdr command"""
    default_impl = 'leandvb' if which('dvbs2-rx') is None else 'gr-dvbs2rx'

    p = subparsers.add_parser('sdr',
                              description="Launch SDR receiver",
                              help='Launch SDR receiver',
                              formatter_class=ArgumentDefaultsHelpFormatter)

    # Monitoring options
    monitoring.add_to_parser(p)

    rtl_p = p.add_argument_group('RTL-SDR options')
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

    demod_p = p.add_argument_group('Demodulator options')
    demod_p.add_argument('--implementation',
                         '--impl',
                         choices=['leandvb', 'gr-dvbs2rx'],
                         default=default_impl,
                         help='Software-defined demodulator implementation')
    demod_p.add_argument(
        '-d',
        '--debug-demod',
        action='count',
        default=0,
        help="Debug the software-defined DVB-S2 demodulator. Use it multiple "
        "times to increase the debugging level")
    demod_p.add_argument('--gui',
                         default=False,
                         action='store_true',
                         help='GUI mode')
    # If the derotate option is within the correctable range (+-sym_rate/4),
    # the leandvb implementation applies the manual correction but the
    # gr-dvbs2rx does not. There is no need to apply a manual correction with
    # gr-dvbs2rx. In contrast, if the derotation exceeds the correctable range,
    # the L-band center frequency changes, in which case both leandvb and
    # gr-dvbs2rx are affected.
    demod_p.add_argument('--derotate',
                         default=0,
                         type=float,
                         help='Frequency offset correction to apply in kHz')
    demod_p.add_argument('-m',
                         '--modcod',
                         choices=defs.modcods.keys(),
                         default='qpsk3/5',
                         metavar='',
                         help="DVB-S2 modulation and coding (MODCOD) scheme. "
                         "Choose from: " + ", ".join(defs.modcods.keys()))
    demod_p.add_argument(
        '--ldpc-iterations',
        default=25,
        help='Max number of iterations used by leandvb\'s external '
        'LDPC decoder or gr-dvbs2rx\'s default LDPC decoder')

    ldvb_p = p.add_argument_group('leandvb options')
    ldvb_p.add_argument(
        '-n',
        '--n-helpers',
        default=6,
        type=int,
        help='Number of instances of the external LDPC decoder \
                        to spawn as child processes')
    ldvb_p.add_argument('-v',
                        '--verbose',
                        default=False,
                        action='store_true',
                        help='leandvb in verbose mode')
    ldvb_p.add_argument('--fastlock',
                        default=False,
                        action='store_true',
                        help='leandvb fast lock mode')
    ldvb_p.add_argument('--rrc-rej',
                        default=30,
                        type=int,
                        help='leandvb RRC rej parameter')
    ldvb_p.add_argument('--ldpc-dec',
                        default="ext",
                        choices=["int", "ext"],
                        help="LDPC decoder to use (internal or external)")
    ldvb_p.add_argument('--ldpc-bf',
                        default=100,
                        help='Max number of iterations used by the internal \
                        LDPC decoder')
    ldvb_p.add_argument('--pipe-size',
                        default=32,
                        type=int,
                        help='Size in MBytes of the input pipe file read by \
                        leandvb')
    ldvb_p.add_argument(
        '--leandvb-opts',
        type=str,
        help="Comma-separated list of extra options to pass into leandvb")

    gr_p = p.add_argument_group('gr-dvbs2rx options')
    gr_p.add_argument(
        '--dvbs2rx-opts',
        type=str,
        help="Comma-separated list of extra options to pass into dvbs2-rx")

    # TSDuck Options
    tsp_p = tsp.add_to_parser(p)
    tsp_p.add_argument(
        '--no-tsp',
        default=False,
        action='store_true',
        help='Feed the demodulator output to stdout instead of tsp')

    p.set_defaults(func=run, record=False)

    subsubparsers = p.add_subparsers(title='subcommands',
                                     help='Target sub-command')
    # IQ recording
    p2 = subsubparsers.add_parser(
        'rec',
        aliases=['record'],
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

    util.check_configured_setup_type(info, defs.sdr_setup_type, logger)

    if args.implementation == 'leandvb':
        pipe_size_bytes = int(args.pipe_size * (2**20))
        if (not _tune_max_pipe_size(pipe_size_bytes)):
            return

    # Check if all dependencies are installed
    apps = ["rtl_sdr"]
    if not args.record:
        if args.implementation == 'leandvb':
            apps.extend(["leandvb", "ldpc_tool"])
        else:
            apps.extend(["dvbs2-rx"])
    if not args.no_tsp:
        apps.append("tsp")
    if (not dependencies.check_apps(apps)):
        return

    # Receiver configs
    spec_inversion = info['freqs']['lo'] > info['freqs']['dl']
    l_band_freq = info['freqs']['l_band'] * 1e6
    sym_rate = defs.sym_rate[info['sat']['alias']]
    samp_rate = args.sps * sym_rate

    assert (samp_rate < 2.4e6), \
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

    # If recording IQ samples, run the rtl_sdr only
    if (args.record):
        _record_iq_samples(args, l_band_freq, samp_rate)
        return

    # Prepare and validate the tsp command
    tsp_handler = tsp.Tsp()
    if (not tsp_handler.gen_cmd(args)):
        return

    logger.debug("Run:")

    if args.implementation == 'leandvb':
        ldvb_cmd, info_pipe, ldvb_cmd_for_print = _get_leandvb_cmd(
            args, samp_rate, sym_rate, pipe_size_bytes, derotate,
            spec_inversion)
        ldvb_stdout = None if args.no_tsp else subprocess.PIPE
        ldvb_stderr = None if (args.debug_demod > 0) else subprocess.DEVNULL
        if (args.iq_file is None):
            rtl_cmd = _get_rtl_sdr_cmd(args, l_band_freq, samp_rate)
            full_cmd = "> " + " ".join(rtl_cmd) + " | \\\n" + \
                " ".join(ldvb_cmd_for_print)
            rtl_proc = subprocess.Popen(rtl_cmd, stdout=subprocess.PIPE)
            ldvb_proc = subprocess.Popen(ldvb_cmd,
                                         stdin=rtl_proc.stdout,
                                         stdout=ldvb_stdout,
                                         stderr=ldvb_stderr,
                                         pass_fds=[info_pipe.w_fd])
            procs = [{
                'handler': rtl_proc,
                'wait': True
            }, {
                'handler': ldvb_proc,
                'wait': True
            }]
        else:
            full_cmd = "> " + " ".join(ldvb_cmd_for_print) + \
                " < " + args.iq_file
            fd_iq_file = open(args.iq_file, 'rb')
            ldvb_proc = subprocess.Popen(ldvb_cmd,
                                         stdin=fd_iq_file,
                                         stdout=ldvb_stdout,
                                         stderr=ldvb_stderr)
            procs = [{'handler': ldvb_proc, 'wait': True}]
        tsp_in_fd = ldvb_proc.stdout
    else:
        dvbs2rx_cmd, out_pipe = _get_grdvbs2rx_app_cmd(args, l_band_freq,
                                                       samp_rate, sym_rate,
                                                       spec_inversion)
        full_cmd = "> " + " ".join(dvbs2rx_cmd) + " {}>&1 1>&2".format(
            out_pipe.w_fd)
        # The MPEG-TS output from gr-dvbs2rx is always redirected to the
        # out_pipe named pipe. With that, only the logs remain on stdout, and
        # by default these logs are omitted (redirected to /dev/null). However,
        # when debugging the demodulator, the logs are not omitted. In this
        # case, normally they would go to stdout, but that doesn't work with
        # the --no-tsp option, when the TS output is the one that must go to
        # stdout. Hence, when no_tsp=True, the original stdout (with the logs)
        # is redirected to stderr, while the out_pipe output is redirected to
        # the parent application's stdout via a cat command. The descriptor
        # connections are summarized below:
        #
        # When the output goes to tsp (no_tsp=False):
        #   - mpeg-ts output -> out_pipe write fd
        #   - stdout -> /dev/null or stdout if debugging
        #   - stderr -> stderr
        #   - out_pipe read fd -> tsp
        #
        # When the output must go to stdout (no_tsp=True):
        #   - mpeg-ts output -> out_pipe write fd
        #   - stdout -> /dev/null or stderr if debugging
        #   - stderr -> stderr
        #   - out_pipe read fd -> stdout
        if args.debug_demod == 0:
            stdout = subprocess.DEVNULL
        else:
            stdout = sys.stderr if args.no_tsp else None
        rx_proc = subprocess.Popen(dvbs2rx_cmd,
                                   stdout=stdout,
                                   pass_fds=[out_pipe.w_fd])
        procs = [{'handler': rx_proc, 'wait': True}]
        tsp_in_fd = out_pipe.r_fd
        if (args.no_tsp):
            cat_proc = subprocess.Popen(['cat'], stdin=tsp_in_fd)
            procs.append({'handler': cat_proc, 'wait': False})
            # Don't wait on cat because its stdin never closes, so it would be
            # on forever and the parent program would hang.

    if (not args.no_tsp):
        full_cmd += " | \\\n" + " ".join(tsp_handler.cmd)
        if (args.ts_dump):
            tsdump_cmd = ['tsdump']
            tsdump_cmd.extend(tsp_handler.ts_dump_opts)
            full_cmd += " | \\\n" + " ".join(tsdump_cmd)
        tsp_handler.run(stdin=tsp_in_fd)
        procs.append({
            'handler': tsp_handler.proc,
            'wait': False,
            'poll': True
        })
        # Don't wait on the tsp process to avoid hanging, but do check that it
        # is running.

    logger.debug(full_cmd)

    for this_proc in procs:
        try:
            if 'poll' in this_proc and this_proc['poll'] and \
                    this_proc['handler'].poll() is not None:
                for other_proc in procs:
                    other_proc['handler'].kill()
                break
            if this_proc['wait']:
                this_proc['handler'].wait()
        except KeyboardInterrupt:
            for other_proc in procs:
                other_proc['handler'].kill()

    print()
