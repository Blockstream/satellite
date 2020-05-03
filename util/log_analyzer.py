#!/usr/bin/env python3
import logging, sys, os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from datetime import datetime
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter


def _get_time(log):
    tstamp = log[:19]
    return datetime.strptime(tstamp, "%Y-%m-%d %H:%M:%S")


def _parse_dvb(log, start_time):
    """Parse logs acquired via blocksat-cli usb"""
    if ("Signal" not in log):
        return
    d           = {}
    elements    = log.split()
    n_elem      = len(elements)
    log_time    = _get_time(log)
    d['date']   = log_time
    d['time']   = (log_time - start_time).total_seconds()
    d['locked'] = "Lock" in log
    for i, elem in enumerate(elements):
        if (elem[-1] == "=" and (i+1) <= n_elem):
            key = elem[:-1]
            raw = elements[i+1]
            if ("^" in raw):
                val = float(raw.replace("x10^","e").replace(",","."))
            elif ("%" in raw):
                key += "%"
                val = float(raw[:-1].replace(",","."))
            elif (raw[-2:] == "dB"):
                val = float(raw[:-2].replace(",","."))
                key += "_dB"
            elif (raw[-3:] == "dBm"):
                val = float(raw[:-3].replace(",","."))
                key += "_dBm"
            else:
                val = float(raw.replace(",", "."))

            d[key] = val
    return d


def _parse_iperf(log):
    """Parse iperf logs acquired in extended mode"""
    log = log.replace("/   ", "/").replace("/  ", "/").replace("/ ", "/")
    d = {}
    elements = log.split()
    if ("sec" not in log or "SUM" in log or "out-of-order" in log):
        return

    interval = elements[2]

    s_time   = float(interval.split("-")[0])

    transfer = float(elements[4])
    if (elements[5] == "MBytes"):
        transfer *= 1e6
    elif (elements[5] == "KBytes"):
        transfer *= 1e3
    elif (elements[5] == "Bytes"):
        pass
    else:
        raise ValueError("Unknown unit {}".format(elements[5]))

    bw = float(elements[6])
    if (elements[7] == "Mbits/sec"):
        bw *= 1e6
    elif (elements[7] == "Kbits/sec"):
        bw *= 1e3
    elif (elements[7] == "bits/sec"):
        pass
    else:
        raise ValueError("Unknown unit {}".format(elements[7]))

    jitter_ms  = float(elements[8])
    assert(elements[9] == "ms")

    lost_pkts  = int(elements[10].split("/")[0])
    total_pkts = int(elements[10].split("/")[1])

    latency = elements[12].split("/") # avg/min/max/stdev
    assert(len(latency) == 4)
    assert(elements[13] == "ms"), "error {}".format(log)
    if (elements[12] != "-/-/-/-"):
        try:
            latency = [float(x) for x in latency]
        except ValueError:
            print(latency)
        d['latency_ms'] = latency

    pps = int(elements[14])

    d['time']           = s_time
    d['stream_id']      = log[3]
    d['transfer_bytes'] = transfer
    d['bw_kbps']        = bw/1e3
    d['jitter_ms']      = jitter_ms
    d['lost_pkts']      = lost_pkts
    d['total_pkts']     = total_pkts
    d['pps']            = pps

    return d


def _plot_dvb(ds, ds_name):
    keys = list(ds[0].keys())
    keys.remove("time")
    keys.remove("date")

    formatter = DateFormatter('%H:%M')

    path = os.path.join("figs", ds_name)
    if not os.path.isdir(path):
        os.makedirs(path)

    for key in keys:
        print("Plotting {}".format(key))
        x = [r[key] for r in ds if key in r]
        t = [r["date"] for r in ds if key in r]
        n = os.path.join(path, "dvb-" + key.replace("/","_") + ".png")
        if "_" in key:
            kelems = key.split("_")
            ylabel = "{} ({})".format(kelems[0], kelems[1])
        elif key[-1] == "%":
            ylabel = "{} %".format(key[:-1])
        else:
            ylabel = key
        fig, ax = plt.subplots()
        plt.plot_date(t, x, ms=1)
        plt.ylabel(ylabel)
        plt.xlabel("Time")
        if (key == "postBER"):
            ax.set_yscale('log')
        plt.grid()
        ax.xaxis.set_major_formatter(formatter)
        ax.xaxis.set_tick_params(rotation=30, labelsize=10)
        plt.tight_layout()
        plt.savefig(n, dpi=300)
        plt.close()


