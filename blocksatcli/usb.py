"""Linux USB demodulatos"""
from pprint import pformat
from ipaddress import IPv4Interface
import os, sys, signal, argparse, subprocess, time, logging, threading, json
from argparse import ArgumentDefaultsHelpFormatter
from . import config, util, defs, rp, firewall
import textwrap


def _find_v4l_lnb(info):
    """Find suitable LNB within v4l-utils preset LNBs

    The LNBs on list v4l_lnbs are defined at lib/libdvbv5/dvb-sat.c

    """

    target_lo_freq = int(info['lnb']['lo_freq'])

    # Find options that match the LO freq
    options = list()
    for lnb in defs.v4l_lnbs:
        is_universal_option = 'highfreq' in lnb

        if (lnb['lowfreq'] == target_lo_freq and
            is_universal_option == info['lnb']['universal']):
            options.append(lnb)

        if (is_universal_option and
            lnb['highfreq'] == target_lo_freq and
            info['lnb']['universal']):
            options.append(lnb)

    # TODO complete polarization checking
    assert(len(options) > 0), "LNB doesn't match a valid option"
    logging.debug("Matching LNB options: {}".format(pformat(options)))

    return options[0]


def _check_ip(net_if, ip_addr):
    """Check if interface has IP and if it matches target IP

    Args:
        net_if  : DVB network interface name
        ip_addr : Target IP address for the DVB interface slash subnet mask

    Returns:
        (Bool, Bool) Tuple of booleans. The first indicates whether interface
        already has an IP. The second indicates whether the interface IP (if
        existing) matches with respect to a target IP.

    """
    try:
        res = subprocess.check_output(["ip", "addr", "show", "dev", net_if])
    except subprocess.CalledProcessError as e:
        res = None
        pass

    has_ip = False
    ip_ok  = False
    for line in res.splitlines():
        if "inet" in line.decode() and "inet6" not in line.decode():
            has_ip    = True
            # Check if IP matches target
            inet_info = line.decode().split()
            inet_if   = IPv4Interface(inet_info[1])
            target_if = IPv4Interface(ip_addr)
            ip_ok     = (inet_if == target_if)
            break

    return has_ip, ip_ok


def _set_ip(net_if, ip_addr, verbose):
    """Set the IP of the DVB network interface

    Args:
        net_if    : DVB network interface name
        ip_addr   : Target IP address for the DVB interface slash subnet mask
        verbose   : Controls verbosity

    """
    has_ip, ip_ok = _check_ip(net_if, ip_addr)

    if (has_ip and not ip_ok):
        print("Interface %s has an IP, but it is not %s" %(net_if, ip_addr))
        print("Flush current IP address of %s" %(net_if))
        cmd = util.root_cmd(["ip", "address", "flush", "dev", net_if])
        logging.debug("> " + " ".join(cmd))
        res = subprocess.check_output(cmd)

    if (not has_ip or not ip_ok):
        print("Assign IP address %s to %s" %(ip_addr, net_if))
        cmd = util.root_cmd(["ip", "address", "add", ip_addr, "dev", net_if])
        logging.debug("> " + " ".join(cmd))
        res = subprocess.check_output(cmd)
    else:
        if (verbose):
            print("%s already has IP %s" %(net_if, ip_addr))


def _set_ips(net_ifs, ip_addrs, verbose=True):
    """Set IPs of one or multiple DVB network interface(s

    Args:
        net_ifs   : List of DVB network interface names
        ip_addrs  : List of IP addresses for the DVB interface slash subnet mask
        verbose   : Controls verbosity

    """
    if (verbose):
        print("\n----------------------------- Interface IP Address " +
              "-----------------------------")

    for net_if, ip_addr in zip(net_ifs, ip_addrs):
        _set_ip(net_if, ip_addr, verbose)


