#!/usr/bin/env python3
"""
Launch the DVB receiver
"""
import os, argparse, subprocess, re, time, logging


# Constants
src_ports = ["4433", "4434"]


def find_adapter():
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
        response = None
        while response not in {"y", "n"}:
            raw_resp = input("Choose adapter? [Y/n] ") or "Y"
            response = raw_resp.lower()

        if (response.lower() == "y"):
            chosen_adapter = adapter
            break

    if (chosen_adapter is None):
        raise ValueError("Please choose DVB-S2 adapter")

    return chosen_adapter["adapter"]


def zap(adapter, conf_file, lnb="UNIVERSAL"):
    """Run zapper

    Args:
        adapter   : DVB adapter index
        conf_file : Path to channel configurations file
        lnb       : LNB type

    Returns:
        Subprocess object

    """

    print("\n------------------------------ Tuning DVB Receiver " +
          "-----------------------------")
    print("Running dvbv5-zap")

    cmd = ["dvbv5-zap", "-P", "-c", conf_file, "-a", adapter, "-l", lnb,
           "-r", "ch2", "-v"]
    logging.debug("> " + " ".join(cmd))
    ps = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True)
    #   "-P" accepts all PIDs
    #   "-r" sets up MPEG-TS record
    #   "-v" sets verbose
    return ps


def dvbnet(adapter, net_if, pid=1, ule=True):
    """Start DVB network interface

    Args:
        adapter   : DVB adapter index
        net_if    : DVB network interface name
        pid       : PID to listen to
        ule       : Whether to use ULE framing

    """

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
    and a highler level that controls the configurations for all network
    interfaces. This function disables RP filtering on the top layer (for all
    interfaces), but then enables RP fitlering individually for each interface,
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
        # Check interfaces
        ifs = os.listdir("/proc/sys/net/ipv4/conf/")

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

        # Enable all RP filters
        for interface in ifs:
            if (interface == "all" or interface == dvb_if):
                continue

            # Again, /proc/sys uses dot on VLANs normally, but sysctl does
            # not. Instead, it substitutes with slash. Replace here before using
            sysctl_interface = interface.replace(".", "/")

            print("Enabling reverse path filter on interface %s" %(interface))
            subprocess.check_output([
                "sysctl",
                "-w",
                "net.ipv4.conf." + sysctl_interface + ".rp_filter=1"
            ])

        # Disable the overall RP filter
        print("Disabling reverse path filter on \"all\" rule")
        subprocess.check_output([
            "sysctl",
            "-w",
            "net.ipv4.conf.all.rp_filter=0"
        ])

        # And disable RP filtering on the DVB interface
        print("Disabling reverse path filter on interface %s" %(dvb_if))
        subprocess.check_output([
            "sysctl",
            "-w",
            "net.ipv4.conf." + sysctl_dvb_if + ".rp_filter=0"
        ])
    else:
        print("Reverse path filtering configuration cancelled")


def set_iptables_rule(net_if, ports):
    """Define rule on iptables to accept traffic via DVB interface

    Args:
        net_if : DVB network interface name
        ports  : ports used for blocks traffic and API traffic

    """

    print("\n------------------------------- Firewall Rules " +
          "--------------------------------")
    print("Configure firewall rules to accept Blocksat traffic arriving " +
          "at interface %s\ntowards UDP ports %s." %(net_if, ",".join(ports)))

    resp = input("Add corresponding ACCEPT rule on firewall? [Y/n] ") or "Y"

    if (resp.lower() == "y"):
        # Check current configuration
        res = subprocess.check_output([
            "iptables", "-L", "-v", "--line-numbers"
        ])

        # Is the rule already configured?
        header1 = ""
        header2 = ""
        for line in res.splitlines():
            if ("Chain INPUT" in line.decode()):
                header1 = line.decode()

            if ("destination" in line.decode()):
                header2 = line.decode()

            if (net_if in line.decode()):
                current_rule = line.decode().split()
                if (current_rule[3] == "ACCEPT" and
                    current_rule[4] == "udp" and
                    current_rule[6] == net_if and
                    current_rule[12] == ",".join(ports)):
                    print("Firewall rule already configured\n")
                    print(header1)
                    print(header2)
                    print(line.decode())
                    print("Skipping...")
                    return

        # Set up iptables rule
        cmd = [
            "iptables",
            "-I", "INPUT",
            "-p", "udp",
            "-i", net_if,
            "--match", "multiport",
            "--dports", ",".join(ports),
            "-j", "ACCEPT",
        ]
        logging.debug("> " + " ".join(cmd))
        subprocess.check_output(cmd)

        # Check results
        res = subprocess.check_output([
            "iptables", "-L", "-v", "--line-numbers"
        ])

        header1 = ""
        header2 = ""
        for line in res.splitlines():
            if ("Chain INPUT" in line.decode()):
                header1 = line.decode()

            if ("destination" in line.decode()):
                header2 = line.decode()

            if (net_if in line.decode()):
                print("Added iptables rule:\n")
                print(header1)
                print(header2)
                print(line.decode())
    else:
        print("Firewall configuration cancelled")


def launch(args):
    """Launch the DVB interface from scractch

    Handles the launch subcommand

    """

    if (args.debug):
        logging.basicConfig(level=logging.DEBUG)
        logging.debug('[Debug Mode]')
    else:
        logging.basicConfig(level=logging.INFO)

    # Find adapter
    adapter = find_adapter()

    # Interface name
    net_if = "dvb" + adapter + "_0"

    # Launch the DVB network interface
    dvbnet(adapter, net_if, ule=(not args.mpe))

    # Zap
    zap_ps = zap(adapter, args.chan_conf)

    # Set RP filters
    if (not args.skip_rp):
        set_rp_filters(net_if)

    # Set firewall rules
    if (not args.skip_firewall):
        set_iptables_rule(net_if, src_ports)

    # Set IP
    set_ip(net_if, args.ip)

    print("\n----------------------------------- Listening " +
          "----------------------------------")

    # Loop indefinitely over zap stdout/sdterr
    while True:
        line = zap_ps.stderr.readline()
        if (line):
            print('\r' + line, end='')
        else:
            time.sleep(1)


def reverse_path_subcommand(args):
    """Call function that sets reverse path filters

    Handles the reverse-path subcommand

    """
    set_rp_filters(args.interface)


def firewall_subcommand(args):
    """Call function that sets firewall rules

    Handles the firewall subcommand

    """
    set_iptables_rule(args.interface, src_ports)


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

    launch_parser.add_argument('--mpe', default=False, action='store_true',
                               help='Use MPE encapsulation instead of ULE ' +
                               '(default: False)')

    launch_parser.add_argument('--skip-rp', default=False, action='store_true',
                               help='Skip settting of reverse path filters ' + \
                               '(default: False)')

    launch_parser.add_argument('--skip-firewall', default=False,
                               action='store_true',
                               help='Skip configuration of firewall rules ' + \
                               '(default: False)')

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

    fwall_parser.set_defaults(func=firewall_subcommand)

    # Optional args
    parser.add_argument('--debug', action='store_true',
                        help='Debug mode (default: false)')

    # Parse and call corresponding subcommand
    args      = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
