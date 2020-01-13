"""Instructions for the user"""
from blocksat import util, defs, config
import textwrap


def _item(text):
    print(textwrap.fill(text, initial_indent="- ", subsequent_indent="  "))

def _print_s400_instructions(info):
    """Print instructions for configuration of the Novra S400
    """
    util._print_header("Novra S400")

    print("The Novra S400 is standalone modem, connected as follows:\n")

    print(("LNB ----> S400 (RF1 Interface) -- "
           "S400 (LAN 1 Interface) ----> Host / Network\n"))

    print(textwrap.fill("The S400 will receive data from satellite and will "
                        "output IP packets to the host over the network. Hence,"
                        " you will need to configure both the S400 and the "
                        "host."))

    input("\nPress Enter to continue...")

    util._print_sub_header("Connections")

    _item("Connect the LNB directly to interface RF1 of the S400 using a "
          "coaxial cable (for example an RG6 cable).")
    _item("Connect the S400's LAN1 interface to your computer or network.")

    input("\nPress Enter to continue...")

    util._print_sub_header("S400's web user interface (UI)")
    print("Next, you need to access the web UI of the S400:")
    _item(
        "Configure you host's network interface to the same subnet as the S400"
        ". By default, the S400 is configured with IP address 192.168.1.2 on "
        "LAN1 and 192.168.2.2 on LAN2. So, if you are connecting to LAN1, "
        "make sure your host's network interface has IP address 192.168.1.x, "
        "where \"x\" could be any number higher than 2. For example, you could "
        "configure your host's network interface with IP address 192.168.1.3.")
    _item("From your browser, access 192.168.1.2 (or 192.168.2.2 if "
          "connected to LAN 2).")
    _item("The web management console should open.")
    print()

    input("\nPress Enter to continue...")

    util._print_sub_header("S400 FW Version")
    print("In the web UI, go to System > About:")
    print("Confirm that S400's the Configuration Agent's version is 1.5.10 or higher.")
    print()

    input("\nPress Enter to continue...")

    util._print_sub_header("S400 Configurations")
    print("1. First you need to log in as admin, on the top right of the page.")
    _item("Password: \"password\"")
    print()

    print("2. Go to Interfaces > RF1 and configure as follows:\n")
    _item("DVB Mode: \"DVB-S2\"")
    _item("LBand: {:.1f} MHz".format(info['freqs']['l_band']))
    _item("Symbol Rate: 1.0 MBaud")
    _item("MODCOD: AUTO")
    _item("Gold Code: 0")
    _item("Input Stream ID: 0")
    _item("LNB Power On: Enable")
    _item("L.O. Frequencies: {:.1f} MHz".format(info['freqs']['lo']))
    if (info['sat']['pol'] == "H"):
        _item("Polarization: Horiz./L")
    else:
        _item("Polarization: Vert./R")

    if (info['lnb']['universal'] and info['freqs']['dl'] > defs.ku_band_thresh):
        _item("Band (Tone): \"High/On\"")
    else:
        _item("Band (Tone): \"Low/Off\"")
    _item("Long Line Compensation: Disabled")
    _item("Apply")
    print()

    print("3. Verify that the S400 is locked to Blockstream Satellite's signal")
    _item("Check the top panel's \"RF 1 Lock\" indicator. It should be green "
          "if your antenna is already pointed correctly. If not, you can work "
          "on the antenna pointing afterwards.")
    print()

    print("4. Go to Services > Tun1:\n")
    print("Scroll to \"Manage MPE PIDs\"")
    for pid in defs.pids:
        print("- Enter %d on \"New PID\" and click \"Add\"." %(pid))
    _item("Apply")
    print()

    print("** Optional configurations:")
    _item("If you prefer to use another IP address on LAN1 or LAN2, go to "
          "Interfaces > Data (LAN1) or Interfaces > M&C (LAN2) and "
          "configure the IP addresses. Note LAN 1 is the interface that "
          "will deliver the data packets received over satellite, whereas "
          "LAN2 is optional and exclusively for management.")
    print()


    input("\nPress Enter to continue...")

    util._print_sub_header("Host Configuration")
    print("1. Run the following command on the host:")
    print("\n```\nsudo ./blocksat.py standalone -i ifname\n```\n")
    print(textwrap.fill("where \'ifname\' should be replaced with the name "
                        "of the network interface that is connected to the "
                        "S400."))


def _print_usb_rx_instructions():
    """Print instructions for runnning with a Linux USB receiver
    """
    util._print_header("Next Steps")

    print("Now run:\n\nsudo ./blocksat.py launch\n\n")


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


def show(args):
    """Show instructions"""
    info = config.read_cfg_file()

    if (info['setup']['type'] == defs.standalone_setup_type):
        _print_s400_instructions(info)
    elif (info['setup']['type'] == defs.sdr_setup_type):
        pass
    elif (info['setup']['type'] == defs.linux_usb_setup_type):
        _print_usb_rx_instructions()


