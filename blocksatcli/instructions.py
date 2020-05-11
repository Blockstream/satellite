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

    util.prompt_for_enter()

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

    util.prompt_for_enter()

    util._print_sub_header("S400 FW Version")
    print("In the web UI, go to System > About:")
    print("Confirm that the version of the Configuration Agent is 1.6.1 or higher.")
    print()

    util.prompt_for_enter()

    util._print_sub_header("S400 Configurations")
    print("1. First you need to log in as admin, on the top right of the page.")
    _item("Password: \"password\"")
    print()

    print("2. Go to Interfaces > RF1 and configure as follows:\n")
    _item("DVB Mode: \"DVB-S2\"")
    _item("LBand: {:.1f} MHz".format(info['freqs']['l_band']))
    _item("Symbol Rate: {} MBaud".format(
        defs.sym_rate[info['sat']['alias']]/1e6))
    _item("MODCOD: VCM")
    _item("Gold Code: 0")
    _item("Input Stream ID: 0")
    _item("LNB Power On: Enable")
    _item("L.O. Frequencies: {:.1f} MHz".format(info['freqs']['lo']))

    if (info['lnb']['pol'].lower() == "dual" and info['lnb']['v1_pointed']):
        # If a dual-polarization LNB is already pointed for Blocksat v1,
        # then we must use the polarization that the LNB was pointed to
        # originally, regardless of the satellite signal's polarization. In
        # v1, what mattered the most was the power supply voltage, which
        # determined the polarization of the dual polarization LNBs. If the
        # power supply provides voltage >= 18 (often the case), then the LNB
        # necessarily operates currently with horizontal polarization. Thus,
        # the same polarization must be configured in the S400.
        if (info['lnb']["v1_psu_voltage"] >= 16): # 16VDC is a common threshold
            pol = "H"
        else:
            pol = "V"
    else:
        if (info['sat']['pol'] == "H"):
            pol = "H"
        else:
            pol = "V"

    pol_label = "Horiz./L" if pol == "H" else "Vert./R"

    _item("Polarization: {}".format(pol_label))

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

    util.prompt_for_enter()

    if (info['lnb']['pol'].lower() == "dual" and info['lnb']['v1_pointed'] and
        (pol != info['sat']['pol'])):
        util._print_sub_header("Notes")

        _item("The polarization that was suggested above assumes that you "
              "are going to use an LNB that is already pointed to {}, on a "
              "pre-existing SDR-based setup used for reception of the "
              "previous version of Blockstream Satellite (prior to the "
              "update to DVB-S2). It also assumes that you "
              "are not going to change the skew (polarization angle) of the "
              "LNB. The suggested polarization is exactly the same on which "
              "your LNB has been operating so far, i.e. {} polarization. "
              "However, note that your satellite signal has {} polarization. "
              "If you plan on re-pointing the LNB, please re-run the "
              "configuration helper (\"blocksat-cli cfg\") and "
              "answer that you are not reusing an already pointed LNB.".format(
                  info['sat']['name'],
                  "horizontal" if pol == "H" else "vertical",
                  "horizontal" if info['sat']['pol'] == "H" else "vertical"
              ))

        util.prompt_for_enter()

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
    configuring the demodulator using specific DVB-S2 tools. Hence, next, you
    need to prepare the host for driving the {0}.
    """.format(name))

    util._print_sub_header("Hardware Connections")

    print("The {} should be connected as follows:\n".format(name))

    print(("LNB ----> {0} (LNB Interface) -- "
           "{0} (USB Interface) ----> Host\n".format(name)))

    _item("Connect the LNB directly to \"LNB IN\" of the {} using a coaxial"
          " cable (an RG6 cable is recommended).".format(name))
    _item("Connect the {}'s USB interface to your computer.".format(name))

    util.prompt_for_enter()

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

    util.prompt_for_enter()

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

    _print("""
    If dvb-apps is not available on your distribution (for example on Fedora 31
    and 32), you can build it from source by running:
    """)

    build_info = """    git clone https://github.com/Blockstream/dvb-apps
    cd dvb-apps
    make
    sudo make install
    """

    print(build_info)

    util.prompt_for_enter()

    util._print_sub_header("Configure the Host")

    print("Run the following as root:")

    print("\n    sudo blocksat-cli usb config\n")

    _print("""
    This script will create network interfaces in order to handle the IP traffic
    received via the satellite link. It will define arbitrary IP addresses to the
    interfaces. To define a specific IP instead, use command-line argument `--ip`.
    """)

    _print(
        "NOTE: root privileges are required in order to configure firewall "
        "and reverse path (RP) filtering, as well as accessing the adapter "
        "at `/dev/dvb`. You will be prompted to accept or refuse the "
        "firewall and RP configurations.")

    util.prompt_for_enter()

    util._print_sub_header("Launch")

    print("Finally, launch the DVB-S2 interface by running:")

    print("\n    blocksat-cli usb launch\n")

    util.prompt_for_enter()

def _print_sdr_instructions(info):
    """Print instruction for configuration of an SDR setup
    """
    util._print_header("SDR Setup")

    util._print_sub_header("Connections")

    print("The SDR setup is connected as follows:\n")

    print("LNB ----> Power Supply ----> RTL-SDR ----> Host\n")

    _item("Connect the RTL-SDR USB dongle to your host PC.")
    _item("Connect the **non-powered** port of the power supply (labeled as "
          "\"Signal to IRD\") to the RTL-SDR using an SMA cable and an "
          "SMA-to-F adapter.")
    _item("Connect the **powered** port (labeled \"Signal to SWM\") of the "
          "power supply to the LNB using a coaxial cable (an RG6 cable is "
          "recommended).")

    print()
    _print("IMPORTANT: Do NOT connect the powered port of the power supply "
           "to the SDR interface. Permanent damage may occur to your SDR "
           "and/or your computer.")

    util.prompt_for_enter()

    util._print_sub_header("Software Requirements")

    print("The SDR-based setup relies on the applications listed below:\n")

    _item("leandvb: a software-based DVB-S2 demodulator.")
    _item("rtl_sdr: reads samples taken by the RTL-SDR and feeds them into leandvb.")
    _item("TSDuck: unpacks the output of leandvb and produces "
          "IP packets to be fed to Bitcoin Satellite.")
    _item("Gqrx: useful for spectrum visualization during antenna pointing.")

    print("\nTo install them, run:")
    print("""
    blocksat-cli deps install
    """)

    _print(
        """
        NOTE: This command assumes and has been tested with Ubuntu
        18.04 and Fedora 31. Please adapt if necessary in case you
        are using another Linux distribution or version.""")

    _print("If you prefer to build all software components manually, please "
           "refer to the SDR Guide at \"doc/sdr.md\" or:")
    print("https://github.com/Blockstream/satellite/blob/master/doc/sdr.md")

    util.prompt_for_enter()

    util._print_sub_header("Configuration")

    _print("Next, you can generate the configurations that are needed for gqrx "
           "by running:")

    print("    blocksat-cli gqrx-conf")

    util.prompt_for_enter()

    util._print_sub_header("Running")

    _print("You should now be ready to launch the SDR receiver. You can run it "
           "by executing:")

    print("    blocksat-cli sdr\n")
    print("Or, in GUI mode:\n")
    print("    blocksat-cli sdr --gui\n")

    _print("For further options, please refer to the SDR Guide "
           "at \"doc/sdr.md\" or:")
    print("https://github.com/Blockstream/satellite/blob/master/doc/sdr.md")

    util.prompt_for_enter()


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

    if (lnb['universal'] and (setup['type'] == defs.sdr_setup_type)):
        if (sat['dl_freq'] > defs.ku_band_thresh):
            print("NOTE regarding Universal LNB:\n")

            print(textwrap.fill(("The DL frequency of {} is in Ku high "
                                 "band (> {:.1f} MHz). Hence, you need to use "
                                 "the higher frequency LO ({:.1f} MHz) of your "
                                 "Universal LNB. This requires a 22 kHz tone "
                                 "to be sent to the LNB."
            ).format(sat['alias'], defs.ku_band_thresh, lo_freq)))
            print()
            print(textwrap.fill(("With a software-defined setup, you will "
                                 "need to place a 22 kHz tone generator "
                                 "inline between the LNB and the power "
                                 "inserter. Typically the tone generator "
                                 "uses power from the power inserter while "
                                 "delivering the tone directly to the "
                                 "LNB.")))

    util.prompt_for_enter()


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
        util.prompt_for_enter()

    if ((lnb['pol'] == "Dual") and (setup['type'] == defs.sdr_setup_type)):
        util._print_header("LNB Information")
        logging.warning(textwrap.fill(
            "Your LNB has dual polarization. Check the voltage of your power "
            "supply in order to discover the polarization on which your LNB "
            "will operate."))
        util.prompt_for_enter()


def _print_next_steps():
    util._print_header("Next Steps")
    _print("""
    At this point, if your dish is already correctly pointed, you should be able to
    start receiving data in Bitcoin Satellite.
    """)

    print("You can generate a bitcoin.conf configuration file for Bitcoin Satellite using:")
    print("\n    blocksat-cli btc\n")

    print("For further information, refer to \"doc/bitcoin.md\" or:\n")
    print("https://github.com/Blockstream/satellite/blob/master/doc/bitcoin.md\n")

    _print("""If your antenna is not pointed yet, please follow the
    antenna alignment guide available at \"doc/antenna-pointing.md\" or:""")
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
        _print_sdr_instructions(info)
    elif (info['setup']['type'] == defs.linux_usb_setup_type):
        _print_usb_rx_instructions(info)

    _print_next_steps()
