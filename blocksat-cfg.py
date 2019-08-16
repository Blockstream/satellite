#!/usr/bin/env python3
"""
Launch the DVB receiver
"""
import os, sys, signal, argparse, subprocess, re, time, logging


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
    output = subprocess.check_output(["grep", "frontend"], stdin=ps.stdout,
                                     stderr=subprocess.STDOUT)
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

    dvb_s2_adapters = [a for a in adapters if a["support"] == "DVB-S/S2"]

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


def zap(adapter, conf_file, lnb="UNIVERSAL", output=None, timeout=None):
    """Run zapper

    Args:
        adapter   : DVB adapter index
        conf_file : Path to channel configurations file
        lnb       : LNB type
        output    : Output filename (when recording)
        timeout   : Run the zap for this specified duration

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
    else:
        # Set "monitor mode" only if not recording
        cmd.append("-m")

    if (timeout is not None):
        cmd = cmd + ["-t", timeout]

    cmd.append("blocksat-ch")

    logging.debug("> " + " ".join(cmd))
    ps = subprocess.Popen(cmd)

    return ps


def dvbnet(adapter, net_if, pid=32, ule=False):
    """Start DVB network interface

    Args:
        adapter   : DVB adapter index
        net_if    : DVB network interface name
        pid       : PID to listen to
        ule       : Whether to use ULE framing

    """

    assert(pid >= 32 and pid <= 8190), "PID not insider range 32 to 8190"

    print("\n------------------------------ Network Interface " +
          "-------------------------------")

    # Check if interface already exists
    try:
        res = subprocess.check_output(["ip", "addr", "show", "dev", net_if])
    except subprocess.CalledProcessError as e:
        res = None
        pass

    # Create interface in case it doesn't
    if (res is None):
        if (ule):
            print("Launch %s using ULE encapsulation" %(net_if))
        else:
            print("Launch %s using MPE encapsulation" %(net_if))

        adapter_dir = '/dev/dvb/adapter' + adapter
        if (not os.access(adapter_dir, os.W_OK)):
            raise PermissionError(
                "You need write permission on %s. " %(adapter_dir) +
                "Consider running as root." )

        ule_arg = "-U" if ule else ""
        cmd     = ["dvbnet", "-a", adapter, "-p", str(pid), ule_arg]
        logging.debug("> " + " ".join(cmd))
        res     = subprocess.check_output(cmd)
        print(res.decode())
    else:
        print("Interface %s already exists" %(net_if))


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


def rm_interface(adapter, interface):
    """Remove DVB net interface

    Args:
        adapter:   Corresponding DVB adapter
        interface: dvbnet interface number
    """

    print("\n------------------------------ Remove dvbnet interface " +
          "--------------------------------")
    cmd     = ["dvbnet", "-a", adapter, "-d", interface]
    logging.debug("> " + " ".join(cmd))
    res     = subprocess.check_output(cmd)
    print(res.decode())


def set_ip(net_if, ip_addr):
    """Set the IP of the DVB network interface

    Args:
        net_if    : DVB network interface name
        ip_addr   : Target IP address for the DVB interface slash subnet mask

    """

    print("\n----------------------------- Interface IP Address " +
          "-----------------------------")
    # Check if interface has IP:
    try:
        res = subprocess.check_output(["ip", "addr", "show", "dev", net_if])
    except subprocess.CalledProcessError as e:
        res = None
        pass

    has_ip = False
    for line in res.splitlines():
        if "inet" in line.decode():
            inet_info = line.decode().split()
            has_ip = True
            ip_ok  = (inet_info[1] == ip_addr)
            break

    if (has_ip and not ip_ok):
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
    print("Blocksat traffic is one-way and thus reverse path (RP) filtering " +
          "must be\ndisabled. The automatic solution disables RP filtering " +
          "on the DVB interface and\nenables RP filtering on all other " +
          "interfaces.")
    resp = input("OK to proceed? [Y/n] ") or "Y"

    # Sysctl-ready interface name: replace a dot (for VLAN interface) with slash
    sysctl_dvb_if = dvb_if.replace(".", "/")

    if (resp.lower() == "y"):
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


def __filter_iptables_rules(net_if):
    """Filter iptables rules corresponding to a target interface

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


