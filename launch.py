#!/usr/bin/env python3
"""
Launch the DVB receiver
"""
import os, argparse, subprocess, re, time


def find_adapter():
    """Find the DVB adapter

    Returns:
        Adapter index

    """
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

    print("\nTuning DVB receiver")

    cmd = ["dvbv5-zap", "-P", "-c", conf_file, "-a", adapter, "-l", lnb,
           "-r", "ch2", "-v"]
    print("Running: " + " ".join(cmd))
    ps = subprocess.Popen(cmd, stderr=subprocess.PIPE,
                          universal_newlines=True)
    #   "-P" accepts all PIDs
    #   "-r" sets up MPEG-TS record
    #   "-v" sets verbose
    return ps


def dvbnet(ip_addr, netmask, adapter, pid=1, ule=True):
    """Start DVB network interface

    Args:
        ip_addr   : Target IP address for the DVB interface
        netmask   : Subnet mask
        adapter   : DVB adapter index
        pid       : PID to listen to
        ule       : Whether to use ULE framing

    Returns:
        Network interface name

    """

    # Check if interface already exists
    net_if = "dvb" + adapter + "_0"

    try:
        res = subprocess.check_output(["ifconfig", net_if])
    except subprocess.CalledProcessError as e:
        res = None
        pass

    # Create interface in case it doesn't
    if (res is None):
        if (ule):
            print("Using ULE encapsulation")
        else:
            print("Using MPE encapsulation")

        ule_arg = "-U" if ule else ""
        res = subprocess.check_output(["dvbnet", "-a", adapter, "-p",
                                   str(pid), ule_arg])
        print(res.decode())
        has_ip = False
    else:
        print("Interface %s already exists" %(net_if))
        ip_grep = re.findall("inet ", res.decode())
        has_ip  = (len(ip_grep) > 0)

    # Check if interface has IP:
    if (not has_ip):
        print("Assign IP address %s to %s" %(ip_addr, net_if))
        # Assign IP
        res = subprocess.check_output(["ifconfig", net_if, ip_addr,
                                       "netmask", netmask])
    else:
        print("%s already has an IP" %(net_if))

    return net_if


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

    print("\nBlocksat traffic is one-way and thus reverse path (RP) " +\
          "filtering must be disabled.")
    print("The automatic solution disables RP filtering on the DVB " + \
          "interface and enables RP filtering on all other interfaces.")

    resp = input("OK to proceed? [Y/n] ") or "Y"

    if (resp.lower() == "y"):
        # Check interfaces
        ifs = os.listdir("/proc/sys/net/ipv4/conf/")

        dvb_cfg =  subprocess.check_output([
            "sysctl",
            "net.ipv4.conf." + dvb_if + ".rp_filter"
        ])

        # Check current configuration of DVB interface and "all" rule:
        dvb_cfg =  subprocess.check_output([
            "sysctl",
            "net.ipv4.conf." + dvb_if + ".rp_filter"
        ]).split()[-1].decode()
        all_cfg =  subprocess.check_output([
            "sysctl",
            "net.ipv4.conf.all.rp_filter"
        ]).split()[-1].decode()

        if (dvb_cfg == "0" and all_cfg == "0"):
            print("Current RP filtering configurations are already sufficient")
            print("Skipping...")
            return

        # Enable all RP filters
        for interface in ifs:
            if (interface == "all"):
                continue

            print("Enabling reverse path filter on interface %s" %(interface))
            subprocess.check_output([
                "sysctl",
                "-w",
                "net.ipv4.conf." + interface + ".rp_filter=1"
            ])

        # Disable the overall RP filter
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
            "net.ipv4.conf." + dvb_if + ".rp_filter=0"
        ])
    else:
        print("Reverse path filtering configuration cancelled")


def set_iptables_rule(ip, ports):
    """Define rule on iptables to accept traffic via DVB interface

    Args:
        ip    : source IP address
        ports : ports used for blocks traffic and API traffic

    """

    print("\nFirewall rules are necessary to accept Blocksat traffic")
    print("Blocksat traffic will come from IP %s towards UDP ports %s" %(
        ip, ",".join(ports)
    ))

    resp = input("Add corresponding ACCEPT rule on firewall? [Y/n] ") or "Y"

    if (resp.lower() == "y"):
        # Check current configuration
        res = subprocess.check_output([
            "iptables", "-L", "--line-numbers"
        ])

        # Is the rule already configured?
        for line in res.splitlines():
            if (ip in line.decode()):
                current_rule = line.decode().split()
                if (current_rule[1] == "ACCEPT" and current_rule[4] == ip and
                    current_rule[8] == ",".join(ports)):
                    print("Firewall rule already configured")
                    print(line.decode())
                    print("Skipping...")
                    return

        # Set up iptables rule
        subprocess.check_output([
            "iptables",
            "-I", "INPUT",
            "-p", "udp",
            "-s", ip,
            "--match", "multiport",
            "--dports", ",".join(ports),
            "-j", "ACCEPT",
        ])

        # Check results
        res = subprocess.check_output([
            "iptables", "-L", "--line-numbers"
        ])

        for line in res.splitlines():
            if (ip in line.decode()):
                print("Added iptables rule:")
                print(line.decode())
    else:
        print("Firewall configuration cancelled")


def main():
    cwd    = os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser("DVB Receiver Launcher")
    parser.add_argument('-c', '--chan-conf',
                        default=os.path.join(cwd, 'channels.conf'),
                        help='Channel configurations file ' +
                        '(default: channels.conf)')
    parser.add_argument('-i', '--ip',
                        default='192.168.201.2',
                        help='IP address set for the DVB net interface ' +
                        '(default: 192.168.201.2)')
    parser.add_argument('-n', '--netmask',
                        default='255.255.255.252',
                        help='IP address set for the DVB net interface ' +
                        '(default: 255.255.255.252)')
    parser.add_argument('--mpe',
                        default=False,
                        action='store_true',
                        help='Use MPE encapsulation instead of ULE ' +
                        '(default: False)')
    parser.add_argument('--no-firewall',
                        default=False,
                        action='store_true',
                        help='Do not ask to set firewall rule for DVB traffic ' +
                        '(default: False)')
    args      = parser.parse_args()

    # Constants
    src_ip    = "192.168.200.2"
    src_ports = ["4433", "4434"]

    # Find adapter
    adapter = find_adapter()

    # Launch the DVB network interface
    net_if = dvbnet(args.ip, args.netmask, adapter, ule=(not args.mpe))

    # Set RP filters
    set_rp_filters(net_if)

    if (not args.no_firewall):
        set_iptables_rule(src_ip, src_ports)

    # Zap
    zap_ps = zap(adapter, args.chan_conf)

    while True:
        line = zap_ps.stderr.readline()
        if (line):
            print('\r' + line, end='')
        else:
            time.sleep(1)


if __name__ == '__main__':
    main()
