"""User setup configuration"""
import json
import logging
import os
import sys
import textwrap
from argparse import ArgumentDefaultsHelpFormatter, Namespace
from decimal import Decimal, getcontext
from pprint import pprint, pformat

from . import util, defs

logger = logging.getLogger(__name__)


def _cfg_satellite():
    """Configure satellite covering the user"""
    os.system('clear')
    util._print_header("Satellite")

    help_msg = "Not sure? Check the coverage map at:\n" \
               "https://blockstream.com/satellite/#satellite_network-coverage"

    question = "Which satellite below covers your location?"
    sat = util._ask_multiple_choice(
        defs.satellites, question, "Satellite",
        lambda sat: '{} ({})'.format(sat['name'], sat['alias']), help_msg)
    return sat


def _get_rx_marketing_name(rx):
    """Get the marketed receiver name (including satellite kit name)"""
    model = (rx['vendor'] + " " + rx['model']).strip()
    if model == "Novra S400":
        model += " (pro kit)"  # append
    elif model == "TBS 5927":
        model += " (basic kit)"  # append
    elif model == "Selfsat IP22":
        model = "Blockstream Base Station"  # overwrite
    elif model == "RTL-SDR":
        model += " software-defined"
    return model


def _get_antenna_name(x):
    """Get antenna name for the configuration menu"""
    if x['type'] == 'dish':
        s = 'Satellite Dish ({})'.format(x['label'])
    elif x['type'] == 'sat-ip':
        s = 'Blockstream Base Station (Legacy Output)'
    else:
        s = 'Blockstream Flat-Panel Antenna'
    return s


def _ask_antenna():
    """Configure antenna"""
    os.system('clear')
    util._print_header("Antenna")

    question = "What kind of antenna are you using?"
    antenna = util._ask_multiple_choice(defs.antennas,
                                        question,
                                        "Antenna",
                                        _get_antenna_name,
                                        none_option=True,
                                        none_str="Other")

    if (antenna is None):
        size = util.typed_input("Enter size in cm",
                                "Please enter an integer number in cm",
                                in_type=int)
        antenna = {'label': "custom", 'type': 'dish', 'size': size}

    return antenna


def _cfg_rx_setup():
    """Configure Rx setup - which receiver user is using """
    os.system('clear')
    util._print_header("Receiver")

    # Receiver
    question = "Select your DVB-S2 receiver:"
    setup = util._ask_multiple_choice(
        defs.demods, question, "Receiver",
        lambda x: '{} receiver'.format(_get_rx_marketing_name(x)))

    # Network interface connected to the standalone receiver
    if (setup['type'] == defs.standalone_setup_type):
        try:
            devices = os.listdir('/sys/class/net/')
        except FileNotFoundError:
            devices = None
            pass

        question = "Which network interface is connected to the receiver?"
        if (devices is not None):
            netdev = util._ask_multiple_choice(devices, question, "Interface",
                                               lambda x: '{}'.format(x))
        else:
            netdev = input(question + " ")

        setup['netdev'] = netdev.strip()

    # Define the Sat-IP antenna directly without asking the user
    if (setup['type'] == defs.sat_ip_setup_type):
        # NOTE: this works as long as there is a single Sat-IP antenna in the
        # list. In the future, if other Sat-IP antennas are included, change to
        # a multiple-choice prompt.
        for antenna in defs.antennas:
            if antenna['type'] == 'sat-ip':
                setup['antenna'] = antenna
                return setup
        # We should have returned in the preceding line.
        raise RuntimeError("Failed to find antenna of {} receiver".format(
            defs.sat_ip_setup_type))

    # Antenna
    setup['antenna'] = _ask_antenna()

    return setup


def _ask_lnb_freq_range():
    """Prompt the user for the LNB's input frequency range"""
    in_range = []
    while (True):
        while (len(in_range) != 2):
            try:
                resp = input(
                    "Inform the two extreme frequencies (in MHz) of "
                    "your LNB's frequency range, separated by comma: ")
                in_range = [float(x) for x in resp.split(",")]
            except ValueError:
                continue

        if (in_range[1] < in_range[0]):
            in_range = []
            print("Please, provide the lowest frequency first, followed by "
                  "the highest.")
            continue

        if (in_range[0] < 3000 or in_range[1] < 3000):
            in_range = []
            print("Please, provide the frequencies in MHz.")
            continue

        break

    return in_range


