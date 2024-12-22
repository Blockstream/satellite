"""Instructions for the user"""
import logging
import os
import textwrap
from argparse import ArgumentDefaultsHelpFormatter

from . import config, defs, util


def _item(text):
    print(textwrap.fill(text, initial_indent="- ", subsequent_indent="  "))


def _code(text):
    print(textwrap.fill(text, initial_indent="    "))
    print()


def _url(text):
    print("\033[4m" + text + "\033[0m" + "\n")


def _paragraph(text, text_wrap=True):
    text = " ".join(text.replace("\n", "").split())
    if text_wrap:
        print(textwrap.fill(text))
    else:
        print(text)
    print()


def _print(text,
           style='paragraph',
           end_linebreak=False,
           end_prompt=False,
           text_wrap=True):
    assert (style
            in ['header', 'subheader', 'paragraph', 'item', 'code', 'url'])

    if style == 'header':
        util.print_header(text)
    elif style == 'subheader':
        util.print_sub_header(text)
    elif style == 'item':
        _item(text)
    elif style == 'code':
        _code(text)
    elif style == 'url':
        _url(text)
    else:
        _paragraph(text, text_wrap)

    if end_linebreak:
        print()

    if end_prompt:
        util.prompt_for_enter()


def _print_s400_instructions(gui=False):
    """Print instructions for configuration of the Novra S400
    """
    _print("Novra S400", style="header")

    _print(
        "The Novra S400 is a standalone receiver. It receives a satellite "
        "signal fed via its coaxial interface and outputs IP packets to one "
        "or multiple hosts listening to it in the local network. "
        "This section explains how to configure both the Novra S400 modem and "
        "the host(s) of interest.")

    _print("Connections", style="subheader")

    _print("The Novra S400 can be connected as follows:")

    _print(
        "LNB ----> S400 (RF1 Interface) -- "
        "S400 (LAN 1 Interface) ----> Host / Network",
        text_wrap=False)

    _print(
        "Connect the LNB directly to interface RF1 of the S400 using a "
        "coaxial cable. An RG6 cable is recommended.",
        style="item")
    _print("Connect the S400's LAN1 interface to your computer or network.",
           style="item",
           end_prompt=True)

    _print("Network Connection", style="subheader")

    _print("Next, make sure the S400 receiver is reachable by the host.")

    _print("First, configure your host's network interface to the same subnet "
           "as the S400. By default, the S400 is configured with IP address "
           "192.168.1.2 on LAN1 and 192.168.2.2 on LAN2. Hence, if you "
           "connect to LAN1, make sure your host's network interface has IP "
           "address 192.168.1.x, where \"x\" could be any number higher than "
           "2. For example, you could configure your host's network interface "
           "with IP address 192.168.1.3.")

    _print(
        "After that, open the browser and access 192.168.1.2 (or "
        "192.168.2.2 if connected to LAN 2). The web management console "
        "should open up successfully.",
        end_prompt=True)

    if not gui:
        _print("Software Requirements", style="subheader")

        _print("Next, install all software pre-requisites on your host. Run:")

        _print("blocksat-cli deps install\n", style="code")

        _print(
            "NOTE: this command supports the apt, dnf, and yum package "
            "managers.",
            end_prompt=True)

        _print("Receiver and Host Configuration", style="subheader")

        _print("Now, configure the S400 receiver and the host by running:")

        _print("blocksat-cli standalone cfg", style="code")

        _print("If you would like to review the changes that will be made "
               "to the host before applying them, first run the command in "
               "dry-run mode:")

        _print("blocksat-cli standalone cfg --dry-run",
               style="code",
               end_prompt=True)

        _print("Monitoring", style="subheader")

        _print("Finally, you can monitor your receiver by running:")

        _print("blocksat-cli standalone monitor",
               style="code",
               end_prompt=True)
    else:
        _print("Configuration and Monitoring", style="subheader")

        _print("You can start your receiver by clicking on "
               "the \"Run Receiver\" button on the \"Receiver\" tab. "
               "After that, the GUI will automatically check if all the "
               "software dependencies are installed on your host "
               "and proceed with the receiver and host configuration. ")

        _print("Once the configuration is complete, the GUI will "
               "automatically enable the receiver and start monitoring it. "
               " The receiver status metrics will be available in "
               "real time on the \"Receiver\" tab.")


