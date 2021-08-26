"""Instructions for the user"""
import logging
import os
import textwrap
from argparse import ArgumentDefaultsHelpFormatter

from . import util, defs, config


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
    The Novra S400 is a standalone receiver, which will receive data from
    satellite and output IP packets to the host over the network. Hence, you
    will need to configure both the S400 and the host.
    """)

    util._print_sub_header("Connections")

    _print("The Novra S400 can be connected as follows:")

    print(("LNB ----> S400 (RF1 Interface) -- "
           "S400 (LAN 1 Interface) ----> Host / Network\n"))

    _item("Connect the LNB directly to interface RF1 of the S400 using a "
          "coaxial cable (an RG6 cable is recommended).")
    _item("Connect the S400's LAN1 interface to your computer or network.")

    util.prompt_for_enter()

    util._print_sub_header("Network Connection")

    _print("Next, make sure the S400 receiver is reachable by the host.")

    _print("First, configure your host's network interface to the same subnet "
           "as the S400. By default, the S400 is configured with IP address "
           "192.168.1.2 on LAN1 and 192.168.2.2 on LAN2. Hence, if you "
           "connect to LAN1, make sure your host's network interface has IP "
           "address 192.168.1.x, where \"x\" could be any number higher than "
           "2. For example, you could configure your host's network interface "
           "with IP address 192.168.1.3.")

    _print("After that, open the browser and access 192.168.1.2 (or "
           "192.168.2.2 if connected to LAN 2). The web management console "
           "should open up successfully.")

    print()

    util.prompt_for_enter()

    util._print_sub_header("Software Requirements")

    _print("Next, install all software pre-requisites on your host. Run:")

    print("    blocksat-cli deps install\n")

    _print("""
    NOTE: this command supports the apt, dnf, and yum package managers.""")

    util.prompt_for_enter()

    util._print_sub_header("Receiver and Host Configuration")

    print("Now, configure the S400 receiver and the host by running:")

    print("\n    blocksat-cli standalone cfg\n")

    _print("""If you would like to review the changes that will be made to the
    host before applying them, first run the command in dry-run mode:""")

    print("    blocksat-cli standalone cfg --dry-run\n\n")

    util.prompt_for_enter()

    util._print_sub_header("Monitoring")

    print("Finally, you can monitor your receiver by running:")

    print("\n    blocksat-cli standalone monitor\n\n")

    util.prompt_for_enter()


def _print_usb_rx_instructions(info):
    """Print instructions for runnning with a Linux USB receiver
    """

    name = (info['setup']['vendor'] + " " + info['setup']['model']).strip()

    util._print_header(name)

    _print("""
    The {0} is a USB receiver, which will receive data from satellite and will
    output data to the host over USB. The host, in turn, is responsible for
    configuring the receiver using specific DVB-S2 tools. Hence, next, you need
    to prepare the host for driving the {0}.
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
    Before anything else, note that specific device drivers are required in
    order to use the {0}. Please, do note that driver installation can cause
    corruptions and, therefore, it is safer and **strongly recommended** to use
    a virtual machine for running the {0}. If you do so, please note that all
    commands recommended in the remainder of this page are supposed to be
    executed in the virtual machine.
    """.format(name))

    _print("Next, install the drivers for the {0} by running:".format(name))

    print("""
    blocksat-cli deps tbs-drivers
    """)

    print("Once the script completes the installation, reboot the virtual "
          "machine.")

    util.prompt_for_enter()

    util._print_sub_header("Host Requirements")

    print(
        "Now, install all pre-requisites (in the virtual machine) by running:")

    print("""
    blocksat-cli deps install
    """)

    _print("""
    NOTE: this command supports the apt, dnf, and yum package managers. For
    other package managers, refer to the instructions at:""")
    print(defs.user_guide_url + "doc/tbs.html")

    util.prompt_for_enter()

    util._print_sub_header("Configure the Host")

    _print(
        """Next, you need to create and configure the network interfaces that
    will output the IP traffic received via the TBS5927. You can apply all
    configurations by running the following command:""")

    print("\n    blocksat-cli usb config\n")

    _print("""If you would like to review the changes that will be made before
    applying them, first run the command in dry-run mode:
    """)

    print("\n    blocksat-cli usb config --dry-run\n")

    _print("""
    Note this command will define arbitrary IP addresses to the interfaces. If
    you need (or want) to define specific IP addresses instead, for example to
    avoid IP address conflicts, use command-line argument `--ip`.
    """)

    _print(
        """Furthermore, note that this configuration is not persistent across
    reboots. After a reboot, you need to run `blocksat-cli usb config`
    again.""")

    util.prompt_for_enter()

    util._print_sub_header("Launch")

    print("Finally, start the receiver by running:")

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

    _item("leandvb: a software-based DVB-S2 receiver application.")
    _item("rtl_sdr: reads samples taken by the RTL-SDR and feeds them into "
          "leandvb.")
    _item("TSDuck: unpacks the output of leandvb and produces "
          "IP packets to be fed to Bitcoin Satellite.")
    _item("Gqrx: useful for spectrum visualization during antenna pointing.")

    print("\nTo install them, run:")
    print("""
    blocksat-cli deps install
    """)

    _print("""
        NOTE: This command supports the two most recent Ubuntu LTS, Fedora, and
        CentOS releases. In case you are using another Linux distribution or
        version, please refer to the manual compilation and installation
        instructions at:""")
    print(defs.user_guide_url + "doc/sdr.html")

    util.prompt_for_enter()

    util._print_sub_header("Configuration")

    _print(
        "Next, you can generate the configurations that are needed for gqrx "
        "by running:")

    print("    blocksat-cli gqrx-conf")

    util.prompt_for_enter()

    util._print_sub_header("Running")

    _print(
        "You should now be ready to launch the SDR receiver. You can run it "
        "by executing:")

    print("    blocksat-cli sdr\n")
    print("Or, in GUI mode:\n")
    print("    blocksat-cli sdr --gui\n")

    util.prompt_for_enter()


def _print_sat_ip_instructions(info):

    util._print_header("Sat-IP Setup")

    _print("""The Sat-IP setup relies on the Blockstream Satellite Base
    Station (available on Blockstream Store), an all-in-one flat-panel antenna
    with an integrated receiver and LNB. This device receives the satellite
    signal and outputs IP packets to one or more Sat-IP clients listening to
    it in the local network.""")

    _print("The following steps explain how you can connect to the base "
           "station device to receive the Blockstream Satellite traffic.")

    util.prompt_for_enter()

    util._print_sub_header("Connections")

    _item("Connect the Ethernet cable from your switch or computer's network "
          "adapter directly to the antenna's Sat>IP port.")

    _item("If your switch/adapter does not support Power over Ethernet (PoE), "
          "insert a PoE injector in-line between the switch/adapter and the "
          "antenna's Sat-IP port. Connect the injector's PoE-enabled port to "
          "the Sat-IP antenna and the non-powered (non-PoE) port to the "
          "switch/adapter.")

    print()
    _print("IMPORTANT: If using a PoE injector, make sure you are connecting "
           "the correct ports. Permanent damage may occur to your switch or "
           "network adapter otherwise.")

    util.prompt_for_enter()

    util._print_sub_header("Software Requirements")

    _print("Next, install all software pre-requisites on your host. Run:")

    print("    blocksat-cli deps install\n")

    _print("""
    NOTE: this command supports the apt, dnf, and yum package managers.""")

    util.prompt_for_enter()

    util._print_sub_header("Running")

    _print("You should now be ready to launch the Sat-IP client. You can run "
           "it by executing:")

    print("    blocksat-cli sat-ip\n")

    util.prompt_for_enter()


def _print_freq_info(info):
    """Print summary of frequencies of interest"""
    sat = info['sat']
    setup = info['setup']
    lnb = info['lnb']
    lo_freq = info['freqs']['lo']
    l_freq = info['freqs']['l_band']

    util._print_header("Frequencies")

    print("For your information, your setup relies on the following "
          "frequencies:\n")
    print("| Downlink %2s band frequency            | %8.2f MHz |" %
          (sat['band'], sat['dl_freq']))
    print("| LNB local oscillator (LO) frequency   | %8.2f MHz |" % (lo_freq))
    print("| Receiver L-band frequency             | %7.2f MHz  |" % (l_freq))
    print()

    if (lnb['universal'] and (setup['type'] == defs.sdr_setup_type)):
        if (sat['dl_freq'] > defs.ku_band_thresh):
            print("NOTE regarding Universal LNB:\n")

            print(
                textwrap.fill(
                    ("The DL frequency of {} is in Ku high "
                     "band (> {:.1f} MHz). Hence, you need to use "
                     "the higher frequency LO ({:.1f} MHz) of your "
                     "Universal LNB. This requires a 22 kHz tone "
                     "to be sent to the LNB.").format(sat['alias'],
                                                      defs.ku_band_thresh,
                                                      lo_freq)))
            print()
            print(
                textwrap.fill(("With a software-defined setup, you will "
                               "need to place a 22 kHz tone generator "
                               "inline between the LNB and the power "
                               "inserter. Typically the tone generator "
                               "uses power from the power inserter while "
                               "delivering the tone directly to the "
                               "LNB.")))

    util.prompt_for_enter()


def _print_lnb_info(info):
    """Print important waraning based on LNB choice"""
    lnb = info['lnb']
    sat = info['sat']
    setup = info['setup']

    if ((lnb['pol'] != "Dual") and (lnb['pol'] != sat['pol'])):
        util._print_header("LNB Information")
        lnb_pol = "Vertical" if lnb['pol'] == "V" else "Horizontal"
        logging.warning(
            textwrap.fill(
                "Your LNB has {} polarization and the signal from {} has the "
                "opposite polarization.".format(lnb_pol, sat['name'])))
        util.prompt_for_enter()

    if ((lnb['pol'] == "Dual") and (setup['type'] == defs.sdr_setup_type)):
        util._print_header("LNB Information")
        logging.warning(
            textwrap.fill(
                "Your LNB has dual polarization. Check the voltage of your "
                "power supply in order to discover the polarization on which "
                "your LNB will operate."))
        util.prompt_for_enter()


def _print_next_steps():
    util._print_header("Next Steps")
    _print("""
    At this point, if your dish is already correctly pointed, you should be
    able to start receiving data on Bitcoin Satellite.
    """)

    print("You can generate a bitcoin.conf configuration file for Bitcoin "
          "Satellite using:")
    print("\n    blocksat-cli btc\n")

    _print("Next, if you are running Ubuntu, Fedora, or CentOS, you can "
           "install bitcoin-satellite by running:")
    print("    blocksat-cli deps install --btc\n")

    _print("Note that bitcoin-satellite is a fork of bitcoin core, and, "
           "as such, it installs applications with the same name (bitcoind, "
           "bitcoin-cli, bitcoin-qt, and bitcoin-tx). Hence, the "
           "bitcoin-satellite installation will fail if you already have "
           "bitcoin core installed.")

    print("For further information, refer to:\n")
    print(defs.user_guide_url + "doc/bitcoin.html\n")

    _print("""If your antenna is not pointed yet, please follow the
    antenna alignment guide at:""")
    print(defs.user_guide_url + "doc/antenna-pointing.html\n")


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
    info = config.read_cfg_file(args.cfg, args.cfg_dir)

    if (info is None):
        return

    os.system('clear')
    _print_lnb_info(info)

    if (info['setup']['type'] == defs.standalone_setup_type):
        _print_s400_instructions(info)
    elif (info['setup']['type'] == defs.sdr_setup_type):
        _print_sdr_instructions(info)
    elif (info['setup']['type'] == defs.linux_usb_setup_type):
        _print_usb_rx_instructions(info)
    elif (info['setup']['type'] == defs.sat_ip_setup_type):
        _print_sat_ip_instructions(info)

    _print_next_steps()