def _ask_lnb_lo(single_lo=True):
    """Prompt the user for the LNB's LO frequencies"""
    if (single_lo):
        while (True):
            lo_freq = util.typed_input("LNB LO frequency in MHz",
                                       in_type=float)

            if (lo_freq < 3000):
                print("Please, provide the frequencies in MHz.")
                continue

            break
        return lo_freq

    lo_freq = []
    while (True):
        while (len(lo_freq) != 2):
            try:
                resp = input("Inform the two LO frequencies in MHz, separated "
                             "by comma: ")
                lo_freq = [float(x) for x in resp.split(",")]
            except ValueError:
                continue

        if (lo_freq[1] < lo_freq[0]):
            lo_freq = []
            print("Please, provide the low LO frequency first, followed by "
                  "the high LO frequency.")
            continue

        if (lo_freq[0] < 3000 or lo_freq[1] < 3000):
            lo_freq = []
            print("Please, provide the frequencies in MHz.")
            continue

        break

    return lo_freq


def _cfg_custom_lnb(sat):
    """Configure custom LNB based on user-entered specs

    Args:
        sat : user's satellite info

    """

    print("\nPlease, inform the specifications of your LNB:")

    bands = ["C", "Ku"]
    question = "Frequency band:"
    custom_lnb_band = util._ask_multiple_choice(bands, question, "Band",
                                                lambda x: '{}'.format(x))

    if (sat['band'].lower() != custom_lnb_band.lower()):
        logging.error("You must use a %s band LNB to receive from %s" %
                      (sat['band'], sat['name']))
        sys.exit(1)

    if (custom_lnb_band == "Ku"):
        custom_lnb_universal = util._ask_yes_or_no(
            "Is it a Universal Ku band LNB?")

        if (custom_lnb_universal):
            # Input frequency range
            print()
            util.fill_print("""A Universal Ku band LNB typically covers an
            input frequency range from 10.7 to 12.75 GHz.""")
            if (util._ask_yes_or_no("Does your LNB cover this input range "
                                    "from 10.7 to 12.75 GHz?")):
                custom_lnb_in_range = [10700.0, 12750.0]
            else:
                custom_lnb_in_range = _ask_lnb_freq_range()

            # LO
            print()
            util.fill_print("""A Universal Ku band LNB has two LO (local
            oscillator) frequencies. Typically the two frequencies are 9750
            MHz and 10600 MHz.""")
            if (util._ask_yes_or_no("Does your LNB have LO frequencies 9750 "
                                    "MHz and 10600 MHz?")):
                custom_lnb_lo_freq = [9750.0, 10600.0]
            else:
                custom_lnb_lo_freq = _ask_lnb_lo(single_lo=False)
        else:
            # Non-universal Ku-band LNB
            custom_lnb_in_range = _ask_lnb_freq_range()
            custom_lnb_lo_freq = _ask_lnb_lo()
    else:
        # C-band LNB
        custom_lnb_universal = False
        custom_lnb_in_range = _ask_lnb_freq_range()
        custom_lnb_lo_freq = _ask_lnb_lo()

    # Polarization
    question = "Choose the LNB polarization:"
    options = [{
        'id': "Dual",
        'text': "Dual polarization (horizontal and vertical)"
    }, {
        'id': "H",
        'text': "Horizontal"
    }, {
        'id': "V",
        'text': "Vertical"
    }]
    pol = util._ask_multiple_choice(options, question, "Polarization",
                                    lambda x: '{}'.format(x['text']))

    return {
        'vendor': "",
        'model': "",
        'in_range': custom_lnb_in_range,
        'lo_freq': custom_lnb_lo_freq,
        'universal': custom_lnb_universal,
        'band': custom_lnb_band,
        'pol': pol['id']
    }


def _sat_freq_in_lnb_range(sat, lnb):
    """Check if the satellite signal is within the LNB input range"""
    return sat['dl_freq'] > lnb['in_range'][0] and \
        sat['dl_freq'] < lnb['in_range'][1]


