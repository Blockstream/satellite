"""Linux USB receiver"""
import json
import logging
import os
import signal
import subprocess
import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pprint import pformat

from . import config, util, defs, rp, firewall, ip, dependencies, monitoring

logger = logging.getLogger(__name__)
runner = util.ProcessRunner(logger)


def _find_v4l_lnb(info):
    """Find suitable LNB within v4l-utils preset LNBs

    The LNBs on list v4l_lnbs are defined at lib/libdvbv5/dvb-sat.c

    """

    target_lo_freq_raw = info['lnb']['lo_freq']
    target_is_universal = info['lnb']['universal']

    if (target_is_universal):
        assert (isinstance(target_lo_freq_raw, list))
        assert (len(target_lo_freq_raw) == 2)
        target_lo_freq = [int(x) for x in target_lo_freq_raw]
    else:
        target_lo_freq = [int(target_lo_freq_raw)]

    # Find options that match the LO freq
    options = list()
    for lnb in defs.v4l_lnbs:
        is_universal_option = 'highfreq' in lnb

        if (target_is_universal and (not is_universal_option)):
            continue

        if (info['lnb']['pol'].lower() == "dual" and  # user has dual-pol LNB
            (
                info['sat']['pol'] == "H" or  # and satellite requires H pol
                (
                    'v1_pointed' in info['lnb'] and info['lnb']['v1_pointed']
                    and info['lnb']['v1_psu_voltage'] >=
                    16  # or LNB already operates with H pol
                )) and "rangeswitch"
                not in lnb):  # but LNB candidate is single-pol
            continue  # not a validate candidate, skip

        if (target_is_universal):
            if (is_universal_option and lnb['lowfreq'] == target_lo_freq[0]
                    and lnb['highfreq'] == target_lo_freq[1]):
                options.append(lnb)
        else:
            if (lnb['lowfreq'] == target_lo_freq[0]):
                options.append(lnb)

    assert (len(options) > 0), "LNB doesn't match a valid option"
    logger.debug("Matching LNB options: {}".format(pformat(options)))

    return options[0]


