"""User setup configuration"""
import json
import logging
import os
import sys
import textwrap
from argparse import ArgumentDefaultsHelpFormatter, Namespace
from decimal import Decimal, getcontext
from ipaddress import IPv4Address
from pprint import pprint, pformat

from . import util, defs, gqrx

logger = logging.getLogger(__name__)


def _cfg_satellite():
    """Configure satellite covering the user"""
    os.system('clear')
    util.print_header("Satellite")

    help_msg = "Not sure? Check the coverage map at:\n" \
               "https://blockstream.com/satellite/#satellite_network-coverage"

    question = "Which satellite below covers your location?"
    sat = util.ask_multiple_choice(defs.satellites, question, "Satellite",
                                   lambda sat: get_satellite_name(sat),
                                   help_msg)
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


def _ask_antenna(sat):
    """Configure antenna"""
    os.system('clear')
    util.print_header("Antenna")

    question = "What kind of antenna are you using?"

    # The flat-panel antenna models do not work in the C band
    antenna_options = [
        x for x in defs.antennas
        if not (sat["band"] == "C" and x["type"] in ["flat", "sat-ip"])
    ]
    antenna = util.ask_multiple_choice(antenna_options,
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


def _ask_demod(sat):
    """Ask the receiver/demodulator model"""
    question = "Select your DVB-S2 receiver:"

    rx_options = [
        rx for rx in defs.demods
        # If band C, remove Blockstrem Base Station from option list
        if not (sat["band"] == "C" and rx["vendor"] == "Selfsat")
    ]

    setup = util.ask_multiple_choice(
        rx_options, question, "Receiver",
        lambda x: '{} receiver'.format(_get_rx_marketing_name(x)))

    return setup


def _cfg_rx_setup(sat):
    """Configure Rx setup - which receiver user is using """
    os.system('clear')
    util.print_header("Receiver")

    # The setup includes the demodulator info, the antenna, and extra fields
    setup = _ask_demod(sat)

    # Network interface connected to the standalone receiver
    if (setup['type'] == defs.standalone_setup_type):
        devices = util.get_network_interfaces()

        question = "Which network interface is connected to the receiver?"
        if (devices is not None):
            netdev = util.ask_multiple_choice(devices, question, "Interface",
                                              lambda x: '{}'.format(x))
        else:
            netdev = input(question + " ")

        setup['netdev'] = netdev.strip()

        custom_ip = util.ask_yes_or_no(
            "Have you manually assigned a custom IP address to the receiver?",
            default="n")
        if (custom_ip):
            ipv4_addr = util.typed_input("Which IPv4 address?",
                                         in_type=IPv4Address)
            setup["rx_ip"] = str(ipv4_addr)
        else:
            setup["rx_ip"] = defs.default_standalone_ip_addr

    # Define the Sat-IP antenna directly without asking the user
    if (setup['type'] == defs.sat_ip_setup_type):
        # NOTE: this works as long as there is a single Sat-IP antenna in the
        # list. In the future, if other Sat-IP antennas are included, change to
        # a multiple-choice prompt.
        for antenna in defs.antennas:
            if antenna['type'] == 'sat-ip':
                setup['antenna'] = antenna
                break
        if 'antenna' not in setup:
            raise RuntimeError("Failed to find antenna of {} receiver".format(
                defs.sat_ip_setup_type))

        custom_ip = util.ask_yes_or_no(
            "Does the {} have a static IP address?".format(
                _get_rx_marketing_name(setup)),
            default="n")
        if (custom_ip):
            ipv4_addr = util.typed_input("Which IPv4 address?",
                                         in_type=IPv4Address)
            setup["ip_addr"] = str(ipv4_addr)
        return setup

    # Antenna
    setup['antenna'] = _ask_antenna(sat)

    return setup


def _ask_lnb_freq_range(sat):
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

        is_valid, msg = _validate_lnb_freq_range(in_range, sat)
        if not is_valid:
            print(msg)
            in_range = []
            continue

        break

    return in_range


def _validate_lnb_freq_range(freq_range, sat):
    """Validate the LNB frequency range

    Args:
        freq_range (list): Two extreme LNB frequencies.
        sat (dict): Dictionary with the Satellite information.

    Returns:
        is_valid (bool): Whether the two frequencies are valid.
        msg (str): Detailed error message if the frequencies are invalid.

    """
    assert (isinstance(freq_range, list))

    is_valid = False
    msg = ""

    if (freq_range[1] < freq_range[0]):
        msg = ("Please, provide the lowest frequency first, followed by "
               "the highest.")
    elif (freq_range[0] < 3000 or freq_range[1] < 3000):
        msg = "Please, provide the frequencies in MHz."
    elif not _sat_freq_in_lnb_range(sat, {'in_range': freq_range}):
        msg = (f"Please, choose a frequency range covering the {sat['name']} "
               f"downlink frequency of {sat['dl_freq']} MHz")
    else:
        is_valid = True

    return is_valid, msg


def _validate_lnb_lo_freq(lo_freq, single_lo=False):
    is_valid = False
    msg = ""

    if single_lo:
        assert (isinstance(lo_freq, float))
        if (lo_freq < 3000):
            msg = "Please, provide the frequencies in MHz."
        else:
            is_valid = True

    else:
        assert (isinstance(lo_freq, list))
        if (lo_freq[1] < lo_freq[0]):
            msg = ("Please, provide the low LO frequency first, followed by "
                   "the high LO frequency.")
        elif (lo_freq[0] < 3000 or lo_freq[1] < 3000):
            msg = "Please, provide the frequencies in MHz."
        else:
            is_valid = True

    return is_valid, msg


def _ask_lnb_lo(single_lo=True):
    """Prompt the user for the LNB's LO frequencies"""
    if (single_lo):
        while (True):
            lo_freq = util.typed_input("LNB LO frequency in MHz",
                                       in_type=float)

            is_valid, msg = _validate_lnb_lo_freq(lo_freq, single_lo)
            if (not is_valid):
                print(msg)
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

        is_valid, msg = _validate_lnb_lo_freq(lo_freq, single_lo)
        if (not is_valid):
            lo_freq = []
            print(msg)
            continue

        break

    return lo_freq


def _ask_lnb_polarization():
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
    return util.ask_multiple_choice(options, question, "Polarization",
                                    lambda x: '{}'.format(x['text']))


def _cfg_custom_lnb(sat):
    """Configure custom LNB based on user-entered specs

    Args:
        sat : user's satellite info

    """

    print("\nPlease, inform the specifications of your LNB:")

    bands = ["C", "Ku"]
    question = "Frequency band:"
    custom_lnb_band = util.ask_multiple_choice(bands, question, "Band",
                                               lambda x: '{}'.format(x))

    if (sat['band'].lower() != custom_lnb_band.lower()):
        logging.error("You must use a %s band LNB to receive from %s" %
                      (sat['band'], sat['name']))
        sys.exit(1)

    if (custom_lnb_band == "Ku"):
        custom_lnb_universal = util.ask_yes_or_no(
            "Is it a Universal Ku band LNB?")

        if (custom_lnb_universal):
            # Input frequency range
            print()
            util.fill_print("""A Universal Ku band LNB typically covers an
            input frequency range from 10.7 to 12.75 GHz.""")
            if (util.ask_yes_or_no("Does your LNB cover this input range "
                                   "from 10.7 to 12.75 GHz?")):
                custom_lnb_in_range = [10700.0, 12750.0]
            else:
                custom_lnb_in_range = _ask_lnb_freq_range(sat)

            # LO
            print()
            util.fill_print("""A Universal Ku band LNB has two LO (local
            oscillator) frequencies. Typically the two frequencies are 9750
            MHz and 10600 MHz.""")
            if (util.ask_yes_or_no("Does your LNB have LO frequencies 9750 "
                                   "MHz and 10600 MHz?")):
                custom_lnb_lo_freq = [9750.0, 10600.0]
            else:
                custom_lnb_lo_freq = _ask_lnb_lo(single_lo=False)
        else:
            # Non-universal Ku-band LNB
            custom_lnb_in_range = _ask_lnb_freq_range(sat)
            custom_lnb_lo_freq = _ask_lnb_lo()
    else:
        # C-band LNB
        custom_lnb_universal = False
        custom_lnb_in_range = _ask_lnb_freq_range(sat)
        custom_lnb_lo_freq = _ask_lnb_lo()

    # Polarization
    pol = _ask_lnb_polarization()

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
    lnb = util.ask_multiple_choice(
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
    psu = util.ask_multiple_choice(defs.psus,
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
    util.print_header("LNB")

    lnb = _ask_lnb(sat)

    if (not _sat_freq_in_lnb_range(sat, lnb)):
        logging.warning("Your LNB's input frequency range does not cover the "
                        "frequency of {} ({} MHz)".format(
                            sat['name'], sat['dl_freq']))
        if not util.ask_yes_or_no("Continue anyway?", default="n"):
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
        util.print_header("Power Supply")

    if (lnb['pol'].lower() == "dual" and setup['type'] != defs.sdr_setup_type):
        prev_sdr_setup = util.ask_yes_or_no(
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


def _calc_if_freq(dl_freq, lo_freq, band):
    """Calculate the IF frequency for downlink reception with a given LO

    Args:
        dl_freq : Downlink frequency.
        lo_freq : LNB LO frequency.
        band    : Band of the satellite.

    Returns:
        float: IF frequency.

    """
    if (band.lower() == "c"):
        if_freq = float(Decimal(lo_freq) - Decimal(dl_freq))
    elif (band.lower() == "ku"):
        if_freq = float(Decimal(dl_freq) - Decimal(lo_freq))
    else:
        logging.error("Invalid satellite band: {}".format(band))
        sys.exit(1)

    return round(if_freq, 2)


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
            assert (isinstance(lnb['lo_freq'], list)), \
                "A Universal LNB must have a list with two LO frequencies"
            assert (len(lnb['lo_freq']) == 2), \
                "A Universal LNB must have two LO frequencies"
            if (sat['dl_freq'] > defs.ku_band_thresh):
                lo_freq = lnb['lo_freq'][1]
            else:
                lo_freq = lnb['lo_freq'][0]
        else:
            lo_freq = lnb['lo_freq']
    elif (sat['band'].lower() == "c"):
        lo_freq = lnb['lo_freq']
    else:
        raise ValueError("Unknown satellite band")

    if_freq = _calc_if_freq(sat['dl_freq'], lo_freq, sat['band'])

    if (if_freq < setup['tun_range'][0] or if_freq > setup['tun_range'][1]):
        logging.error("Your LNB yields an L-band frequency that is out of "
                      "the tuning range of the {} receiver.".format(
                          _get_rx_marketing_name(setup)))
        sys.exit(1)

    return {'dl': sat['dl_freq'], 'lo': lo_freq, 'l_band': if_freq}


def _gen_chan_conf(info):
    """Generate the content for the channel configuration file

    Returns:
        dict: Dictionary with the keys and values to be written in the channel
        configuration file.
    """
    chan_conf = {}
    chan_conf['DELIVERY_SYSTEM'] = 'DVBS2'
    chan_conf['FREQUENCY'] = str(int(info['sat']['dl_freq'] * 1000))
    if (info['lnb']['pol'].lower() == "dual" and 'v1_pointed' in info['lnb']
            and info['lnb']['v1_pointed']):
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
            chan_conf['POLARIZATION'] = 'HORIZONTAL'
        else:
            chan_conf['POLARIZATION'] = 'VERTICAL'
    else:
        if (info['sat']['pol'] == 'V'):
            chan_conf['POLARIZATION'] = 'VERTICAL'
        else:
            chan_conf['POLARIZATION'] = 'HORIZONTAL'
    chan_conf['SYMBOL_RATE'] = str(defs.sym_rate[info['sat']['alias']])
    chan_conf['INVERSION'] = 'AUTO'
    chan_conf['MODULATION'] = 'QPSK'
    chan_conf['VIDEO_PID'] = "+".join([str(x) for x in defs.pids])
    return chan_conf


def write_chan_conf(info, chan_file, yes=False):
    """Generate the channels.conf file"""

    util.print_header("Channel Configuration")

    print(
        textwrap.fill("This step will generate the channel configuration "
                      "file that is required when launching the USB "
                      "receiver in Linux.") + "\n")

    if (os.path.isfile(chan_file)):
        print("Found previous %s file:" % (chan_file))

        if (yes or util.ask_yes_or_no("Remove and regenerate file?")):
            os.remove(chan_file)
        else:
            print("Configuration aborted.")
            return

    with open(chan_file, 'w') as f:
        chan_config = _gen_chan_conf(info)
        f.write('[blocksat-ch]\n')
        for k, v in chan_config.items():
            f.write(f'\t{k} = {v}\n')

    print("File \"%s\" saved." % (chan_file))

    with open(chan_file, 'r') as f:
        logging.debug(f.read())


def _parse_chan_conf(chan_file):
    """Read channel.conf file and parse contents into a dictionary"""
    chan_conf = {}
    with open(chan_file, 'r') as f:
        lines = f.read().splitlines()
        for line in lines[1:]:  # skip the channel name
            key, val = line.split('=')
            chan_conf[key.strip()] = val.strip()
    return chan_conf


def get_chan_file_path(cfg_dir, cfg_name):
    """Get the path to the channels configuration file"""
    return os.path.join(cfg_dir, cfg_name + '-channel.conf')


def verify_chan_conf(info):
    """Verify if channel.conf file content is up-to-date

    Args:
        info (dict): User's info.

    Returns:
        bool: True if the file is up-to-date or false otherwise.

    """
    if 'channel' not in info['setup'] or not info['setup']['channel']:
        return False

    chan_file = info['setup']['channel']
    new_chan_cfg = _gen_chan_conf(info)
    old_chan_cfg = _parse_chan_conf(chan_file)

    return new_chan_cfg == old_chan_cfg


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


def _patch_cfg_file(cfg_file, info):
    """Apply changes/updates to the configuration file"""
    updated = False
    if 'sat' in info:
        new_dl_freq = None
        if info['sat']['alias'] == "T11N AFR" and \
                info['sat']['dl_freq'] == 11480.7:
            new_dl_freq = 11452.1
        if info['sat']['alias'] == "T11N EU" and \
                info['sat']['dl_freq'] == 11484.3:
            new_dl_freq = 11505.4
        if info['sat']['alias'] == "G18" and \
                info['sat']['dl_freq'] == 12016.4:
            new_dl_freq = 11913.4
        if info['sat']['alias'] == "T18V C" and \
                info['sat']['dl_freq'] == 4053.83:
            new_dl_freq = 4057.4

        if new_dl_freq is not None:
            logger.info(
                "Updating the {} DL frequency from {} MHz to {} MHz".format(
                    info['sat']['alias'], info['sat']['dl_freq'], new_dl_freq))
            info['sat']['dl_freq'] = new_dl_freq
            info['freqs']['dl'] = new_dl_freq
            info['freqs']['l_band'] = _calc_if_freq(new_dl_freq,
                                                    info['freqs']['lo'],
                                                    info['sat']['band'])
            updated = True

    if updated:
        _write_cfg_file(cfg_file, info)


def _rst_cfg_file(cfg_file):
    """Reset a previous configuration file in case it exists"""
    info = _read_cfg_file(cfg_file)

    if (info is not None):
        print("Found previous configuration:")
        pprint(info, width=80, compact=False)
        if (util.ask_yes_or_no("Reset?")):
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

    if (info is not None):
        _patch_cfg_file(cfg_file, info)

    while (info is None):
        print("Missing {} configuration file".format(cfg_file))
        if (util.ask_yes_or_no("Run configuration helper now?")):
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


def get_rx_label(user_info):
    """Return the label of the target receiver"""
    target_map = {
        "sdr": defs.sdr_setup_type,
        "usb": defs.linux_usb_setup_type,
        "standalone": defs.standalone_setup_type,
        "sat-ip": defs.sat_ip_setup_type
    }
    target = user_info['setup']['type']

    return next(key for key, val in target_map.items() if val == target)


def get_satellite_name(sat):
    """Return string with satellite name"""
    return f"{sat['name']} ({sat['alias']})"


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


def subparser(subparsers):  # pragma: no cover
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
    p2.add_argument('--json',
                    default=False,
                    action='store_true',
                    help='Print results in JSON format')
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
        user_setup = _cfg_rx_setup(user_sat)
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
        write_chan_conf(user_info, chan_file)
        user_info['setup']['channel'] = chan_file

    # Gqrx configuration
    if (user_setup['type'] == defs.sdr_setup_type):
        os.system('clear')
        gqrx._configure(user_info)

    # Create the JSON configuration file
    _write_cfg_file(cfg_file, user_info)

    os.system('clear')
    util.print_header("JSON configuration file")
    print("Saved configurations on %s" % (cfg_file))

    util.print_header("Next Steps")

    print(textwrap.fill("Please check setup instructions by running:"))
    print("""
    blocksat-cli instructions
    """)


def get_readable_cfg(info):
    assert (info is not None), "Empty receiver configuration"

    setup = info['setup']
    sat = info['sat']
    freqs = info['freqs']

    cfg = {
        'Setup': {
            'Receiver': _get_rx_marketing_name(setup),
            'Tuning range':
            f"From {setup['tun_range'][0]} to {setup['tun_range'][1]} MHz ",
            'LNB': get_lnb_model(info),
            'Antenna': get_antenna_model(info),
        },
        'Satellite': {
            'Satellite name':
            get_satellite_name(sat),
            'Signal band':
            sat['band'],
            'Signal polarization':
            "Horizontal" if sat['pol'] == "H" else "Vertical"
        },
        'Frequencies': {
            'Downlink frequency': f"{freqs['dl']} MHz",
            'LNB LO frequency': f"{freqs['lo']} MHz",
            'Receiver L-band frequency': f"{freqs['l_band']} MHz"
        }
    }

    if (setup['type'] == defs.standalone_setup_type and 'rx_ip' in setup):
        cfg['Setup']['IP Address'] = setup['rx_ip']

    if (setup['type'] == defs.sat_ip_setup_type and 'ip_addr' in setup):
        cfg['Setup']['IP Address'] = setup['ip_addr']

    return cfg


def show(args):
    """Print the local configuration"""
    info = read_cfg_file(args.cfg, args.cfg_dir)
    if (info is None):
        return

    pr_cfgs = get_readable_cfg(info)

    if args.json:
        print(json.dumps(pr_cfgs, indent=4))
        return

    box_size = 67
    box_line = "-" * box_size

    for category in pr_cfgs:
        print(f"\n{category}")
        print(box_line)
        for key, pr_cfg in pr_cfgs[category].items():
            print("| {:30s} | {:30s} |".format(key, pr_cfg))
        print(box_line)


def channel(args):
    """Configure the channels.conf file directly"""
    user_info = read_cfg_file(args.cfg, args.cfg_dir)
    if (user_info is None):
        return

    # Channel configuration file
    if (user_info['setup']['type'] != defs.linux_usb_setup_type):
        raise TypeError("Invalid command for {} receivers".format(
            user_info['setup']['type']))

    chan_file = get_chan_file_path(args.cfg_dir, args.cfg)
    write_chan_conf(user_info, chan_file)

    # Overwrite the channels.conf path in case it is changing from a previous
    # version of the CLI when the conf file name was not bound to the cfg name
    user_info['setup']['channel'] = chan_file
    write_cfg_file(args.cfg, args.cfg_dir, user_info)