def _ask_lnb(sat):
    """Ask the user's LNB"""
    question = "Please, inform your LNB model:"
    lnb_options = [
        lnb for lnb in defs.lnbs
        if _sat_freq_in_lnb_range(sat, lnb) and lnb['vendor'] != 'Selfsat'
    ]
    lnb = util._ask_multiple_choice(
        lnb_options,
        question,
        "LNB",
        lambda x: "{} {} {}".format(
            x['vendor'], x['model'], "(Universal Ku band LNBF)"
            if x['universal'] else ""),
        none_option=True,
        none_str="Other")

    if (lnb is None):
        lnb = _cfg_custom_lnb(sat)

    return lnb


def _ask_psu_voltage(question):
    """Prompt for the power inserter model or voltage"""
    psu = util._ask_multiple_choice(defs.psus,
                                    question,
                                    "Power inserter",
                                    lambda x: "{}".format(x['model']),
                                    none_option=True,
                                    none_str="No - another model")
    if (psu is None):
        voltage = util.typed_input("What is the voltage supplied to the "
                                   "LNB by your power inserter?")
    else:
        voltage = psu["voltage"]

    return voltage


def _cfg_lnb(sat, setup):
    """Configure LNB - either from preset or from custom specs

    Configure also the LNB power supply, if applicable.

    Args:
        sat   : user's satellite info
        setup : user's setup info

    """

    # For flat-panel and Sat-IP antennas, the LNB is the integrated one
    if (setup['antenna']['type'] in ['flat', 'sat-ip']):
        for lnb in defs.lnbs:
            if lnb['vendor'] == 'Selfsat':
                lnb["v1_pointed"] = False
                return lnb

    os.system('clear')
    util._print_header("LNB")

    lnb = _ask_lnb(sat)

    if (not _sat_freq_in_lnb_range(sat, lnb)):
        logging.warning("Your LNB's input frequency range does not cover the "
                        "frequency of {} ({} MHz)".format(
                            sat['name'], sat['dl_freq']))
        if not util._ask_yes_or_no("Continue anyway?", default="n"):
            logging.error("Invalid LNB")
            sys.exit(1)

    if (sat['band'].lower() != lnb['band'].lower()):
        logging.error("The LNB you chose cannot operate " +
                      "in %s band (band of satellite %s)" %
                      (sat['band'], sat['alias']))
        sys.exit(1)

    # When configuring a non-SDR receiver with a dual polarization LNB, we must
    # know whether the LNB was pointed before on an SDR setup in order to
    # define the polarization on channels.conf. When configuring an SDR
    # receiver, collect the power inserter voltage too for future use.
    if ((lnb['pol'].lower() == "dual" and setup['type'] != defs.sdr_setup_type)
            or setup['type'] == defs.sdr_setup_type):
        os.system('clear')
        util._print_header("Power Supply")

    if (lnb['pol'].lower() == "dual" and setup['type'] != defs.sdr_setup_type):
        prev_sdr_setup = util._ask_yes_or_no(
            "Are you reusing an LNB that is already pointed and that was used "
            "before by an SDR receiver?",
            default='n',
            help_msg="NOTE: this information is helpful to determine the "
            "polarization required for the LNB.")

        lnb["v1_pointed"] = prev_sdr_setup

        if (prev_sdr_setup):
            print()
            question = (
                "In the pre-existing SDR setup, did you use one of the "
                "LNB power inserters below?")
            lnb["v1_psu_voltage"] = _ask_psu_voltage(question)
    elif (setup['type'] == defs.sdr_setup_type):
        question = ("Are you using one of the LNB power inserters below?")
        lnb["psu_voltage"] = _ask_psu_voltage(question)

    return lnb