def _find_adapter(list_only=False, target_model=None):
    """Find the DVB adapter

    Returns:
        Tuple with (adapter index, frontend index)

    """
    if (target_model is None):
        util._print_header("Find DVB Adapter")

    # Search a range of adapters. There is no command to list all adapters, so
    # we try to list each one individually using `dvbnet -a adapter_no -l`.
    adapters = list()
    for a in range(0, 10):
        cmd = ["dvbnet", "-a", str(a), "-l"]
        logger.debug("> " + " ".join(cmd))

        with open(os.devnull, 'w') as devnull:
            res = subprocess.call(cmd, stdout=devnull, stderr=devnull)
            if (res == 0):
                # Try a few frontends too
                for f in range(0, 2):
                    try:
                        output = subprocess.check_output(
                            ["dvb-fe-tool", "-a",
                             str(a), "-f",
                             str(f)])
                        line = output.splitlines()[0].decode().split()
                        adapter = {
                            "adapter":
                            str(a),
                            "frontend":
                            line[5].replace(")", "").split("frontend")[-1],
                            "vendor":
                            line[1],
                            "model":
                            " ".join(line[2:4]),
                            "support":
                            line[4]
                        }
                        adapters.append(adapter)
                        logger.debug(pformat(adapter))
                    except subprocess.CalledProcessError:
                        pass

    # If nothing was obtained using dvbnet, try to inspect dmesg logs
    if (len(adapters) == 0):
        ps = subprocess.Popen("dmesg", stdout=subprocess.PIPE)
        try:
            output = subprocess.check_output(["grep", "frontend"],
                                             stdin=ps.stdout,
                                             stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as grepexc:
            if (grepexc.returncode == 1):
                output = ""
                pass
        ps.wait()

        lines = output.splitlines()
        adapter_set = set()  # use set to filter unique values
        adapters = list()
        for line in lines:
            linesplit = line.decode().split()
            if ("adapter" not in linesplit):
                continue
            i_adapter = linesplit.index('adapter')
            i_frontend = linesplit.index('frontend')
            device = linesplit[i_frontend + 2:]
            adapter = {
                "adapter": linesplit[i_adapter + 1],
                "frontend": linesplit[i_frontend + 1],
                "vendor": device[0][1:],
                "model": " ".join(device[1:-1]),
                "support": device[-1][:-4].replace('(', '').replace(')', '')
            }

            # Maybe the device on dmesg does not exist anymore. Check!
            try:
                cmd = ["dvbnet", "-a", adapter['adapter'], "-l"]
                logger.debug("> " + " ".join(cmd))
                res = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                continue

            # If it exists, add to set of candidate adapters
            adapter_set.add(json.dumps(adapter))

        # Process unique adapter logs
        for adapter in adapter_set:
            adapters.append(json.loads(adapter))
            logger.debug(pformat(json.loads(adapter)))

    dvb_s2_adapters = [a for a in adapters if ("DVB-S/S2" in a["support"])]
    logger.debug(dvb_s2_adapters)

    assert (len(dvb_s2_adapters) > 0), "No DVB-S2 adapters found"

    chosen_adapter = None
    if (target_model is not None):
        # Search without prompting
        for adapter in dvb_s2_adapters:
            if (adapter["model"] == target_model):
                chosen_adapter = adapter
                break
    else:
        # Prompt the user
        for adapter in dvb_s2_adapters:
            print("Found DVB-S2 adapter: %s %s" %
                  (adapter["vendor"], adapter["model"]))

            if (not list_only):
                if (len(dvb_s2_adapters) == 1
                        or util._ask_yes_or_no("Choose adapter?")):
                    chosen_adapter = adapter
                    logger.debug("Chosen adapter:")
                    logger.debug(pformat(adapter))
                    break

    if (list_only):
        return

    if (chosen_adapter is None):
        if (target_model is None):
            err_msg = "Please choose a DVB-S2 adapter"
        else:
            err_msg = "Please choose a valid DVB-S2 adapter"
        raise ValueError(err_msg)

    return chosen_adapter["adapter"], chosen_adapter["frontend"]


def _dvbnet_single(adapter, ifname, pid, ule, existing_dvbnet_interfaces):
    """Start DVB network interface

    Args:
        adapter                    : DVB adapter index
        ifname                     : DVB network interface name
        pid                        : PID to listen to
        ule                        : Whether to use ULE framing
        existing_dvbnet_interfaces : List of dvbnet interfaces already
                                     configured for the adapter

    """

    assert (pid >= 32 and pid <= 8190), "PID not insider range 32 to 8190"

    if (ule):
        encapsulation = 'ULE'
    else:
        encapsulation = 'MPE'

    # Check if the interface already exists
    res = subprocess.call(["ip", "addr", "show", "dev", ifname],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL)
    os_interface_exists = (res == 0)
    matching_dvbnet_if = None

    # When the network interface exists in the OS, we also need to check if the
    # matching dvbnet device is configured according to what we want now
    if (os_interface_exists):
        print("Network interface %s already exists" % (ifname))

        for interface in existing_dvbnet_interfaces:
            if (interface['name'] == ifname):
                matching_dvbnet_if = interface
                break

    # Our indication that interface exists comes from "ip addr show
    # dev". However, it is possible that dvbnet does not have any interface
    # associated to an adapter, so check if we found anything:
    cfg_interface = False
    if (len(existing_dvbnet_interfaces) > 0
            and matching_dvbnet_if is not None):
        # Compare to desired configurations
        if (matching_dvbnet_if['pid'] != pid
                or matching_dvbnet_if['encapsulation'] != encapsulation):
            cfg_interface = True

        if (matching_dvbnet_if['pid'] != pid):
            print("Current PID is %d. Set it to %d" %
                  (matching_dvbnet_if['pid'], pid))

        if (matching_dvbnet_if['encapsulation'] != encapsulation):
            print("Current encapsulation is %s. Set it to %s" %
                  (matching_dvbnet_if['encapsulation'], encapsulation))
    else:
        cfg_interface = True

    # Create interface in case it doesn't exist or needs to be re-created
    if (cfg_interface):
        # If interface exists, but must be re-created, remove the existing one
        # first
        if (os_interface_exists):
            _rm_dvbnet_interface(adapter, ifname, verbose=False)

        ule_arg = "-U" if ule else ""

        if (runner.dry):
            print("Create interface {}:".format(ifname))

        runner.run(["dvbnet", "-a", adapter, "-p",
                    str(pid), ule_arg],
                   root=True)
    else:
        print("Network interface %s already configured correctly" % (ifname))


def _dvbnet(adapter, ifnames, pids, ule=False):
    """Start DVB network interfaces of a DVB adapter

    An adapter can have multiple dvbnet interfaces, one for each PID.

    Args:
        adapter  : DVB adapter index
        ifnames  : list of DVB network interface names
        pids     : List of PIDs to listen to on each interface
        ule      : Whether to use ULE framing

    """
    assert (isinstance(ifnames, list))
    assert (isinstance(pids, list))
    assert(len(ifnames) == len(pids)), \
        "Interface names and PID number must be vectors of the same length"

    # Find the dvbnet interfaces that already exist for the chosen adapter
    existing_dvbnet_iif = _find_dvbnet_interfaces(adapter)

    util._print_header("Network Interface")

    for ifname, pid in zip(ifnames, pids):
        _dvbnet_single(adapter, ifname, pid, ule, existing_dvbnet_iif)


def _find_dvbnet_interfaces(adapter):
    """Find dvbnet interface(s) of a DVB adapter

    An adapter can have multiple dvbnet interfaces, one for each PID.

    Args:
        adapter: Corresponding DVB adapter

    Returns:
        interfaces : List of dvbnet interfaces

    """

    util._print_header("Find dvbnet interface(s)")
    cmd = ["dvbnet", "-a", adapter, "-l"]
    logger.debug("> " + " ".join(cmd))
    res = subprocess.check_output(cmd)

    interfaces = list()
    for line in res.splitlines():
        if ("Found device" in line.decode()):
            line_split = line.decode().split()
            interface = {
                'dev': line_split[2][:-1],
                'name': line_split[4][:-1],
                'pid': int(line_split[8][:-1]),
                'encapsulation': line_split[10]
            }
            logger.debug(pformat(interface))
            interfaces.append(interface)

    if (len(interfaces) == 0):
        print("Could not find any dvbnet interface")

    return interfaces


def _rm_dvbnet_interface(adapter, ifname, verbose=True):
    """Remove DVB net interface

    Args:
        adapter   : Corresponding DVB adapter
        interface : dvbnet interface number
        verbose   : Controls verbosity
    """

    if (verbose):
        util._print_header("Remove dvbnet interface")

    runner.run(["ip", "link", "set", ifname, "down"], root=True)

    if_number = ifname.split("_")[-1]
    runner.run(["dvbnet", "-a", adapter, "-d", if_number], root=True)

    # Remove also the static IP address configuration
    ip.rm_ip(ifname, runner.dry)


def zap(adapter,
        frontend,
        ch_conf_file,
        user_info,
        lnb="UNIVERSAL",
        output=None,
        timeout=None,
        monitor=False):
    """Run zapper

    Args:
        adapter      : DVB adapter index
        frontend     : frontend
        ch_conf_file : Path to channel configurations file
        user_info    : Dictionary with user configurations
        lnb          : LNB type
        output       : Output filename (when recording)
        timeout      : Run the zap for this specified duration
        monitor      : Monitor mode. Monitors DVB traffic stats (throughput and
                       packets per second), but does not deliver data upstream.

    Returns:
        Subprocess object

    """

    util._print_header("Tuning the DVB-S2 Receiver")

    # LNB name to use when calling dvbv5-zap
    if (lnb is None):
        # Find suitable LNB within v4l-utils preset LNBs
        lnb = _find_v4l_lnb(user_info)['alias']

    print("Running dvbv5-zap")
    print("  - Config:   {}".format(ch_conf_file))
    print("  - Adapter:  {}".format(adapter))
    print("  - Frontend: {}".format(frontend))
    print("  - LNB:      {}".format(lnb))

    cmd = [
        "dvbv5-zap", "-c", ch_conf_file, "-a",
        str(adapter), "-f",
        str(frontend), "-l", lnb, "-v"
    ]

    rec_mode = output is not None
    if (rec_mode):
        cmd = cmd + ["-o", output]

        if (os.path.exists(output)):
            print("File %s already exists" % (output))

            # The recording is such that MPEG TS packets are overwritten one by
            # one. For instance, if previous ts file had 1000 MPEG TS packets,
            # when overwriting, the tool would overwrite each packet
            # individually. So if it was stopped for instance after the first
            # 10 MPEG TS packets, only the first 10 would be overwritten, the
            # remaining MPEG TS packets would remain in the ts file.
            #
            # The other option is to remove the ts file completely and start a
            # new one. This way, all previous ts packets are guaranteed to be
            # erased.
            raw_resp = input(
                "Remove and start new (R) or Overwrite (O)? [R/O] ")
            response = raw_resp.lower()

            if (response == "r"):
                os.remove(output)
            elif (response != "o"):
                raise ValueError("Unknown response")

    if (timeout is not None):
        cmd = cmd + ["-t", timeout]

    if (monitor):
        assert(output is None), \
            "Monitor mode does not work if recording (i.e. w/ -r flag)"
        cmd.append("-m")

    cmd.append("blocksat-ch")

    logger.debug("> " + " ".join(cmd))

    # Make sure the locale of dvbv5-zap is set to English. Otherwise, the
    # parser of "_parse_log" would not work.
    new_env = dict(os.environ)
    new_env['LC_ALL'] = 'C'

    if (monitor or rec_mode):
        ps = subprocess.Popen(cmd, env=new_env)
    else:
        ps = subprocess.Popen(cmd,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              env=new_env,
                              universal_newlines=True)
    return ps


def subparser(subparsers):
    """Subparser for usb command"""
    p = subparsers.add_parser('usb',
                              description="USB DVB-S2 receiver manager",
                              help='Manage Linux USB DVB-S2 receiver',
                              formatter_class=ArgumentDefaultsHelpFormatter)

    # Common parameters
    p.add_argument('-a',
                   '--adapter',
                   default=None,
                   help='DVB-S2 adapter number or model')

    p.add_argument('-f',
                   '--frontend',
                   default=None,
                   help='DVB-S2 adapter\'s frontend number')

    p.set_defaults(func=print_help)

    subsubparsers = p.add_subparsers(title='subcommands',
                                     help='Target sub-command')

    # Launch
    p1 = subsubparsers.add_parser(
        'launch',
        description="Launch a USB DVB-S2 receiver",
        help='Launch a Linux USB DVB-S2 receiver',
        formatter_class=ArgumentDefaultsHelpFormatter)

    p1.add_argument(
        '-l',
        '--lnb',
        choices=defs.lnb_options,
        default=None,
        metavar='',
        help="LNB being used. If not specified, it will be defined "
        "automatically. Choose from the following LNBs supported "
        "by v4l-utils: " + ", ".join(defs.lnb_options))

    p1.add_argument('-r',
                    '--record-file',
                    default=None,
                    help='Record MPEG-TS traffic into a target file')

    p1.add_argument('-t',
                    '--timeout',
                    default=None,
                    help='Stop zapping after a timeout in seconds - useful to \
                    control recording time')

    p1.add_argument('-m',
                    '--monitor',
                    default=False,
                    action='store_true',
                    help='Launch dvbv5-zap in monitor mode to debug MPEG TS '
                    'packet and bit rates')

    monitoring.add_to_parser(p1)

    p1.set_defaults(func=launch)

    # Initial configurations
    p2 = subsubparsers.add_parser(
        'config',
        aliases=['cfg'],
        description='Initial configurations',
        help='Configure DVB-S2 interface(s) and\
                                  the host',
        formatter_class=ArgumentDefaultsHelpFormatter)
    p2.add_argument('-U',
                    '--ule',
                    default=False,
                    action='store_true',
                    help='Use ULE encapsulation instead of MPE')

    p2.add_argument('--skip-rp',
                    default=False,
                    action='store_true',
                    help='Skip settting of reverse path filters')

    p2.add_argument('--skip-firewall',
                    default=False,
                    action='store_true',
                    help='Skip configuration of firewall rules')

    p2.add_argument('--pid',
                    default=defs.pids,
                    type=int,
                    nargs='+',
                    help='List of PIDs to be listened to by dvbnet')

    p2.add_argument('-i',
                    '--ip',
                    default=None,
                    nargs='+',
                    help='IP address set for each DVB-S2 net \
                    interface with subnet mask in CIDR notation')

    p2.add_argument('-y',
                    '--yes',
                    default=False,
                    action='store_true',
                    help="Default to answering Yes to configuration prompts")

    p2.add_argument("--dry-run",
                    action='store_true',
                    default=False,
                    help="Print all commands but do not execute them")

    p2.set_defaults(func=usb_config)

    # Find adapter sub-command
    p3 = subsubparsers.add_parser(
        'list',
        aliases=['ls'],
        description="List DVB-S2 adapters",
        help='List DVB-S2 adapters',
        formatter_class=ArgumentDefaultsHelpFormatter)
    p3.set_defaults(func=list_subcommand)

    # Remove adapter sub-command
    p4 = subsubparsers.add_parser(
        'remove',
        aliases=['rm'],
        description="Remove DVB-S2 adapter",
        help='Remove DVB-S2 adapter',
        formatter_class=ArgumentDefaultsHelpFormatter)
    p4.add_argument('--all',
                    default=False,
                    action='store_true',
                    help='Remove all dvbnet interfaces associated with the '
                    'adapter')
    p4.add_argument("--dry-run",
                    action='store_true',
                    default=False,
                    help="Print all commands but do not execute them")
    p4.set_defaults(func=rm_subcommand)

    return p


def _common(args):
    # User info
    user_info = config.read_cfg_file(args.cfg, args.cfg_dir)

    if (user_info is None):
        return

    # Check if dvbnet is available before trying to find the adapter
    if (not dependencies.check_apps(["dvbnet", "dvb-fe-tool"])):
        return

    # Find adapter
    if (args.adapter is None):
        adapter, frontend = _find_adapter()
    else:
        if (args.adapter.isdigit()):
            # Assume argument --adapter has the adapter number. In this case,
            # --frontend is also required.
            if (args.frontend is None):
                raise ValueError("argument --adapter requires --frontend.")
            adapter = args.adapter
            frontend = args.frontend
        else:
            # Assume argument --adapter has the target model
            adapter, frontend = _find_adapter(target_model=args.adapter)

    # Cache the adapter number on the local config file so that other modules
    # can read the adapter number directly. Rewrite the info every time, as the
    # adapter number could change between boots.
    user_info['setup']['adapter'] = adapter
    config.write_cfg_file(args.cfg, args.cfg_dir, user_info)

    return user_info, adapter, frontend


def usb_config(args):
    """Config the DVB interface(s) and the host"""
    common_params = _common(args)
    if (common_params is None):
        return
    user_info, adapter, frontend = common_params

    # Check if dependencies other than dvbnet are installed
    apps = ["ip"]
    if not args.skip_firewall:
        apps.append("iptables")
    if (not dependencies.check_apps(apps)):
        return

    # Configure the subprocess runner
    runner.set_dry(args.dry_run)

    if args.ip is None:
        ips = ip.compute_rx_ips(user_info['sat']['ip'], len(args.pid))
    else:
        ips = args.ip

    assert (all(["/" in x
                 for x in ips])), "Please provide IPs in CIDR notation"

    assert(len(args.pid) == len(ips)), \
        "Please define one IP address for each PID."

    # dvbnet interfaces of interest
    #
    # NOTE: there is one dvbnet interface per PID. Each interface will have a
    # different IP address.
    net_ifs = list()
    for i_device in range(0, len(args.pid)):
        # Define interface name that is going to be generated by dvbnet
        net_if = "dvb" + adapter + "_" + str(i_device)
        net_ifs.append(net_if)

    # Create the dvbnet interface(s)
    _dvbnet(adapter, net_ifs, args.pid, ule=args.ule)

    # Set RP filters
    if (not args.skip_rp):
        rp.set_filters(net_ifs, prompt=(not args.yes), dry=args.dry_run)

    # Set firewall rules
    if (not args.skip_firewall):
        firewall.configure(net_ifs,
                           defs.src_ports,
                           user_info['sat']['ip'],
                           prompt=(not args.yes),
                           dry=args.dry_run)

    # Set IP
    ip.set_ips(net_ifs, ips, dry=runner.dry)

    util._print_header("Next Step")
    print("Run:\n\nblocksat-cli usb launch\n")

    return


log_key_map = {
    'Lock': 'lock',
    'Signal': 'level',
    'C/N': 'snr',
    'postBER': 'ber'
}


def _parse_log(line):
    """Parse logs from dvbv5-zap and convert to the monitoring format

    The monitoring format is the format accepted by the monitor.py module.

    """
    if (line is None or line == "\n"):
        return

    # Don't process the "Layer A" lines
    if ("Layer" in line):
        return

    # Only process lines containing "Signal"
    if ("Signal" not in line):
        return
    d = {}
    elements = line.split()
    n_elem = len(elements)
    d['lock'] = ("Lock" in line, None)
    for i, elem in enumerate(elements):
        # Each metric is printed as "name=value"
        if (elem[-1] == "=" and (i + 1) <= n_elem):
            key = elem[:-1]
            raw_value = elements[i + 1]

            # Convert key to the nomenclature adopted on monitor.py
            key = log_key_map[key]

            # Fix any scientific notation
            if ("^" in raw_value):
                raw_value = raw_value.replace("x10^", "e")

            # Parse value and unit
            unit = None
            if ("%" in raw_value):
                unit = "%"
                val = float(raw_value[:-1].replace(",", "."))
            elif (raw_value[-2:] == "dB"):
                val = float(raw_value[:-2].replace(",", "."))
                unit = "dB"
            elif (raw_value[-3:] == "dBm"):
                val = float(raw_value[:-3].replace(",", "."))
                unit = "dBm"
            else:
                val = float(raw_value.replace(",", "."))

            d[key] = (val, unit)

    return d


def launch(args):
    """Launch the DVB interface from scratch

    Handles the launch subcommand

    """

    common_params = _common(args)
    if (common_params is None):
        return
    user_info, adapter, frontend = common_params

    # Check if all dependencies are installed
    if (not dependencies.check_apps(["dvbv5-zap"])):
        return

    # Check conflicting logging options
    if ((args.monitor or args.record_file)
            and (args.log_scrolling or args.log_file)):
        raise ValueError("Logging options are disabled when running with "
                         "-m/--monitor or -r/--record-file")

    # Log Monitoring
    monitor = monitoring.Monitor(args.cfg_dir,
                                 logfile=args.log_file,
                                 scroll=args.log_scrolling,
                                 min_interval=args.log_interval,
                                 server=args.monitoring_server,
                                 port=args.monitoring_port,
                                 report=args.report,
                                 report_opts=monitoring.get_report_opts(args),
                                 utc=args.utc)

    # Channel configuration file
    chan_conf = user_info['setup']['channel']

    # Zap
    zap_ps = zap(adapter,
                 frontend,
                 chan_conf,
                 user_info,
                 lnb=args.lnb,
                 output=args.record_file,
                 timeout=args.timeout,
                 monitor=args.monitor)

    # Handler for SIGINT
    def signal_handler(sig, frame):
        print('Stopping...')
        zap_ps.terminate()
        sys.exit(zap_ps.poll())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    util._print_header("Receiver Monitoring")
    print()

    # Listen to dvbv5-zap indefinitely
    if (args.monitor or args.record_file):
        zap_ps.wait()
    else:
        while (zap_ps.poll() is None):
            line = zap_ps.stderr.readline()
            metrics = _parse_log(line)
            if (metrics is None):
                continue
            monitor.update(metrics)
    print()
    sys.exit(zap_ps.poll())


def list_subcommand(args):
    """Call function that finds the DVB adapter

    Handles the find-adapter subcommand

    """
    if (not dependencies.check_apps(["dvbnet", "dvb-fe-tool"])):
        return

    _find_adapter(list_only=True)


def rm_subcommand(args):
    """Remove DVB interface

    """

    if (not dependencies.check_apps(["dvbnet", "dvb-fe-tool", "ip"])):
        return

    # Configure the subprocess runner
    runner.set_dry(args.dry_run)

    # Find adapter
    if (args.adapter is None):
        adapter, _ = _find_adapter()
    else:
        # If argument --adapter holds a digit-only string, assume it refers to
        # the adapter number. Otherwise, assume it refers to the target model.
        adapter = args.adapter if args.adapter.isdigit() else \
            _find_adapter(target_model=args.adapter)[0]

    interfaces = _find_dvbnet_interfaces(adapter)
    chosen_devices = list()

    if (len(interfaces) > 1):
        if (args.all):
            for interface in interfaces:
                chosen_devices.append(interface['name'])
        else:
            print("Choose net device to remove:")
            for i_dev, interface in enumerate(interfaces):
                print("[%2u] %s" % (i_dev, interface['name']))
            print("[ *] all")

            try:
                choice = input("Choose number: ")
                if (choice == "*"):
                    i_chosen_devices = range(0, len(interfaces))
                else:
                    i_chosen_devices = [int(choice)]
            except ValueError:
                raise ValueError(
                    "Please choose a number or \"*\" for all devices")

            for i_chosen_dev in i_chosen_devices:
                if (i_chosen_dev > len(interfaces)):
                    raise ValueError("Invalid number")

                chosen_devices.append(interfaces[i_chosen_dev]['name'])

    elif (len(interfaces) == 0):
        print("No DVB network interfaces to remove")
        return
    else:
        # There is a single interface
        chosen_devices.append(interfaces[0]['name'])

    for chosen_dev in chosen_devices:
        _rm_dvbnet_interface(adapter, chosen_dev)


def print_help(args):
    """Re-create argparse's help menu for the usb command"""
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(title='', help='')
    parser = subparser(subparsers)
    print(parser.format_help())