def _print_usb_rx_instructions(info, gui=False):
    """Print instructions for runnning with a Linux USB receiver
    """

    name = (info['setup']['vendor'] + " " + info['setup']['model']).strip()

    _print(name, style="header")

    _print(
        "The {0} is a USB-based DVB-S2 receiver. It receives the satellite "
        "signal fed via a coaxial interface and outputs data to the host over "
        "USB. It is also configured directly via USB, and the host is "
        "responsible for setting such configurations using specific Linux "
        "tools. ".format(name))

    _print("The instructions that follow prepare the host for driving the "
           "{0} receiver.".format(name))

    _print("Hardware Connections", style="subheader")

    _print("The {} should be connected as follows:".format(name))

    _print("LNB ----> {0} (LNB Interface) -- "
           "{0} (USB Interface) ----> Host".format(name),
           text_wrap=False)

    _print("Connect the LNB directly to \"LNB IN\" of the {} using a coaxial"
           " cable (an RG6 cable is recommended).".format(name),
           style="item")
    _print("Connect the {}'s USB2.0 interface to your computer.".format(name),
           style="item")
    if (info['setup']['model'] == "5520SE"):
        power_up_str = "Connect both male connectors of the dual-male " + \
            "USB Y cable to your host."
    else:
        power_up_str = "Connect the 12V DC power supply."
    _print("Power up the {} device. {} ".format(name, power_up_str),
           style="item",
           end_prompt=True)

    if not gui:
        _print("Drivers", style="subheader")

        _print(
            "Next, you will need to install specific device drivers to use "
            "the {0}. These are installed by rebuilding and rewriting the "
            "Linux Media drivers. Hence, if you are not setting up a "
            "dedicated machine to host the {0}, it would be safer and "
            "recommended to use a virtual machine (VM) as the receiver host "
            "so that the drivers can be installed directly on the VM instead "
            "of your main machine.".format(name))

        _print(
            "Next, install the drivers for the {0} by running:".format(name))

        _print("blocksat-cli deps tbs-drivers\n", style="code")

        _print(
            "Once the script completes the installation, reboot the machine.",
            end_prompt=True)

        _print("Host Requirements", style="subheader")

        _print("Next, install all the software pre-requisites by running:")

        _print("blocksat-cli deps install", style="code")

        _print(
            "NOTE: this command supports the apt, dnf, and yum package "
            "managers. For other package managers, refer to the instructions "
            "at:")
        _print(defs.user_guide_url + "doc/tbs.html",
               style="url",
               end_prompt=True)

        _print("Configure the Host", style="subheader")

        _print("Next, you need to create and configure the network interface "
               "that will output the IP traffic received via the {} device. "
               "You can apply all configurations by running the following "
               "command:".format(name))

        _print("blocksat-cli usb config", style="code")

        _print("If you would like to review the changes before applying them, "
               "first run the command in dry-run mode: ")

        _print("blocksat-cli usb config --dry-run", style="code")

        _print(
            "Note this command will define an arbitrary IP address to the "
            "interface. If you would like to set a specific IP address, for "
            "example, to avoid address conflicts, use the option \"--ip\". ")

        _print(
            "Furthermore, note this configuration is not persistent across "
            "reboots. After a reboot, you need to run \"blocksat-cli usb "
            "config\" again.",
            end_prompt=True)

        _print("Launch", style="subheader")

        _print("Finally, start the receiver by running:")

        _print("blocksat-cli usb launch", style="code", end_prompt=True)
    else:
        _print("Configuration and Monitoring", style="subheader")

        _print("You can start your receiver by clicking on "
               "the \"Run Receiver\" button on the \"Receiver\" tab. "
               "After that, the GUI will automatically check if the "
               "software dependencies and drivers are installed on "
               "your host and proceed with the receiver configuration.")

        _print("Once the configuration is complete, the GUI will "
               "automatically launch the receiver and start monitoring it. "
               " The receiver status metrics will be available in "
               "real time on the \"Receiver\" tab.")