def __config_input_rule(net_if, cmd):
    """Helper to configure an iptables rule

    Checks if rule already exists and, otherwise, adds it.

    Args:
        net_if : network interface name
        cmd    : list with iptables command

    """

    for rule in __filter_iptables_rules(net_if):
        if (rule['rule'][3] == "ACCEPT" and rule['rule'][6] == cmd[6] and
            (cmd[4] == "igmp" or (rule['rule'][4] == "udp" and
                                  rule['rule'][12] == cmd[10]))):
            print("\nFirewall rule already configured\n")
            print(rule['header1'])
            print(rule['header2'])
            print(" ".join(rule['rule']))
            print("\nSkipping...\n")
            return

    # Set up iptables rules
    logging.debug("> " + " ".join(cmd))
    subprocess.check_output(cmd)

    # Check results
    res = subprocess.check_output([
        "iptables", "-L", "-v", "--line-numbers"
    ])

    for rule in __filter_iptables_rules(net_if):
        if (rule['rule'][3] == "ACCEPT" and rule['rule'][6] == cmd[6] and
            (cmd[4] == "igmp" or (rule['rule'][4] == "udp" and
                                  rule['rule'][12] == cmd[10]))):
            print("Added iptables rule:\n")
            print(rule['header1'])
            print(rule['header2'])
            print(" ".join(rule['rule']))


def set_iptables_rules(net_if, ports, igmp=False):
    """Define rule on iptables to accept blocksat traffic via DVB interface

    Args:
        net_if : DVB network interface name
        ports  : ports used for blocks traffic and API traffic
        igmp   : Whether or not to configure rule to accept IGMP queries

    """

    print("\n------------------------------- Firewall Rules " +
          "--------------------------------")
    print("Configure firewall rule to accept Blocksat traffic arriving " +
          "at interface %s\ntowards UDP ports %s." %(net_if, ",".join(ports)))

    resp = input("Add corresponding ACCEPT firewall rule? [Y/n] ") or "Y"

    if (resp.lower() == "y"):
        cmd = [
            "iptables",
            "-I", "INPUT",
            "-p", "udp",
            "-i", net_if,
            "--match", "multiport",
            "--dports", ",".join(ports),
            "-j", "ACCEPT",
        ]
        __config_input_rule(net_if, cmd)
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

    resp = input("Add corresponding ACCEPT rule on firewall? [Y/n] ") or "Y"

    if (resp.lower() == "y"):
        cmd = [
            "iptables",
            "-I", "INPUT",
            "-p", "igmp",
            "-i", net_if,
            "-j", "ACCEPT",
        ]
        __config_input_rule(net_if, cmd)
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
        set_iptables_rules(net_if, src_ports)

    # Set IP
    set_ip(net_if, args.ip)

    print("\n----------------------------------- Listening " +
          "----------------------------------")

    # Zap
    zap_ps = zap(adapter, args.chan_conf, output=args.record_file,
                 timeout=args.timeout)

    def signal_handler(sig, frame):
        print('Stopping...')
        zap_ps.terminate()
        sys.exit(zap_ps.poll())

    signal.signal(signal.SIGINT, signal_handler)
    zap_ps.wait()
    sys.exit(zap_ps.poll())


def reverse_path_subcommand(args):
    """Call function that sets reverse path filters

    Handles the reverse-path subcommand

    """
    set_rp_filters(args.interface)


def firewall_subcommand(args):
    """Call function that sets firewall rules

    Handles the firewall subcommand

    """
    set_iptables_rules(args.interface, src_ports, igmp=args.standalone)


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

    if (len(interfaces) > 0):
        print("Choose net device to remove:")
        resp       = input("%s or %s? " %(", ".join(interfaces[:-1]), interfaces[-1]))
        chosen_dev = resp

        if (chosen_dev not in interfaces):
            raise ValueError("Wrong device")
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

    launch_parser.set_defaults(func=launch)

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