def _cfg_frequencies(sat, lnb, setup):
    """Print summary of frequencies

    Inform the downlink RF frequency, the LNB LO frequency and the L-band
    frequency to be configured in the receiver.

    Args:
        sat   : user's satellite info
        lnb   : user's LNB info

    """
    getcontext().prec = 8

    if (sat['band'].lower() == "ku"):
        if (lnb['universal']):
            assert(isinstance(lnb['lo_freq'], list)), \
                "A Universal LNB must have a list with two LO frequencies"
            assert(len(lnb['lo_freq']) == 2), \
                "A Universal LNB must have two LO frequencies"

            if (sat['dl_freq'] > defs.ku_band_thresh):
                lo_freq = lnb['lo_freq'][1]
            else:
                lo_freq = lnb['lo_freq'][0]
        else:
            lo_freq = lnb['lo_freq']

        if_freq = float(Decimal(sat['dl_freq']) - Decimal(lo_freq))

    elif (sat['band'].lower() == "c"):
        lo_freq = lnb['lo_freq']
        if_freq = float(Decimal(lo_freq) - Decimal(sat['dl_freq']))
    else:
        raise ValueError("Unknown satellite band")

    if (if_freq < setup['tun_range'][0] or if_freq > setup['tun_range'][1]):
        logging.error("Your LNB yields an L-band frequency that is out of "
                      "the tuning range of the {} receiver.".format(
                          _get_rx_marketing_name(setup)))
        sys.exit(1)

    return {'dl': sat['dl_freq'], 'lo': lo_freq, 'l_band': if_freq}


def _cfg_chan_conf(info, chan_file):
    """Generate the channels.conf file"""

    util._print_header("Channel Configuration")

    print(
        textwrap.fill("This step will generate the channel configuration "
                      "file that is required when launching the USB "
                      "receiver in Linux.") + "\n")

    if (os.path.isfile(chan_file)):
        print("Found previous %s file:" % (chan_file))

        if (not util._ask_yes_or_no("Remove and regenerate file?")):
            print("Configuration aborted.")
            return
        else:
            os.remove(chan_file)

    with open(chan_file, 'w') as f:
        f.write('[blocksat-ch]\n')
        f.write('\tDELIVERY_SYSTEM = DVBS2\n')
        f.write('\tFREQUENCY = %u\n' % (int(info['sat']['dl_freq'] * 1000)))
        if (info['lnb']['pol'].lower() == "dual"
                and 'v1_pointed' in info['lnb'] and info['lnb']['v1_pointed']):
            # If a dual-polarization LNB is already pointed for Blocksat v1,
            # then we must use the polarization that the LNB was pointed to
            # originally, regardless of the satellite signal's polarization. In
            # v1, what mattered the most was the power supply voltage, which
            # determined the polarization of the dual polarization LNBs. If the
            # power supply provides voltage >= 18 (often the case), then the
            # LNB necessarily operates currently with horizontal polarization.
            # Thus, on channels.conf we must use the same polarization in order
            # for the DVB adapter to supply the 18VDC voltage.
            if (info['lnb']["v1_psu_voltage"] >= 16):  # 16VDC threshold
                f.write('\tPOLARIZATION = HORIZONTAL\n')
            else:
                f.write('\tPOLARIZATION = VERTICAL\n')
        else:
            if (info['sat']['pol'] == 'V'):
                f.write('\tPOLARIZATION = VERTICAL\n')
            else:
                f.write('\tPOLARIZATION = HORIZONTAL\n')
        f.write('\tSYMBOL_RATE = {}\n'.format(
            defs.sym_rate[info['sat']['alias']]))
        f.write('\tINVERSION = AUTO\n')
        f.write('\tMODULATION = QPSK\n')
        pids = "+".join([str(x) for x in defs.pids])
        f.write('\tVIDEO_PID = {}\n'.format(pids))

    print("File \"%s\" saved." % (chan_file))

    with open(chan_file, 'r') as f:
        logging.debug(f.read())


def _parse_chan_conf(chan_file):
    """Convert channel.conf file contents to dictionary"""
    chan_conf = {}
    with open(chan_file, 'r') as f:
        lines = f.read().splitlines()
        for line in lines[1:]:
            key, val = line.split('=')
            chan_conf[key.strip()] = val.strip()
    return chan_conf


def _cfg_file_name(cfg_name, directory):
    """Get the name of the configuration JSON file"""
    # Remove paths
    basename = os.path.basename(cfg_name)
    # Remove extension
    noext = os.path.splitext(basename)[0]
    # Add JSON extension
    json_file = noext + ".json"
    return os.path.join(directory, json_file)


