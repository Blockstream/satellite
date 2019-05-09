#!/usr/bin/env python
"""
Launch the DVB receiver
"""
import argparse, subprocess, re, time


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

    print("Tuning DVB receiver:")

    cmd = ["sudo", "dvbv5-zap", "-P", "-c", conf_file, "-a", adapter, "-l", lnb,
           "-r", "ch2", "-v"]
    print(" ".join(cmd))
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
        res = subprocess.check_output(["sudo", "ifconfig", net_if])
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
        res = subprocess.check_output(["sudo", "dvbnet", "-a", adapter, "-p",
                                   str(pid), ule_arg])
        print(res.decode())
        has_ip = False
    else:
        print("Interface %s already exists" %(net_if))
        ip_grep = re.findall("inet", res.decode())
        has_ip  = (len(ip_grep) > 0)

    # Check if interface has IP:
    if (not has_ip):
        print("Assign IP address %s to %s" %(ip_addr, net_if))
        # Assign IP
        res = subprocess.check_output(["sudo", "ifconfig", net_if, ip_addr,
                                       "netmask", netmask])
    else:
        print("%s already has an IP" %(net_if))

    return net_if


def main():
    parser = argparse.ArgumentParser("DVB Receiver Launcher")
    parser.add_argument('-c', '--chan-conf',
                        default='channels.conf',
                        help='Channel configurations file ' +
                        '(default: ~/channels.conf)')
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
    args      = parser.parse_args()

    # Find adapter
    adapter = find_adapter()

    # Zap
    zap_ps = zap(adapter, args.chan_conf)

    # Launch the DVB network interface
    net_if = dvbnet(args.ip, args.netmask, adapter, ule=(not args.mpe))

    while True:
        line = zap_ps.stderr.readline()
        if (line):
            print(line)
        time.sleep(0.001)


if __name__ == '__main__':
    main()
