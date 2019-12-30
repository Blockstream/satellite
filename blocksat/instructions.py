"""Instructions for the user"""
from blocksat import util, defs
import textwrap


def _print_s400_instructions(info):
    """Print instruction for configuration of the Novra S400
    """
    util._print_header("Novra S400")

    print("The Novra S400 is standalone modem, connected as follows:\n")

    print(("LNB ----> S400 (RF1 Interface) -- "
           "S400 (LAN 1 Interface) ----> Host / Network\n"))

    print(textwrap.fill("The S400 will receive from satellite and will output "
                        "multicast-addressed IP packets. The host will then "
                        "listen to these packets. Hence, the next step is to "
                        "configure both the S400 and the host."))

    util._print_sub_header("S400 Configurations")
    print("First access the web user interface of the S400:")
    print()
    print("1. Go to Interfaces > RF1:\n")
    print("- DVB Mode: \"DVB-S2\"")
    print("- Carrier Freq.: {:.1f} MHz".format(info['freqs']['dl']))
    print("- LBand: {:.1f} MHz".format(info['freqs']['l_band']))
    print("- Symbol Rate: 1.0 MBaud")
    print("- MODCOD: AUTO")
    print("- Gold Code: 0")
    print("- Input Stream ID: 0")
    print("- LNB Power On: Enable")
    print("- L.O. Frequencies: {:.1f} MHz".format(info['freqs']['lo']))
    if (info['sat']['pol'] == "H"):
        print("- Polarization: Horiz./L")
    else:
        print("- Polarization: Vert./R")

    if (info['lnb']['universal'] and info['freqs']['dl'] > defs.ku_band_thresh):
        print("- Band (Tone): \"High/On\"")
    else:
        print("- Band (Tone): \"Low/On\"")
    print("- Long Line Compensation: Disabled")
    print()
    print("2. Go to Interfaces > Data (LAN1):\n")
    print(textwrap.fill("Configure the IP address of the data interface. "
                        "This is the interface that will deliver IP "
                        "packets (data packets) received over satellite."))
    print()
    print("3. Go to Interfaces > M&C (LAN2):\n")
    print(textwrap.fill("Configure the IP address of the management and "
                        "control (M&C) interface. "
                        "This is the interface that will be used exclusively "
                        "for M&C traffic."))
    print()
    print("4. Go to Services > Tun1:\n")
    print("Scroll to \"Manage MPE PIDs\"")
    for pid in defs.pids:
        print("- Enter %d on \"New PID\" and click \"Add\"." %(pid))

    util._print_sub_header("Host Configurations")
    print("1. Run the following command on the host:")
    print("\n```\nsudo ./blocksat.py standalone -i ifname\n```\n")
    print(textwrap.fill("where \'ifname\' should be replaced with the name "
                        "of the network interface that is connected to the "
                        "S400. This interface can be connected directly to "
                        "S400 or via switch(es)."))


def _print_sdr_instructions(info):
    """Print instruction for configuration of an SDR setup
    """
    util._print_header("SDR Setup")

    util._print_sub_header("Connections")

    print("An SDR-based setup is assembled as follows:\n")

    print("LNB ----> Power Supply ----> RTL-SDR ----> Host\n")
    print(("The power supply is typically a \"Single Wire Multiswitch\" (SWM) "
          "supply. In this scenario, the LNB must be connected to the "
           "**powered** port, labeled \“Signal to SWM\”, and the "
           "**non-powered** port of the supply, labeled as \“Signal to IRD\", "
           "must be connected to the RTL-SDR."))

    util._print_sub_header("Host Configuration")

