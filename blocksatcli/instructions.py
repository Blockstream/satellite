"""Instructions for the user"""
from argparse import ArgumentDefaultsHelpFormatter
from . import util, defs, config
import textwrap, logging


def _item(text):
    print(textwrap.fill(text, initial_indent="- ", subsequent_indent="  "))


def _print(text):
    text = " ".join(text.replace("\n", "").split())
    print(textwrap.fill(text))
    print()


def _print_s400_instructions(info):
    """Print instructions for configuration of the Novra S400
    """
    util._print_header("Novra S400")

    _print("""
    The Novra S400 is a standalone demodulator, which will receive data from
    satellite and output IP packets to the host over the network. Hence, you will
    need to configure both the S400 and the host.
    """)

    util._print_sub_header("Connections")

    _print("The Novra S400 can be connected as follows:")


    print(("LNB ----> S400 (RF1 Interface) -- "
           "S400 (LAN 1 Interface) ----> Host / Network\n"))


    _item("Connect the LNB directly to interface RF1 of the S400 using a "
          "coaxial cable (an RG6 cable is recommended).")
    _item("Connect the S400's LAN1 interface to your computer or network.")

    input("\nPress Enter to continue...")

    util._print_sub_header("S400's web user interface (UI)")
    print("Next, you need to access the web UI of the S400:\n")
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
    print("Confirm that the version of the Configuration Agent is 1.5.10 or higher.")
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
    _item("Check the \"RF 1 Lock\" indicator at the top of the page or the "
          "status LED in the S400's front panel. It should be green (locked) "
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

    _print("""
    In order to receive the traffic from the S400, you will need some networking
    configurations on your host. Such configurations are indicated and executed
    by running:
    """)

    print("\n```\nblocksat-cli standalone -i ifname\n```\n")
    print(textwrap.fill("where \'ifname\' should be replaced with the name "
                        "of the network interface that is connected to the "
                        "S400."))


def _print_usb_rx_instructions(info):
    """Print instructions for runnning with a Linux USB receiver
    """

    name = (info['setup']['vendor'] + " " + info['setup']['model']).strip()

    util._print_header(name)

    _print("""
    The {0} is a USB demodulator, which will receive data from satellite and
    will output data to the host over USB. The host, in turn, is responsible for
    configuring the modem using specific DVB-S2 tools. Hence, next, you need to
    prepare the host for driving the {0}.
    """.format(name))

    util._print_sub_header("Hardware Connections")

    print("The {} should be connected as follows:\n".format(name))

    print(("LNB ----> {0} (LNB Interface) -- "
           "{0} (USB Interface) ----> Host\n".format(name)))

    _item("Connect the LNB directly to \"LNB IN\" of the {} using a coaxial"
          " cable (an RG6 cable is recommended).".format(name))
    _item("Connect the {}'s USB interface to your computer.".format(name))

    input("\nPress Enter to continue...")

    util._print_sub_header("Drivers")

    _print("""
    Before anything else, note that specific device drivers are required in order to
    use the {0}. Please, do note that driver installation can cause corruptions
    and, therefore, it is safer and **strongly recommended** to use a virtual
    machine for running the {0}. If you do so, please note that all commands
    recommended in the remainder of this page are supposed to be executed in the
    virtual machine.
    """.format(name))
    _print("""
    Next, install the drivers for the {0}. A helper script is available in the
    `util` directory from the root of this repository:
    """.format(name))

    _item("From the util/ folder, run:")
    print("""
    ./tbsdriver.sh
    """)
    print("Once the script completes the installation, reboot the virtual machine.")

    input("\nPress Enter to continue...")

    util._print_sub_header("Host Requirements")

    print("Now, install all pre-requisites (in the virtual machine):")

    install_info = """
    On Ubuntu/Debian:

    sudo apt apt update
    sudo apt install python3 iproute2 iptables dvb-apps dvb-tools


    On Fedora

    sudo dnf update
    sudo dnf install python3 iproute iptables dvb-apps v4l-utils
    """
    print(install_info)

    input("\nPress Enter to continue...")

    util._print_sub_header("Launch")

    print("Finally, launch the DVB-S2 interface by running:")

    print("\n    blocksat-cli usb\n")

    _print("""
    This script will set an arbitrary IP address to the network interface that is
    created in Linux in order to handle the IP traffic received via the satellite
    link. To define a specific IP instead, run the above with `--ip target_ip`
    argument, where `target_ip` is the IP of interest.
    """)

    _print(
        "NOTE: root privileges are required in order to configure firewall "
        "and reverse path (RP) filtering, as well as accessing the adapter "
        "at `/dev/dvb`. You will be prompted to accept or refuse the "
        "firewall and RP configurations that are executed as root.")

    input("\nPress Enter to continue...")

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


def _print_freq_info(info):
    """Print summary of frequencies of interest"""
    sat     = info['sat']
    setup   = info['setup']
    lnb     = info['lnb']
    lo_freq = info['freqs']['lo']
    l_freq  = info['freqs']['l_band']

    util._print_header("Frequencies")

    print("| Downlink %2s band frequency                     | %8.2f MHz |" %(sat['band'], sat['dl_freq']))
    print("| Your LNB local oscillator (LO) frequency       | %8.2f MHz |" %(lo_freq))
    print("| L-band frequency to configure on your receiver | %7.2f MHz  |" %(l_freq))
    print()

    if (lnb['universal']):
        print("NOTE regarding Universal LNB:\n")
        if (sat['dl_freq'] > defs.ku_band_thresh):
            print(textwrap.fill(("The DL frequency of {} is in Ku high "
                                 "band (> {:.1f} MHz). Hence, you need to use "
                                 "the higher frequency LO ({:.1f} MHz) of your "
                                 "LNB. This requires a 22 kHz tone to be sent "
                                 "to the LNB."
            ).format(sat['alias'], defs.ku_band_thresh, lo_freq)))
            print()
            if (setup['type'] == defs.sdr_setup_type):
                print(textwrap.fill(("With a software-defined setup, you will "
                                     "need to place a 22 kHz tone generator "
                                     "inline between the LNB and the power "
                                     "inserter. Typically the tone generator "
                                     "uses power from the power inserter while "
                                     "delivering the tone directly to the "
                                     "LNB.")))
            else:
                print("The {} {} modem will generate the 22 kHz tone.".format(
                    setup['vendor'], setup['model']))
        else:
            print(textwrap.fill("The DL frequency of {} is in Ku low \
            band (< {:.1f} MHz). Hence, you need to use the lower (default) \
            frequency LO of your LNB.".format(sat['alias'], defs.ku_band_thresh)))

    input("\nPress Enter to continue...")


def _print_lnb_info(info):
    """Print important waraning based on LNB choice"""
    lnb   = info['lnb']
    sat   = info['sat']
    setup = info['setup']

    if ((lnb['pol'] != "Dual") and (lnb['pol'] != sat['pol'])):
        util._print_header("LNB Information")
        lnb_pol = "Vertical" if lnb['pol'] == "V" else "Horizontal"
        logging.warning(textwrap.fill(
            "Your LNB has {} polarization and the signal from {} has the "
            "opposite polarization.".format(lnb_pol, sat['name'])))
        input("\nPress Enter to continue...")

    if ((lnb['pol'] == "Dual") and (setup['type'] == defs.sdr_setup_type)):
        util._print_header("LNB Information")
        logging.warning(textwrap.fill(
            "Your LNB has dual polarization. Check the voltage of your power "
            "supply in order to discover the polarization on which your LNB "
            "will operate."))
        input("\nPress Enter to continue...")


def _print_next_steps():
    util._print_header("Next Steps")
    _print("""
    At this point, if your dish is already correctly pointed, you should be able to
    start receiving data in Bitcoin FIBRE.
    """)

    print("You can generate a bitcoin.conf configuration file for FIBRE using:")
    print("\n    blocksat-cli btc\n")

    print("For further information, refer to:\n")
    print("https://github.com/Blockstream/satellite/blob/master/doc/fibre.md\n")

    _print("""If your antenna is not pointed yet, please follow the
    antenna alignment guide available at:""")
    print("https://github.com/Blockstream/satellite/blob/master/doc/antenna-pointing.md\n")


def subparser(subparsers):
    """Argument parser of instructions command"""
    p = subparsers.add_parser('instructions',
                              description="Instructions for Blocksat Rx setup",
                              help='Read instructions for the receiver setup',
                              formatter_class=ArgumentDefaultsHelpFormatter)
    p.set_defaults(func=show)
    return p


def show(args):
    """Show instructions"""
    info = config.read_cfg_file(args.cfg_file, args.cfg_dir)

    if (info is None):
        return

    _print_freq_info(info)
    _print_lnb_info(info)

    if (info['setup']['type'] == defs.standalone_setup_type):
        _print_s400_instructions(info)
    elif (info['setup']['type'] == defs.sdr_setup_type):
        pass
    elif (info['setup']['type'] == defs.linux_usb_setup_type):
        _print_usb_rx_instructions(info)

    _print_next_steps()