def _find_adapter(prompt=True):
    """Find the DVB adapter

    Returns:
        Tuple with (adapter index, frontend index)

    """
    print("\n------------------------------ Find DVB Adapter " +
          "--------------------------------")
    ps     = subprocess.Popen("dmesg", stdout=subprocess.PIPE)
    try:
        output = subprocess.check_output(["grep", "frontend"], stdin=ps.stdout,
                                         stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as grepexc:
        if (grepexc.returncode == 1):
            output = ""
            pass
    ps.wait()

    # Search a range of adapters. There is no command to list all adapters, so
    # we try to list each one individually using `dvbnet -a adapter_no -l`.
    adapters = list()
    for a in range(0,10):
        cmd     = ["dvbnet", "-a", str(a), "-l"]
        logging.debug("> " + " ".join(cmd))

        with open(os.devnull, 'w') as devnull:
            res = subprocess.call(cmd, stdout=devnull, stderr=devnull)
            if (res == 0):
                # Try a few frontends too
                for f in range(0,2):
                    try:
                        output = subprocess.check_output(["dvb-fe-tool", "-a",
                                                          str(a), "-f", str(f)])
                        line   = output.splitlines()[0].decode().split()
                        adapter = {
                            "adapter"  : str(a),
                            "frontend" : line[5].replace(")","").split("frontend")[-1],
                            "vendor"   : line[1],
                            "model"    : " ".join(line[2:4]),
                            "support"  : line[4]
                        }
                        adapters.append(adapter)
                        logging.debug(pformat(adapter))
                    except subprocess.CalledProcessError as e:
                        pass

    # If nothing was obtained using dvbnet, try to inspect dmesg logs
    if (len(adapters) == 0):
        lines       = output.splitlines()
        adapter_set = set() # use set to filter unique values
        adapters    = list()
        for line in lines:
            linesplit  = line.decode().split()
            i_adapter  = linesplit.index('adapter')
            i_frontend = linesplit.index('frontend')
            device     = linesplit[i_frontend + 2:]
            adapter = {
                "adapter"  : linesplit[i_adapter + 1],
                "frontend" : linesplit[i_frontend + 1],
                "vendor"   : device[0][1:],
                "model"    : " ".join(device[1:-1]),
                "support"  : device[-1][:-4].replace('(', '').replace(')', '')
            }
            adapter_set.add(json.dumps(adapter))

        # Process unique adapter logs
        for adapter in adapter_set:
            adapters.append(json.loads(adapter))
            logging.debug(pformat(json.loads(adapter)))

    dvb_s2_adapters = [a for a in adapters if ("DVB-S/S2" in a["support"])]
    logging.debug(dvb_s2_adapters)

    assert(len(dvb_s2_adapters) > 0), "No DVB-S2 adapters found"

    chosen_adapter = None
    for adapter in dvb_s2_adapters:
        print("Found DVB-S2 adapter: %s %s" %(adapter["vendor"],
                                              adapter["model"]))

        if (prompt):
            if (util._ask_yes_or_no("Choose adapter?")):
                chosen_adapter = adapter
                logging.debug("Chosen adapter:")
                logging.debug(pformat(adapter))
                break

    if (not prompt):
        return

    if (chosen_adapter is None):
        raise ValueError("Please choose DVB-S2 adapter")

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

    assert(pid >= 32 and pid <= 8190), "PID not insider range 32 to 8190"

    if (ule):
        encapsulation = 'ULE'
    else:
        encapsulation = 'MPE'

    # Check if interface already exists
    try:
        res = subprocess.check_output(["ip", "addr", "show", "dev", ifname])
    except subprocess.CalledProcessError as e:
        res = None
        pass

    os_interface_exists = (res is not None)
    matching_dvbnet_if  = None

    # When the network interface exists in the OS, we also need to check if the
    # matching dvbnet device is configured according to what we want now
    if (os_interface_exists):
        print("Network interface %s already exists" %(ifname))

        for interface in existing_dvbnet_interfaces:
            if (interface['name'] == ifname):
                matching_dvbnet_if = interface
                break

    # Our indication that interface exists comes from "ip addr show
    # dev". However, it is possible that dvbnet does not have any interface
    # associated to an adapter, so check if we found anything:
    cfg_interface = False
    if (len(existing_dvbnet_interfaces) > 0 and matching_dvbnet_if is not None):
        # Compare to desired configurations
        if (matching_dvbnet_if['pid'] != pid or
            matching_dvbnet_if['encapsulation'] != encapsulation):
            cfg_interface = True

        if (matching_dvbnet_if['pid'] != pid):
            print("Current PID is %d. Set it to %d" %(
                matching_dvbnet_if['pid'], pid))

        if (matching_dvbnet_if['encapsulation'] != encapsulation):
            print("Current encapsulation is %s. Set it to %s" %(
                matching_dvbnet_if['encapsulation'], encapsulation
            ))
    else:
        cfg_interface = True

    # Create interface in case it doesn't exist or needs to be re-created
    if (cfg_interface):
        # If interface exists, but must be re-created, remove the existing one
        # first
        if (os_interface_exists):
            _rm_dvbnet_interface(adapter, ifname, verbose=False)

        adapter_dir = '/dev/dvb/adapter' + adapter

        if (ule):
            print("Launch %s using ULE encapsulation" %(ifname))
            ule_arg = "-U"
        else:
            print("Launch %s using MPE encapsulation" %(ifname))
            ule_arg = ""

        cmd = util.root_cmd(["dvbnet", "-a", adapter, "-p", str(pid), ule_arg])

        has_w_access = os.access(adapter_dir, os.W_OK)
        if (not has_w_access):
            print(textwrap.fill(
                "You don't have write access to {}. Hence, \"sudo\" will "
                "be inserted in the following command:".format(adapter_dir)))
            print("\n> " + " ".join(cmd) + "\n")

        # Create interface for a given DVB adapter
        logging.debug("> " + " ".join(cmd))
        res     = subprocess.check_output(cmd)
        print(res.decode())
    else:
        print("Network interface %s already configured correctly" %(ifname))


def _dvbnet(adapter, ifnames, pids, ule=False):
    """Start DVB network interfaces of a DVB adapter

    An adapter can have multiple dvbnet interfaces, one for each PID.

    Args:
        adapter  : DVB adapter index
        ifnames  : list of DVB network interface names
        pids     : List of PIDs to listen to on each interface
        ule      : Whether to use ULE framing

    """
    assert(isinstance(ifnames, list))
    assert(isinstance(pids, list))
    assert(len(ifnames) == len(pids)), \
        "Interface names and PID number must be vectors of the same length"

    # Find the dvbnet interfaces that already exist for the chosen adapter
    existing_dvbnet_iif = _find_dvbnet_interfaces(adapter)

    print("\n------------------------------ Network Interface " +
          "-------------------------------")

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

    print("\n-------------------------- Find dvbnet interface(s) " +
          "----------------------------")
    cmd     = ["dvbnet", "-a", adapter, "-l"]
    logging.debug("> " + " ".join(cmd))
    res     = subprocess.check_output(cmd)

    interfaces = list()
    for line in res.splitlines():
        if ("Found device" in line.decode()):
            line_split    = line.decode().split()
            interface = {
                'dev'           : line_split[2][:-1],
                'name'          : line_split[4][:-1],
                'pid'           : int(line_split[8][:-1]),
                'encapsulation' : line_split[10]
            }
            logging.debug(pformat(interface))
            interfaces.append(interface)

    return interfaces


def _rm_dvbnet_interface(adapter, ifname, verbose=True):
    """Remove DVB net interface

    Args:
        adapter   : Corresponding DVB adapter
        interface : dvbnet interface number
        verbose   : Controls verbosity
    """

    if (verbose):
        print("\n------------------------------ Remove dvbnet interface " +
              "--------------------------------")
    cmd = util.root_cmd(["ip", "link", "set", ifname, "down"])
    logging.debug("> " + " ".join(cmd))
    res = subprocess.check_output(cmd)

    if_number = ifname.split("_")[-1]
    cmd       = util.root_cmd(["dvbnet", "-a", adapter, "-d", if_number])
    logging.debug("> " + " ".join(cmd))
    res       = subprocess.check_output(cmd)
    print(res.decode())


def zap(adapter, frontend, ch_conf_file, user_info, lnb="UNIVERSAL",
        output=None, timeout=None, monitor=False, scrolling=False):
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
        scrolling    : Whether to print zap logs by scrolling rather than
                       printing always on the same line.

    Returns:
        Subprocess object

    """

    print("\n------------------------------ Tuning DVB Receiver " +
          "-----------------------------")
    print("Running dvbv5-zap")

    # LNB name to use when calling dvbv5-zap
    if (lnb is None):
        # Find suitable LNB within v4l-utils preset LNBs
        lnb = _find_v4l_lnb(user_info)['alias']

    cmd = ["dvbv5-zap", "-c", ch_conf_file, "-a", adapter, "-f", frontend,
           "-l", lnb, "-v"]

    if (output is not None):
        cmd = cmd + ["-o", output]

        if (os.path.exists(output)):
            print("File %s already exists" %(output))

            # The recording is such that MPEG TS packets are overwritten one by
            # one. For instance, if previous ts file had 1000 MPEG TS packets,
            # when overwriting, the tool would overwrite each packet
            # individually. So if it was stopped for instance after the first 10
            # MPEG TS packets, only the first 10 would be overwritten, the
            # remaining MPEG TS packets would remain in the ts file.
            #
            # The other option is to remove the ts file completely and start a
            # new one. This way, all previous ts packets are guaranteed to be
            # erased.
            raw_resp = input("Remove and start new (R) or Overwrite (O)? [R/O] ")
            response = raw_resp.lower()

            if (response == "r"):
                os.remove(output)
            elif (response != "o"):
                raise ValueError("Unknown response")

    if (timeout is not None):
        cmd = cmd + ["-t", timeout]

    if (monitor):
        assert(not scrolling), \
            "Monitor mode does not work with scrolling (line-by-line) logs"
        assert(output is None), \
            "Monitor mode does not work if recording (i.e. w/ -r flag)"
        cmd.append("-m")

    cmd.append("blocksat-ch")

    logging.debug("> " + " ".join(cmd))

    if (scrolling):
        ps = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, universal_newlines=True)
    else:
        ps = subprocess.Popen(cmd)

    return ps


def subparser(subparsers):
    """Subparser for usb command"""
    p = subparsers.add_parser('usb',
                              description="Launch a USB DVB-S2 receiver",
                              help='Launch a Linux USB DVB-S2 receiver',
                              formatter_class=ArgumentDefaultsHelpFormatter)

    p.add_argument('-c', '--chan-conf',
                   default="channels.conf",
                   help='Channel configurations file within the configuration \
                   directory')

    p.add_argument('-a', '--adapter',
                   default=None,
                   help='DVB-S2 adapter number')

    p.add_argument('-f', '--frontend',
                   default=None,
                   help='DVB-S2 adapter\'s frontend number')

    p.add_argument('-l', '--lnb',
                   choices=defs.lnb_options,
                   default=None,
                   help="LNB from v4l-utils to be used. "
                   "If None, i.e. not specified, it will be set "
                   "automatically")

    p.add_argument('-U', '--ule', default=False,
                   action='store_true',
                   help='Use ULE encapsulation instead of MPE')

    p.add_argument('--skip-rp', default=False, action='store_true',
                   help='Skip settting of reverse path filters')

    p.add_argument('--skip-firewall', default=False,
                   action='store_true',
                   help='Skip configuration of firewall rules')

    p.add_argument('-r', '--record-file', default=None,
                   help='Record MPEG-TS traffic into target file')

    p.add_argument('-t', '--timeout', default=None,
                   help='Stop zapping after timeout - useful to \
                               control recording time')

    p.add_argument('-m', '--monitor', default=False,
                   action='store_true',
                   help='Launch dvbv5-zap in monitor mode - useful \
                               to debug packet and bit rates')

    p.add_argument('-s', '--scrolling', default=False,
                   action='store_true',
                   help='Print dvbv5-zap logs line-by-line, i.e. \
                               scrolling, rather than always on the same line')

    p.add_argument('--pid', default=defs.pids,
                   type=int,
                   nargs='+',
                   help='List of PIDs to be listened to by dvbnet')

    p.add_argument('-i', '--ip',
                   default=['192.168.201.2/24', '192.168.201.3/24'],
                   nargs='+',
                   help='IP address set for each DVB-S2 net \
                               interface with subnet mask in CIDR notation')

    p.set_defaults(func=launch)

    subsubparsers = p.add_subparsers(title='subcommands',
                                     help='Target USB sub-command')
    # Find adapter sub-command
    p2 = subsubparsers.add_parser('ls',
                                  description="List DVB-S2 adapters",
                                  help='List DVB-S2 adapters',
                                  formatter_class=ArgumentDefaultsHelpFormatter)
    p2.set_defaults(func=list_subcommand)

    # Remove adapter sub-command
    p3 = subsubparsers.add_parser('rm',
                                  description="Remove DVB-S2 adapter",
                                  help='Remove DVB-S2 adapter',
                                  formatter_class=ArgumentDefaultsHelpFormatter)
    p3.add_argument('-a', '--adapter',
                           default=None,
                           help='DVB-S2 adapter number')
    p3.set_defaults(func=rm_subcommand)


def launch(args):
    """Launch the DVB interface from scratch

    Handles the launch subcommand

    """

    assert(len(args.pid) == len(args.ip)), \
        "Number of PIDs (%u) defined by argument --pid " %(len(args.pid)) + \
        "does not match the number of IPs (%u) defined by " %(len(args.ip)) + \
        "argument --ip. Please define one IP address for each PID."

    # User info
    user_info = config.read_cfg_file(args.cfg_file, args.cfg_dir)

    if (user_info is None):
        return

    # Find adapter
    if (args.adapter is None):
        adapter, frontend = _find_adapter()
    else:
        adapter  = args.adapter
        frontend = args.frontend

    # Launch the DVB network interface - one interface for each PID of interest
    net_ifs  = list()
    for i_device in range(0, len(args.pid)):
        # Define interface name that is going to be generated by dvbnet
        net_if = "dvb" + adapter + "_" + str(i_device)
        net_ifs.append(net_if)

    # Create the interface(s)
    _dvbnet(adapter, net_ifs, args.pid, ule=args.ule)

    # Set RP filters
    if (not args.skip_rp):
        rp.set_rp_filters(net_ifs)

    # Set firewall rules
    if (not args.skip_firewall):
        firewall.configure(net_ifs, defs.src_ports)

    # Set IP
    _set_ips(net_ifs, args.ip)

    # Channel configuration file
    chan_conf = os.path.join(args.cfg_dir, os.path.basename(args.chan_conf))

    # Zap
    zap_ps = zap(adapter, frontend, chan_conf, user_info, lnb=args.lnb,
                 output=args.record_file, timeout=args.timeout,
                 monitor=args.monitor, scrolling=args.scrolling)

    # Handler for SIGINT
    def signal_handler(sig, frame):
        print('Stopping...')
        zap_ps.terminate()
        sys.exit(zap_ps.poll())

    signal.signal(signal.SIGINT, signal_handler)

    # Timer to periodically check the interface IP
    def reset_ip():
        _set_ips(net_ifs, args.ip, verbose=False)
        timer        = threading.Timer(10, reset_ip)
        timer.daemon = True
        timer.start()

    reset_ip()

    # Listen to dvbv5-zap indefinitely
    if (args.scrolling):
        # Loop indefinitely over zap
        while (zap_ps.poll() is None):
            line = zap_ps.stderr.readline()
            if (line):
                print('\r%s: '%(time.strftime("%Y-%m-%d %H:%M:%S",
                                              time.gmtime())) +
                      line, end='')
            else:
                time.sleep(1)
    else:
        zap_ps.wait()
    sys.exit(zap_ps.poll())


def list_subcommand(args):
    """Call function that finds the DVB adapter

    Handles the find-adapter subcommand

    """
    _find_adapter(prompt=False)


def rm_subcommand(args):
    """Remove DVB interface

    """

    # Find adapter
    if (args.adapter is None):
        adapter, frontend = _find_adapter()
    else:
        adapter = args.adapter

    interfaces     = _find_dvbnet_interfaces(adapter)
    chosen_devices = list()

    if (len(interfaces) > 1):
        print("Choose net device to remove:")
        for i_dev, interface in enumerate(interfaces):
            print("[%2u] %s" %(i_dev, interface['name']))
        print("[ *] all")

        try:
            choice = input("Choose number: ")
            if (choice == "*"):
                i_chosen_devices = range(0, len(interfaces))
            else:
                i_chosen_devices = [int(choice)]
        except ValueError:
            raise ValueError("Please choose a number or \"*\" for all devices")

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
        if (not util._ask_yes_or_no("Remove interface %s?" %(chosen_dev))):
            print("Aborting...")
            return

        _rm_dvbnet_interface(adapter, chosen_dev)