def _print_sdr_instructions(gui=False):
    """Print instruction for configuration of an SDR setup
    """
    _print("SDR Setup", style="header")

    _print("Connections", style="subheader")

    _print("The SDR setup is connected as follows:")

    _print("LNB ----> Power Supply ----> RTL-SDR ----> Host", text_wrap=False)

    _print("Connect the RTL-SDR USB dongle to your host PC.", style="item")
    _print(
        "Connect the **non-powered** port of the power supply (labeled as "
        "\"Signal to IRD\") to the RTL-SDR using an SMA cable and an "
        "SMA-to-F adapter.",
        style="item")
    _print(
        "Connect the **powered** port (labeled \"Signal to SWM\") of the "
        "power supply to the LNB using a coaxial cable (an RG6 cable is "
        "recommended).",
        style="item",
        end_linebreak=True)

    _print(
        "IMPORTANT: Do NOT connect the powered port of the power supply "
        "to the SDR interface. Permanent damage may occur to your SDR "
        "and/or your computer.",
        end_prompt=True)

    if not gui:
        _print("Software Requirements", style="subheader")

        _print("The SDR-based setup relies on the applications listed below:")

        _print(
            "leandvb or gr-dvbs2rx: the software-based DVB-S2 receiver "
            "application.",
            style="item")
        _print(
            "rtl_sdr: reads samples taken by the RTL-SDR and feeds them into "
            "leandvb.",
            style="item")
        _print(
            "TSDuck: unpacks the output of leandvb and produces "
            "IP packets to be fed to Bitcoin Satellite.",
            style="item")
        _print(
            "Gqrx: useful for spectrum visualization during antenna pointing.",
            style="item",
            end_linebreak=True)
        _print("To install them, run:")
        _print("blocksat-cli deps install", style="code")

        _print(
            "NOTE: This command supports the two most recent Ubuntu LTS, "
            "Fedora, and CentOS releases. In case you are using another Linux "
            "distribution or version, please refer to the manual compilation "
            "and installation instructions at:")
        _print(defs.user_guide_url + "doc/sdr.html",
               style="url",
               end_prompt=True)

        _print("Configuration", style="subheader")

        _print("Next, you can generate the configurations that are needed for "
               "gqrx by running:")

        _print("blocksat-cli gqrx-conf", style="code", end_prompt=True)

        _print("Running", style="subheader")

        _print(
            "You should now be ready to launch the SDR receiver. You can run "
            "it by executing:")

        _print("blocksat-cli sdr", style="code")
        _print("Or, in GUI mode:")
        _print("blocksat-cli sdr --gui", style="code", end_prompt=True)
    else:
        _print("Configuration and Monitoring", style="subheader")

        _print("You can start your receiver by clicking on "
               "the \"Run Receiver\" button on the \"Receiver\" tab. "
               "After that, the GUI will automatically check if all the "
               "software dependencies are installed on your host "
               "and generate the configuration file needed for gqrx. ")

        _print("Once the configuration is complete, the SDR receiver will be "
               "launched and the receiver metrics will be available in "
               "real time on the \"Receiver\" tab.")


def _print_sat_ip_instructions(gui=False):

    _print("Sat-IP Setup", style="header")

    _print("The Sat-IP setup relies on the Blockstream Satellite Base "
           "Station (available on Blockstream Store), an all-in-one "
           "flat-panel antenna with an integrated receiver and LNB. This "
           "device receives the satellite signal and outputs IP packets to "
           "one or more Sat-IP clients listening to it in the local network.")

    _print(
        "The following steps explain how you can connect to the base "
        "station device to receive the Blockstream Satellite traffic.",
        end_prompt=True)

    _print("Connections", style="subheader")

    _print(
        "Connect the Ethernet cable from your switch or computer's network "
        "adapter directly to the antenna's Sat>IP port.",
        style="item")

    _print(
        "If your switch/adapter does not support Power over Ethernet (PoE), "
        "insert a PoE injector in-line between the switch/adapter and the "
        "antenna's Sat-IP port. Connect the injector's PoE-enabled port to "
        "the Sat-IP antenna and the non-powered (non-PoE) port to the "
        "switch/adapter.",
        style="item",
        end_linebreak=True)

    _print(
        "IMPORTANT: If using a PoE injector, make sure you are connecting "
        "the correct ports. Permanent damage may occur to your switch or "
        "network adapter otherwise.",
        end_prompt=True)

    if not gui:
        _print("Software Requirements", style="subheader")

        _print("Next, install all software pre-requisites on your host. Run:")

        _print("blocksat-cli deps install", style="code")

        _print(
            "NOTE: this command supports the apt, dnf, and yum package "
            "managers.",
            end_prompt=True)

        _print("Running", style="subheader")

        _print("You should now be ready to launch the Sat-IP client. You can "
               "run it by executing:")

        _print("blocksat-cli sat-ip", style="code", end_prompt=True)
    else:
        _print("Configuration and Monitoring", style="subheader")

        _print("You can start your receiver by clicking on "
               "the \"Run Receiver\" button on the \"Receiver\" tab. "
               "After that, the GUI will automatically check if all the "
               "software dependencies are installed on your host and "
               "install them if necessary.")

        _print("Once the installation is complete, the GUI will "
               "automatically launch the Sat-IP client and start monitoring "
               "the receiver frontend. The receiver status metrics will be "
               "available in real time on the \"Receiver\" tab.")


