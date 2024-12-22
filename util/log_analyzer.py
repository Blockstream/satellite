#!/usr/bin/env python3
import logging
import os
import re
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

matplotlib.use('agg')
plt.style.use('seaborn')
logger = logging.getLogger(__name__)


def _get_time(log):
    """Parse timestamp from log line"""
    tstamp = log[:19]
    return datetime.strptime(tstamp, "%Y-%m-%d %H:%M:%S")


def _parse(log, start_time):
    """Parse logs in the format from monitor.py

    Args:
        log        : String containing the logged line.
        start_time : Log file's starting time.

    Returns:
        Dictionary with the receiver metrics.

    """
    log_time = _get_time(log)
    info = {'date': log_time, 'time': (log_time - start_time).total_seconds()}
    for entry in log[19:-1].split(";"):
        key, val = entry.split("=")
        key = key.strip()
        val = val.strip()

        if (key == "Lock"):
            val = "Locked" if val == "True" else "Unlocked"  # categorial plot
        elif (key == "Level" or key == "SNR"):
            unit = re.sub('[0-9.-]', '', val)
            val = val.replace(unit, '')
            # The logs from the S400 could return NaN, in which case "val" is
            # empty here. Skip these values.
            if (val == ''):
                continue
            val = float(val)
        elif (key == "BER" or key == "Packet Errors"):
            val = float(val)
        else:
            raise ValueError("Unknown key")

        info[key] = val

    return info


def _plot(ds, ds_name):
    """Plot all results from list of dictionaries

    Args:
        ds      : Dataset (list of dictionaries)
        ds_name : Dataset name

    """
    keys = set()
    for elem in ds:
        keys.update(list(ds[0].keys()))
    keys.remove("time")
    keys.remove("date")

    formatter = DateFormatter('%m/%d %H:%M')

    path = os.path.join("figs", ds_name)
    if not os.path.isdir(path):
        os.makedirs(path)

    for key in keys:
        logger.info("Plotting {}".format(key))

        x = [r[key] for r in ds if key in r]
        t = [r["date"] for r in ds if key in r]

        # Add unit to y-label
        if (key == "SNR"):
            ylabel = "SNR (dB)"
        elif (key == "Level"):
            ylabel = "Signal Level"
            # NOTE: the SDR logs positive signal levels rather than dBm.
            if (all([val < 0 for val in x])):
                ylabel += " (dBm)"
        else:
            ylabel = key

        fig, ax = plt.subplots()
        plt.plot_date(t, x, ms=2)
        plt.ylabel(ylabel)
        plt.xlabel("Time (UTC)")

        # Plot BER in log scale as it is not zero throughout the acquisition
        if (key == "BER" and any([val > 0 for val in x])):
            ax.set_yscale('log')

        ax.xaxis.set_major_formatter(formatter)
        ax.xaxis.set_tick_params(rotation=30, labelsize=10)
        plt.tight_layout()

        savepath = os.path.join(path, key.replace("/", "_").lower() + ".png")
        plt.savefig(savepath, dpi=300)
        plt.close()


def _analyze(logs, ds_name):
    """Parse and plot receiver metrics"""
    start_time = _get_time(logs[0])
    ds = list()
    for log in logs:
        logger.debug(log)
        res = _parse(log, start_time)
        logger.debug(res)
        if (res is not None):
            ds.append(res)
    _plot(ds, ds_name)


def _read_log_file(filename):
    with open(filename) as fd:
        logs = fd.read()

    return logs.splitlines()


def parser():  # pragma: no cover
    parser = ArgumentParser(prog="log_analyzer",
                            description="Analyze receiver logs",
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('file', help="Log file")
    parser.add_argument('--verbose',
                        '-v',
                        action='count',
                        default=5,
                        help="Verbosity (logging) level")
    return parser.parse_args()


def main():
    args = parser()

    logging_level = 70 - (10 * args.verbose) if args.verbose > 0 else 0
    logging.basicConfig(level=logging_level,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    logs = _read_log_file(args.file)
    logname = os.path.splitext(os.path.basename(args.file))[0]

    _analyze(logs, logname)


if __name__ == '__main__':
    main()