def _read_cfg_file(cfg_file):
    """Read configuration file"""

    if (os.path.isfile(cfg_file)):
        with open(cfg_file) as fd:
            info = json.load(fd)
        return info


def _write_cfg_file(cfg_file, user_info):
    """Write configuration file"""
    with open(cfg_file, 'w') as fd:
        json.dump(user_info, fd)


def _rst_cfg_file(cfg_file):
    """Reset a previous configuration file in case it exists"""
    info = _read_cfg_file(cfg_file)

    if (info is not None):
        print("Found previous configuration:")
        pprint(info, width=80, compact=False)
        if (util._ask_yes_or_no("Reset?")):
            os.remove(cfg_file)
        else:
            print("Configuration aborted.")
            return False
    return True


def read_cfg_file(cfg_name, directory):
    """Read configuration file

    If not available, run configuration helper.

    """
    cfg_file = _cfg_file_name(cfg_name, directory)
    info = _read_cfg_file(cfg_file)

    while (info is None):
        print("Missing {} configuration file".format(cfg_file))
        if (util._ask_yes_or_no("Run configuration helper now?")):
            configure(Namespace(cfg_dir=directory, cfg=cfg_name))
        else:
            print("Abort")
            return

        info = _read_cfg_file(cfg_file)

    return info


def write_cfg_file(cfg_name, directory, user_info):
    """Write configuration file"""
    cfg_file = _cfg_file_name(cfg_name, directory)
    _write_cfg_file(cfg_file, user_info)


def get_rx_model(user_info):
    """Return string with the receiver vendor and model

    Note: this function differs from _get_rx_marketing_name(). The latter
    includes the satellite kit name. In contrast, this function returns the raw
    vendeor-model string.

    """
    return (user_info['setup']['vendor'] + " " +
            user_info['setup']['model']).strip()


def get_antenna_model(user_info):
    """Return string with the antenna model"""
    antenna_info = user_info['setup']['antenna']
    antenna_type = antenna_info.get('type')

    if (antenna_type == 'dish' or antenna_info['label'] == 'custom'):
        dish_size = antenna_info['size']
        if (dish_size >= 100):
            antenna = "{:g}m dish".format(dish_size / 100)
        else:
            antenna = "{:g}cm dish".format(dish_size)
    else:
        return antenna_info['label']

    return antenna


def get_lnb_model(user_info):
    """Return string with the LNB model"""
    lnb_info = user_info['lnb']
    if (lnb_info['vendor'] == "" and lnb_info['model'] == ""):
        if (lnb_info['universal']):
            lnb = "Custom Universal LNB"
        else:
            lnb = "Custom {}-band LNB".format(lnb_info['band'])
    else:
        lnb = "{} {}".format(lnb_info['vendor'], lnb_info['model'])
    return lnb


def get_net_if(user_info):
    """Get the network interface used by the given setup"""
    if (user_info is None):
        raise ValueError("Failed to read local configuration")

    setup_type = user_info['setup']['type']

    if (setup_type in [defs.sdr_setup_type, defs.sat_ip_setup_type]):
        interface = "lo"
    elif (setup_type == defs.linux_usb_setup_type):
        if ('adapter' not in user_info['setup']):
            interface = "dvb0_0"
            logger.warning("Could not find the dvbnet interface name. "
                           "Is the {} receiver running?".format(
                               get_rx_model(user_info)))
            logger.warning("Assuming interface name {}.".format(interface))
        else:
            adapter = user_info['setup']['adapter']
            interface = "dvb{}_0".format(adapter)
    elif (setup_type == defs.standalone_setup_type):
        interface = user_info['setup']['netdev']
    else:
        raise ValueError("Unknown setup type")
    return interface