def _plot_iperf(ds, ds_name, stream_ids, stream_labels):
    keys = list(ds[0].keys())
    keys.remove("time")
    keys.remove("stream_id")
    log_keys = ["lost_pkts", "total_pkts", "latency_ms", "pps"]

    path = os.path.join("figs", ds_name)
    if not os.path.isdir(path):
        os.makedirs(path)

    for key in keys:
        print("Plotting {}".format(key))
        n = os.path.join(path, "iperf-" + key.replace("/","_") + ".png")
        if key == "lost_pkts":
            ylabel = "Loss (packets)"
        elif key == "total_pkts":
            ylabel = "Total (packets)"
        elif key == "pps":
            ylabel = "Packets per Second"
        elif "_" in key:
            kelems = key.split("_")
            if kelems[0] == "bw":
                kelems[0] = "Throughput"
            ylabel = "{} ({})".format(kelems[0].title(), kelems[1])
        else:
            ylabel = key
        fig, ax = plt.subplots()
        for stream, s_label in zip(stream_ids, stream_labels):
            t = [r["time"]/3600 for r in ds if key in r and
                 r['stream_id'] == stream]
            if (key == "latency_ms"):
                metrics = ["avg", "min", "max", "stdev"]
                for idx, metric in enumerate(metrics[:-1]): # ignore stdev
                    x = [r[key][idx] for r in ds if key in r and
                         r['stream_id'] == stream]
                    plt.plot(t, x, ms=1,
                             marker='o', linestyle='None',
                             label="{} - {}".format(metric, s_label))
            else:
                x = [r[key] for r in ds if key in r and
                     r['stream_id'] == stream]
                plt.plot(t, x, marker='o', linestyle='None',
                         label="{}".format(s_label), ms=1)

        plt.ylabel(ylabel)
        plt.xlabel("Time (h)")
        if (key in log_keys):
            ax.set_yscale('log')
        plt.grid()
        plt.legend()
        plt.tight_layout()
        plt.savefig(n, dpi=300)
        plt.close()


def _analyze_usb(logs, ds_name):
    start_time = _get_time(logs[0])
    ds = list()
    for log in logs:
        logging.debug(log)
        res = _parse_dvb(log, start_time)
        logging.info(res)
        if (res is not None):
            ds.append(res)
    _plot_dvb(ds, ds_name)


def _analyze_iperf(logs, ds_name):
    ds = list()
    stream_ids = set()
    for log in logs:
        logging.debug(log)
        res = _parse_iperf(log)
        logging.info(res)
        if (res is not None):
            ds.append(res)
            stream_ids.add(res['stream_id'])

    # Find QPSK stream
    stream_ids = list(stream_ids)
    assert(len(stream_ids) <= 2)
    first_qpsk = all([r["bw_kbps"] < 200e3 for r in ds if "bw_kbps" in r and
                      r['stream_id'] == stream_ids[0]])
    stream_labels = ["QPSK 1/3", "8PSK 2/3"] if first_qpsk else \
                    ["8PSK 2/3", "QPSK 1/3"]

    _plot_iperf(ds, ds_name, stream_ids, stream_labels)


def _read_log_file(filename):
    with open(filename) as fd:
        logs = fd.read()

    return logs.splitlines()


def parser():
    parser = ArgumentParser(prog="log_analyzer",
                            description="Analyze blocksat logs",
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('file',
                        help="Log file")
    parser.add_argument('-a', '--analysis',
                        default="usb",
                        choices=["usb", "iperf"],
                        help="Target analysis")
    parser.add_argument('--verbose', '-v',
                        action='count',
                        default=1,
                        help="Verbosity (logging) level")
    return parser.parse_args()


def main():
    args = parser()

    logging_level = 70 - (10 * args.verbose) if args.verbose > 0 else 0
    logging.basicConfig(stream=sys.stderr, level=logging_level)

    logs    = _read_log_file(args.file)
    logname = os.path.splitext(os.path.basename(args.file))[0]

    if (args.analysis == "usb"):
        _analyze_usb(logs, logname)
    else:
        _analyze_iperf(logs, logname)


if __name__ == '__main__':
    main()
