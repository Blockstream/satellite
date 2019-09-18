#!/usr/bin/env python3
"""
Launch the DVB receiver
"""
import os, sys, signal, argparse, subprocess, re, time, logging, threading
from ipaddress import IPv4Interface


# Constants
src_ports = ["4433", "4434"]


def find_adapter(prompt=True):
    """Find the DVB adapter

    Returns:
        Adapter index

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

    lines    = output.splitlines()
    adapters = list()
    for line in lines:
        linesplit  = line.decode().split()
        i_adapter  = linesplit.index('adapter')
        i_frontend = linesplit.index('frontend')
        device     = linesplit[i_frontend + 2:]
        adapters.append({
            "adapter"  : linesplit[i_adapter + 1],
            "frontend" : linesplit[i_frontend + 1],
            "vendor"   : device[0][1:],
            "model"    : " ".join(device[1:-1]),
            "support"  : device[-1][:-4].replace('(', '').replace(')', '')
        })

    # If nothing was obtained by inspecting dmesg logs, try searching for a
    # range of adapter numbers. There is no command to list all adapters, so we
    # have to try to list each one individually using `dvbnet -a adapter_no -l`.
    if (len(adapters) == 0):
        adapters = list()
        for a in range(0,5):
            cmd     = ["dvbnet", "-a", str(a), "-l"]
            logging.debug("> " + " ".join(cmd))

            with open(os.devnull, 'w') as devnull:
                res = subprocess.call(cmd, stdout=devnull, stderr=devnull)
                if (res == 0):
                    output = subprocess.check_output(["dvb-fe-tool", "-a", str(a)])
                    line   = output.splitlines()[0].decode().split()
                    adapters.append({
                        "adapter"  : str(a),
                        "frontend" : line[5].replace(")","").split("frontend")[-1],
                        "vendor"   : line[1],
                        "model"    : " ".join(line[2:4]),
                        "support"  : line[4]
                    })

    dvb_s2_adapters = [a for a in adapters if a["support"] == "DVB-S/S2"]

    assert(len(dvb_s2_adapters) > 0), "No DVB-S2 adapters found"

    chosen_adapter = None
    for adapter in dvb_s2_adapters:
        print("Found DVB-S2 adapter: %s %s" %(adapter["vendor"],
                                              adapter["model"]))

        if (prompt):
            response = None
            while response not in {"y", "n"}:
                raw_resp = input("Choose adapter? [Y/n] ") or "Y"
                response = raw_resp.lower()

            if (response.lower() == "y"):
                chosen_adapter = adapter
                break

    if (not prompt):
        return

    if (chosen_adapter is None):
        raise ValueError("Please choose DVB-S2 adapter")

    return chosen_adapter["adapter"]


def zap(adapter, conf_file, lnb="UNIVERSAL", output=None, timeout=None,
        monitor=False, scrolling=False):
    """Run zapper

    Args:
        adapter   : DVB adapter index
        conf_file : Path to channel configurations file
        lnb       : LNB type
        output    : Output filename (when recording)
        timeout   : Run the zap for this specified duration
        monitor   : Monitor mode. Monitors DVB traffic stats (throughput and
                    packets per second), but does not deliver data upstream.
        scrolling : Whether to print zap logs by scrolling rather than printing
                    always on the same line.

    Returns:
        Subprocess object

    """

    print("\n------------------------------ Tuning DVB Receiver " +
          "-----------------------------")
    print("Running dvbv5-zap")

    cmd = ["dvbv5-zap", "-c", conf_file, "-a", adapter, "-l", lnb, "-v"]

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


def dvbnet(adapter, ifname, pid=32, ule=False):
    """Start DVB network interface

    Args:
        adapter   : DVB adapter index
        ifname    : DVB network interface name
        pid       : PID to listen to
        ule       : Whether to use ULE framing

    """

    assert(pid >= 32 and pid <= 8190), "PID not insider range 32 to 8190"

    print("\n------------------------------ Network Interface " +
          "-------------------------------")

    # Check if interface already exists
    try:
        res = subprocess.check_output(["ip", "addr", "show", "dev", ifname])
    except subprocess.CalledProcessError as e:
        res = None
        pass

    interface_exists = (res is not None)

    # Define whether or not to configure the DVB interface
    if (interface_exists):
        cfg_interface = False
        print("Interface %s already exists" %(ifname))

        # Do we want to configure an existing interface differently?
        cmd     = ["dvbnet", "-a", adapter, "-l"]
        logging.debug("> " + " ".join(cmd))
        res     = subprocess.check_output(cmd)
        for line in res.splitlines():
            if ("Found device" in line.decode()):
                split_line = line.decode().split()
                # Current configurations
                current_pid    = int(split_line[8].split(",")[0])
                current_ule    = (split_line[10] == "ULE")
                current_ifname = split_line[4].split(",")[0]

                # Compare to desired configurations
                if (current_pid != pid or current_ule != ule
                    or current_ifname != ifname):
                    cfg_interface = True

                if (current_pid != pid):
                    print("Current PID is %d. Set it to %d" %(current_pid, pid))

                if (current_ule != ule):
                    if (current_ule):
                        print("Current encapsulation is ULE. Set it to MPE")
                    else:
                        print("Current encapsulation is MPE. Set it to ULE")

                if (current_ifname != ifname):
                    print("Current interface name is %s. Set it to %s" %(
                        current_ifname, ifname))
    else:
        cfg_interface = True

    # Create interface in case it doesn't exist or needs to be re-created
    if (cfg_interface):
        # If interface exists, but must be re-created, remove the existing one
        # first
        if (interface_exists):
            rm_interface(adapter, current_ifname.split("_")[-1], verbose=False)

        adapter_dir = '/dev/dvb/adapter' + adapter
        if (not os.access(adapter_dir, os.W_OK)):
            raise PermissionError(
                "You need write permission on %s. " %(adapter_dir) +
                "Consider running as root." )

        if (ule):
            print("Launch %s using ULE encapsulation" %(ifname))
            ule_arg = "-U"
        else:
            print("Launch %s using MPE encapsulation" %(ifname))
            ule_arg = ""

        # Create interface for a given DVB adapter
        cmd     = ["dvbnet", "-a", adapter, "-p", str(pid), ule_arg]
        logging.debug("> " + " ".join(cmd))
        res     = subprocess.check_output(cmd)
        print(res.decode())


def find_interface(adapter):
    """Find DVB net interface

    Args:
        adapter: Corresponding DVB adapter

    Returns:
        interfaces : List of dvbnet interfaces

    """

    print("\n------------------------------ Find dvbnet interface " +
          "--------------------------------")
    cmd     = ["dvbnet", "-a", adapter, "-l"]
    logging.debug("> " + " ".join(cmd))
    res     = subprocess.check_output(cmd)

    interfaces = list()
    for line in res.splitlines():
        if ("Found device" in line.decode()):
            print(line.decode())
            interfaces.append(line.decode().split()[2][:-1])

    return interfaces


def rm_interface(adapter, interface, verbose=True):
    """Remove DVB net interface

    Args:
        adapter   : Corresponding DVB adapter
        interface : dvbnet interface number
        verbose   : Controls verbosity
    """

    if (verbose):
        print("\n------------------------------ Remove dvbnet interface " +
              "--------------------------------")

    ifname  = "dvb" + adapter + "_" + interface
    cmd     = ["ip", "link", "set", ifname, "down"]
    logging.debug("> " + " ".join(cmd))
    res     = subprocess.check_output(cmd)

    cmd     = ["dvbnet", "-a", adapter, "-d", interface]
    logging.debug("> " + " ".join(cmd))
    res     = subprocess.check_output(cmd)
    print(res.decode())


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

def set_ip(net_if, ip_addr, verbose=True):
    """Set the IP of the DVB network interface

    Args:
        net_if    : DVB network interface name
        ip_addr   : Target IP address for the DVB interface slash subnet mask
        verbose   : Controls verbosity

    """

    if (verbose):
        print("\n----------------------------- Interface IP Address " +
              "-----------------------------")

    has_ip, ip_ok = _check_ip(net_if, ip_addr)

    if (has_ip and not ip_ok):
        print("Interface %s has an IP, but it is not %s" %(net_if, ip_addr))
        print("Flush current IP address of %s" %(net_if))
        cmd = ["ip", "address", "flush", "dev", net_if]
        logging.debug("> " + " ".join(cmd))
        res = subprocess.check_output(cmd)

    if (not has_ip or not ip_ok):
        print("Assign IP address %s to %s" %(ip_addr, net_if))
        cmd = ["ip", "address", "add", ip_addr, "dev", net_if]
        logging.debug("> " + " ".join(cmd))
        res = subprocess.check_output(cmd)
    else:
        if (verbose):
            print("%s already has IP %s" %(net_if, ip_addr))


def set_rp_filters(dvb_if):
    """Disable reverse-path (RP) filtering for the DVB interface

    There are two layers of RP filters, one specific to the network interface
    and a higher level that controls the configurations for all network
    interfaces. This function disables RP filtering on the top layer (for all
    interfaces), but then enables RP filtering individually for each interface,
    except the DVB interface. This way, in the end only the DVB interface has RP
    filtering disabled.

    Args:
        dvb_if : DVB network interface

    """

    print("\n----------------------------- Reverse Path Filters " +
          "-----------------------------")

    # Sysctl-ready interface name: replace a dot (for VLAN interface) with slash
    sysctl_dvb_if = dvb_if.replace(".", "/")

    # Check current configuration of DVB interface and "all" rule:
    dvb_cfg =  subprocess.check_output([
        "sysctl",
        "net.ipv4.conf." + sysctl_dvb_if + ".rp_filter"
    ]).split()[-1].decode()
    all_cfg =  subprocess.check_output([
        "sysctl",
        "net.ipv4.conf.all.rp_filter"
    ]).split()[-1].decode()

    if (dvb_cfg == "0" and all_cfg == "0"):
        print("Current RP filtering configurations are already OK")
        print("Skipping...")
        return

    print("Blocksat traffic is one-way and thus reverse path (RP) filtering " +
          "must be\ndisabled. The automatic solution disables RP filtering " +
          "on the DVB interface and\nenables RP filtering on all other " +
          "interfaces.")
    resp = input("OK to proceed? [Y/n] ") or "Y"

    if (resp.lower() == "y"):
        # If "all" rule is already disabled, it is only necessary to disable the
        # target interface
        if (all_cfg == "0"):
            print("RP filter for \"all\" interfaces is already disabled")
            print("Disabling RP filter on interface %s" %(dvb_if))
            subprocess.check_output([
                "sysctl",
                "-w",
                "net.ipv4.conf." + sysctl_dvb_if + ".rp_filter=0"
            ])
        # If "all" rule is enabled, we will need to disable it. Also to preserve
        # RP filtering on all other interfaces, we will enable them manually.
        else:
            # Check interfaces
            ifs = os.listdir("/proc/sys/net/ipv4/conf/")

            # Enable all RP filters
            for interface in ifs:
                if (interface == "all" or interface == dvb_if or
                    interface == "lo"):
                    continue

                # Again, /proc/sys uses dot on VLANs normally, but sysctl does
                # not. Instead, it substitutes with slash. Replace here before using
                sysctl_interface = interface.replace(".", "/")

                # Check current configuration
                current_cfg =  subprocess.check_output([
                    "sysctl",
                    "net.ipv4.conf." + sysctl_interface + ".rp_filter"
                ]).split()[-1].decode()

                if (int(current_cfg) > 0):
                    print("RP filter is already enabled on interface %s" %(
                        interface))
                else:
                    print("Enabling RP filter on interface %s" %(interface))
                    subprocess.check_output([
                        "sysctl",
                        "-w",
                        "net.ipv4.conf." + sysctl_interface + ".rp_filter=1"
                    ])

            # Disable the overall RP filter
            print("Disabling RP filter on \"all\" rule")
            subprocess.check_output([
                "sysctl",
                "-w",
                "net.ipv4.conf.all.rp_filter=0"
            ])

            # And disable RP filtering on the DVB interface
            print("Disabling RP filter on interface %s" %(dvb_if))
            subprocess.check_output([
                "sysctl",
                "-w",
                "net.ipv4.conf." + sysctl_dvb_if + ".rp_filter=0"
            ])
    else:
        print("RP filtering configuration cancelled")


def __get_iptables_rules(net_if):
    """Get iptables rules that are specifically applied to a target interface

    Args:
        net_if : network interface name

    Returns:
        list of dictionaries with information of the individual matched rules

    """

    rules = list()

    # Get rules
    res = subprocess.check_output([
        "iptables", "-L", "-v", "--line-numbers"
    ])

    # Parse
    header1 = ""
    header2 = ""
    for line in res.splitlines():
        if ("Chain INPUT" in line.decode()):
            header1 = line.decode()

        if ("destination" in line.decode()):
            header2 = line.decode()

        if (net_if in line.decode()):
            rules.append({
                'rule' : line.decode().split(),
                'header1' : header1,
                'header2' : header2
            })

    return rules


def __is_iptables_igmp_rule_set(net_if, cmd):
    """Check if an iptables rule for IGMP is already configured

    Args:
        net_if : network interface name
        cmd    : list with iptables command

    Returns:
        True if rule is already set, False otherwise.

    """

    for rule in __get_iptables_rules(net_if):
        if (rule['rule'][3] == "ACCEPT" and rule['rule'][6] == cmd[6] and
            rule['rule'][4] == "igmp"):
            print("\nFirewall rule for IGMP already configured\n")
            print(rule['header1'])
            print(rule['header2'])
            print(" ".join(rule['rule']))
            print("\nSkipping...")
            return True

    return False

def __is_iptables_udp_rule_set(net_if, cmd):
    """Check if an iptables rule for UDP is already configured

    Args:
        net_if : network interface name
        cmd    : list with iptables command

    Returns:
        True if rule is already set, False otherwise.

    """

    for rule in __get_iptables_rules(net_if):
        if (rule['rule'][3] == "ACCEPT" and rule['rule'][6] == cmd[6] and
            (rule['rule'][4] == "udp" and rule['rule'][12] == cmd[10])):
            print("\nFirewall rule already configured\n")
            print(rule['header1'])
            print(rule['header2'])
            print(" ".join(rule['rule']))
            print("\nSkipping...")
            return True

    return False


def __add_iptables_rule(net_if, cmd):
    """Add iptables rule

    Args:
        net_if : network interface name
        cmd    : list with iptables command

    """

    # Set up iptables rules
    logging.debug("> " + " ".join(cmd))
    subprocess.check_output(cmd)

    # Check results
    res = subprocess.check_output([
        "iptables", "-L", "-v", "--line-numbers"
    ])

    for rule in __get_iptables_rules(net_if):
        print_rule = False

        if (rule['rule'][3] == "ACCEPT" and
            rule['rule'][6] == cmd[6] and
            rule['rule'][4] == cmd[4]):
            if (cmd[4] == "igmp"):
                print_rule = True
            elif (cmd[4] == "udp" and rule['rule'][12] == cmd[10]):
                print_rule = True

            if (print_rule):
                print("Added iptables rule:\n")
                print(rule['header1'])
                print(rule['header2'])
                print(" ".join(rule['rule']) + "\n")


def configure_firewall(net_if, ports, igmp=False):
    """Configure firewallrules to accept blocksat traffic via DVB interface

    Args:
        net_if : DVB network interface name
        ports  : ports used for blocks traffic and API traffic
        igmp   : Whether or not to configure rule to accept IGMP queries

    """

    print("\n------------------------------- Firewall Rules " +
          "--------------------------------")
    print("Configure firewall rule to accept Blocksat traffic arriving " +
          "at interface %s\ntowards UDP ports %s." %(net_if, ",".join(ports)))

    cmd = [
        "iptables",
        "-I", "INPUT",
        "-p", "udp",
        "-i", net_if,
        "--match", "multiport",
        "--dports", ",".join(ports),
        "-j", "ACCEPT",
    ]

    if (not __is_iptables_udp_rule_set(net_if, cmd)):
        resp = input("Add corresponding ACCEPT firewall rule? [Y/n] ") or "Y"

        if (resp.lower() == "y"):
            __add_iptables_rule(net_if, cmd)
        else:
            print("\nFirewall configuration cancelled")


    # We're done, unless we also need to configure an IGMP rule
    if (not igmp):
        return

    # IGMP rule supports standalone DVB modems. The host in this case will need
    # to periodically send IGMP membership reports in order for upstream
    # switches between itself and the DVB modem to continue delivering the
    # multicast-addressed traffic. This overcomes the scenario where group
    # membership timeouts are implemented by the intermediate switches.
    print("Configure also a firewall rule to accept IGMP queries. This is " +
          "necessary when using a standalone DVB modem.")

    cmd = [
        "iptables",
        "-I", "INPUT",
        "-p", "igmp",
        "-i", net_if,
        "-j", "ACCEPT",
    ]

    if (not __is_iptables_igmp_rule_set(net_if, cmd)):
        resp = input("Add corresponding ACCEPT rule on firewall? [Y/n] ") or "Y"

        if (resp.lower() == "y"):
            __add_iptables_rule(net_if, cmd)
        else:
            print("\nIGMP firewall rule cancelled")


def launch(args):
    """Launch the DVB interface from scratch

    Handles the launch subcommand

    """

    # Find adapter
    if (args.adapter is None):
        adapter = find_adapter()
    else:
        adapter = args.adapter

    # Interface name
    net_if = "dvb" + adapter + "_0"

    # Launch the DVB network interface
    dvbnet(adapter, net_if, ule=args.ule)

    # Set RP filters
    if (not args.skip_rp):
        set_rp_filters(net_if)

    # Set firewall rules
    if (not args.skip_firewall):
        configure_firewall(net_if, src_ports)

    # Set IP
    set_ip(net_if, args.ip)

    # Zap
    zap_ps = zap(adapter, args.chan_conf, output=args.record_file,
                 timeout=args.timeout, monitor=args.monitor,
                 scrolling=args.scrolling)

    # Handler for SIGINT
    def signal_handler(sig, frame):
        print('Stopping...')
        zap_ps.terminate()
        sys.exit(zap_ps.poll())

    signal.signal(signal.SIGINT, signal_handler)

    # Timer to periodically check the interface IP
    def reset_ip():
        set_ip(net_if, args.ip, verbose=False)
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


def cfg_standalone(args):
    """Configurations for standalone DVB modem
    """
    set_rp_filters(args.interface)
    configure_firewall(args.interface, src_ports,
                       igmp=True)


def reverse_path_subcommand(args):
    """Call function that sets reverse path filters

    Handles the reverse-path subcommand

    """
    set_rp_filters(args.interface)


def firewall_subcommand(args):
    """Call function that sets firewall rules

    Handles the firewall subcommand

    """
    configure_firewall(args.interface, src_ports, igmp=args.standalone)


def find_adapter_subcommand(args):
    """Call function that finds the DVB adapter

    Handles the find-adapter subcommand

    """
    find_adapter(prompt=False)


def rm_subcommand(args):
    """Remove DVB interface

    """

    # Find adapter
    if (args.adapter is None):
        adapter = find_adapter()
    else:
        adapter = args.adapter


    interfaces = find_interface(adapter)

    if (len(interfaces) > 1):
        print("Choose net device to remove:")
        chosen_dev = input("%s or %s? " %(", ".join(interfaces[:-1]),
                                          interfaces[-1]))

        if (chosen_dev not in interfaces):
            raise ValueError("Wrong device")

    if (len(interfaces) == 1):
        resp = input("Remove interface %s? [Y/n] " %(interfaces[-1])) or "Y"

        if (resp.lower() != "y"):
            print("Aborting...")
            return
        else:
            chosen_dev = interfaces[-1]

    elif (len(interfaces) == 1):
        chosen_dev = interfaces[0]
        print("Try removing device %s" %(chosen_dev))
    else:
        print("No DVB devices to remove")
        return

    rm_interface(adapter, chosen_dev)


def main():
    """Main - parse command-line arguments and call subcommands

    """

    cwd        = os.path.dirname(os.path.realpath(__file__))
    parser     = argparse.ArgumentParser(prog="blocksat-cfg",
                                         description="Blocksat configuration helper")
    subparsers = parser.add_subparsers(title='subcommands',
                                       help='Target sub-command')

    # Launch command
    launch_parser = subparsers.add_parser('launch',
                                          description="Set up the DVB interface",
                                          help='Launch DVB interface')

    launch_parser.add_argument('-c', '--chan-conf',
                               default=os.path.join(cwd, 'channels.conf'),
                               help='Channel configurations file ' +
                               '(default: channels.conf)')

    launch_parser.add_argument('-i', '--ip', default='192.168.201.2/24',
                               help='IP address set for the DVB net interface '
                               + 'with subnet mask in CIDR notation' +
                               '(default: 192.168.201.2/24)')

    launch_parser.add_argument('-a', '--adapter',
                               default=None,
                               help='DVB adapter number (default: None)')

    launch_parser.add_argument('--ule', default=False, action='store_true',
                               help='Use ULE encapsulation instead of MPE ' +
                               '(default: False)')

    launch_parser.add_argument('--skip-rp', default=False, action='store_true',
                               help='Skip settting of reverse path filters ' + \
                               '(default: False)')

    launch_parser.add_argument('--skip-firewall', default=False,
                               action='store_true',
                               help='Skip configuration of firewall rules ' + \
                               '(default: False)')

    launch_parser.add_argument('-r', '--record-file', default=None,
                               help='Record MPEG-TS traffic into target file \
                               (default: None)')

    launch_parser.add_argument('-t', '--timeout', default=None,
                               help='Stop zapping after timeout - useful to \
                               control recording time (default: None)')

    launch_parser.add_argument('-m', '--monitor', default=False,
                               action='store_true',
                               help='Launch dvbv5-zap in monitor mode - useful \
                               to debug packet and bit rates (default: False)')

    launch_parser.add_argument('-s', '--scrolling', default=False,
                               action='store_true',
                               help='Print dvbv5-zap logs line-by-line, i.e. \
                               scrolling, rather than always on the same line \
                               (default: False)')

    launch_parser.set_defaults(func=launch)

    # Standalone command
    stdl_parser = subparsers.add_parser('standalone',
                                        description="Configure host to \
                                        interface with standalone DVB modem",
                                        help='Configure host to interface with \
                                        standalone DVB modem')
    stdl_parser.add_argument('-i', '--interface', required = True,
                             help='Network interface (required)')
    stdl_parser.set_defaults(func=cfg_standalone)

    # Reverse path configuration command
    rp_parser = subparsers.add_parser('reverse-path', aliases=['rp'],
                                      description="Set reverse path filters",
                                      help='Set reverse path filters')

    rp_parser.add_argument('-i', '--interface', required = True,
                           help='Network interface (required)')

    rp_parser.set_defaults(func=reverse_path_subcommand)

    # Firewall configuration command
    fwall_parser = subparsers.add_parser('firewall',
                                         description="Set firewall rules",
                                         help='Set firewall rules')

    fwall_parser.add_argument('-i', '--interface', required = True,
                              help='Network interface (required)')

    fwall_parser.add_argument('--standalone', default=False,
                              action='store_true',
                              help='Configure for standalone DVB modem ' + \
                              '(default: False)')

    fwall_parser.set_defaults(func=firewall_subcommand)

    # Find adapter command
    find_parser = subparsers.add_parser('find',
                                        description="Find DVB adapter",
                                        help='Find DVB adapter')

    find_parser.set_defaults(func=find_adapter_subcommand)

    # Remove adapter command
    rm_parser = subparsers.add_parser('rm',
                                      description="Remove DVB adapter",
                                      help='Remove DVB adapter')

    rm_parser.add_argument('-a', '--adapter',
                           default=None,
                           help='DVB adapter number (default: None)')

    rm_parser.set_defaults(func=rm_subcommand)

    # Optional args
    parser.add_argument('--debug', action='store_true',
                        help='Debug mode (default: false)')

    args      = parser.parse_args()

    if (args.debug):
        logging.basicConfig(level=logging.DEBUG)
        logging.debug('[Debug Mode]')
    else:
        logging.basicConfig(level=logging.INFO)

    # Call corresponding subcommand
    args.func(args)


if __name__ == '__main__':
    main()