def subparser(subparsers):
    """Argument parser of config command"""
    p = subparsers.add_parser('config',
                              aliases=['cfg'],
                              description="Configure Blocksat Rx setup",
                              help='Define receiver and Bitcoin Satellite \
                              configurations',
                              formatter_class=ArgumentDefaultsHelpFormatter)
    p.set_defaults(func=configure)

    subsubparsers = p.add_subparsers(title='subcommands',
                                     help='Target sub-command')
    p2 = subsubparsers.add_parser(
        'show',
        description="Display the local configuration",
        help='Display the local configuration',
        formatter_class=ArgumentDefaultsHelpFormatter)
    p2.set_defaults(func=show)

    p3 = subsubparsers.add_parser(
        'channel',
        description="Configure the channels file used by the USB receiver",
        help='Configure the channels file used by the USB receiver',
        formatter_class=ArgumentDefaultsHelpFormatter)
    p3.set_defaults(func=channel)
    return p


def configure(args):
    """Configure Blocksat Receiver setup

    """
    cfg_file = _cfg_file_name(args.cfg, args.cfg_dir)
    rst_ok = _rst_cfg_file(cfg_file)
    if (not rst_ok):
        return

    try:
        user_sat = _cfg_satellite()
        user_setup = _cfg_rx_setup()
        user_lnb = _cfg_lnb(user_sat, user_setup)
        user_freqs = _cfg_frequencies(user_sat, user_lnb, user_setup)
    except KeyboardInterrupt:
        print("\nAbort")
        sys.exit(1)

    user_info = {
        'sat': user_sat,
        'setup': user_setup,
        'lnb': user_lnb,
        'freqs': user_freqs
    }

    logging.debug(pformat(user_info))

    if not os.path.exists(args.cfg_dir):
        os.makedirs(args.cfg_dir)

    # Channel configuration file
    if (user_setup['type'] == defs.linux_usb_setup_type):
        chan_file = os.path.join(args.cfg_dir, args.cfg + "-channel.conf")
        _cfg_chan_conf(user_info, chan_file)
        user_info['setup']['channel'] = chan_file

    # Create the JSON configuration file
    _write_cfg_file(cfg_file, user_info)

    os.system('clear')
    util._print_header("JSON configuration file")
    print("Saved configurations on %s" % (cfg_file))

    util._print_header("Next Steps")

    print(textwrap.fill("Please check setup instructions by running:"))
    print("""
    blocksat-cli instructions
    """)


def show(args):
    """Print the local configuration"""
    info = read_cfg_file(args.cfg, args.cfg_dir)
    if (info is None):
        return
    print("| {:30s} | {:25s} |".format("Receiver",
                                       _get_rx_marketing_name(info['setup'])))
    print("| {:30s} | {:25s} |".format("LNB", get_lnb_model(info)))
    print("| {:30s} | {:25s} |".format("Antenna", get_antenna_model(info)))
    pr_cfgs = {
        'freqs': {
            'dl': ("Downlink frequency", "MHz", None),
            'lo': ("LNB LO frequency", "MHz", None),
            'l_band': ("Receiver L-band frequency", "MHz", None)
        },
        'sat': {
            'name': ("Satellite name", "", None),
            'band': ("Signal band", "", None),
            'pol': ("Signal polarization", "", lambda x: "Horizontal"
                    if x == "H" else "vertical"),
        }
    }
    for category in pr_cfgs:
        for key, pr_cfg in pr_cfgs[category].items():
            label = pr_cfg[0]
            unit = pr_cfg[1]
            val = info[category][key]
            # Transform the value if a callback is defined
            if (pr_cfg[2] is not None):
                val = pr_cfg[2](val)
            print("| {:30s} | {:25s} |".format(label, str(val) + " " + unit))


def channel(args):
    """Configure the channels.conf file directly"""
    user_info = read_cfg_file(args.cfg, args.cfg_dir)
    if (user_info is None):
        return

    # Channel configuration file
    if (user_info['setup']['type'] != defs.linux_usb_setup_type):
        raise TypeError("Invalid command for {} receivers".format(
            user_info['setup']['type']))

    chan_file = os.path.join(args.cfg_dir, args.cfg + "-channel.conf")
    _cfg_chan_conf(user_info, chan_file)

    # Overwrite the channels.conf path in case it is changing from a previous
    # version of the CLI when the conf file name was not bound to the cfg name
    user_info['setup']['channel'] = chan_file
    write_cfg_file(args.cfg, args.cfg_dir, user_info)