def _print_freq_info(info):
    """Print summary of frequencies of interest"""
    sat = info['sat']
    setup = info['setup']
    lnb = info['lnb']
    lo_freq = info['freqs']['lo']
    l_freq = info['freqs']['l_band']

    util.print_header("Frequencies")

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


def _print_lnb_warnings(info):
    """Print important warnings based on LNB choice"""
    lnb = info['lnb']
    sat = info['sat']
    setup = info['setup']

    if ((lnb['pol'] != "Dual") and (lnb['pol'] != sat['pol'])):
        _print("LNB Information", style="header")
        lnb_pol = "Vertical" if lnb['pol'] == "V" else "Horizontal"
        logging.warning(
            textwrap.fill(
                "Your LNB has {} polarization and the signal from {} has the "
                "opposite polarization.".format(lnb_pol, sat['name'])))

        _print("", end_prompt=True)

    if ((lnb['pol'] == "Dual") and (setup['type'] == defs.sdr_setup_type)):
        _print("LNB Information", style="header")
        logging.warning(
            textwrap.fill(
                "Your LNB has dual polarization. Check the voltage of your "
                "power supply in order to discover the polarization on which "
                "your LNB will operate."))
        _print("", end_prompt=True)


def print_next_steps(gui=False):
    _print("Next Steps", style="header")
    _print("At this point, if your dish is already correctly pointed, you "
           "should be able to start receiving data on Bitcoin Satellite. ")

    if gui:
        _print(
            "You can generate a bitcoin.conf configuration file for Bitcoin "
            "Satellite by going into the Settings tab, then clicking on the "
            "'Bitcoin' option and selecting 'Create configuration file' from "
            "the dropdown menu.")
    else:
        _print(
            "You can generate a bitcoin.conf configuration file for Bitcoin "
            "Satellite using:")
        _print("blocksat-cli btc", style="code")

    if gui:
        _print("Next, if you are running a supported Linux distribution "
               "(Ubuntu, Debian, Fedora, CentOS, or Raspberry Pi OS), you can "
               "install Bitcoin Satellite by selecting 'Install Bitcoin "
               "Satellite' from the 'Bitcoin' dropdown menu on the Setting "
               "tab.")
    else:
        _print("Next, if you are running a supported Linux distribution "
               "(Ubuntu, Debian, Fedora, CentOS, or Raspberry Pi OS), you can "
               "install Bitcoin Satellite by running:")

        _print("blocksat-cli deps install --btc", style="code")

    _print("Note that Bitcoin Satellite is a fork of Bitcoin Core, and, "
           "as such, it installs applications with the same name (bitcoind, "
           "bitcoin-cli, bitcoin-qt, and bitcoin-tx). Hence, the "
           "Bitcoin Satellite installation will fail if you already have "
           "Bitcoin Core installed.")

    _print("For further information, refer to:")

    _print(defs.user_guide_url + "doc/bitcoin.html", style="url")

    _print("If your antenna is not pointed yet, please follow the antenna "
           "alignment guide at:")

    _print(defs.user_guide_url + "doc/antenna-pointing.html", style="url")


def print_rx_instructions(info, gui=False):
    if (info['setup']['type'] == defs.standalone_setup_type):
        _print_s400_instructions(gui)
    elif (info['setup']['type'] == defs.sdr_setup_type):
        _print_sdr_instructions(gui)
    elif (info['setup']['type'] == defs.linux_usb_setup_type):
        _print_usb_rx_instructions(info, gui)
    elif (info['setup']['type'] == defs.sat_ip_setup_type):
        _print_sat_ip_instructions(gui)


def subparser(subparsers):  # pragma: no cover
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
    _print_lnb_warnings(info)
    print_rx_instructions(info)
    print_next_steps()
