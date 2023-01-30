"""Standalone Receiver"""
import logging
import os
import sys
import time
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from ipaddress import ip_address

from pysnmp.hlapi import SnmpEngine, ObjectType, ObjectIdentity, \
     getCmd, setCmd, nextCmd, CommunityData, ContextData, UdpTransportTarget

from . import rp, firewall, defs, config, dependencies, util, monitoring

logger = logging.getLogger(__name__)
runner = util.ProcessRunner(logger)

STANDARD_SNMP_TABLE = {'both': 0, 'dvbs': 1, 'dvbs2': 2}
MODCOD_SNMP_TABLE = {
    'auto': 0,
    'oneQuarterQPSK': 1,
    'oneThirdQPSK': 2,
    'twoFifthsQPSK': 3,
    'oneHalfQPSK': 4,
    'threeFifthsQPSK': 5,
    'twoThirdsQPSK': 6,
    'threeQuartersQPSK': 7,
    'fourFifthsQPSK': 8,
    'fiveSixthsQPSK': 9,
    'eightNinthsQPSK': 10,
    'nineTenthsQPSK': 11,
    'threeFifths8PSK': 12,
    'twoThirds8PSK': 13,
    'threeQuarters8PSK': 14,
    'fiveSixths8PSK': 15,
    'eightNinths8PSK': 16,
    'nineTenths8PSK': 17,
    'twoThirds16APSK': 18,
    'threeQuarters16APSK': 19,
    'fourFifths16APSK': 20,
    'fiveSixths16APSK': 21,
    'eightNinths16APSK': 22,
    'nineTenths16APSK': 23,
    'threeQuarters32APSK': 24,
    'fourFifths32APSK': 25,
    'fiveSixths32APSK': 26,
    'eightNinths32APSK': 27,
    'nineTenths32APSK': 28,
    'oneThirdBPSK': 29,
    'oneQuarterBPSK': 30,
}
SNMP_ROW_STATUS_TABLE = {
    'active': 1,
    'notInService': 2,
    'notReady': 3,
    'createAndGo': 4,
    'createAndWait': 5,
    'destroy': 6
}


def _tuple_to_dotted_str(in_tuple):
    return ".".join([str(x) for x in in_tuple])


class SnmpClient():
    """SNMP Client"""

    def __init__(self, address, port, mib, dry=False):
        """Constructor

        Args:
            address : SNMP agent's IP address
            port    : SNMP agent's port
            mib     : Target SNMP MIB
            dry     : Dry run mode

        """
        assert (ip_address(address))  # parse address
        self.address = address
        self.port = port
        self.mib = mib
        self.dry = dry
        self.engine = SnmpEngine()
        self._dump_mib()

    def _dump_mib(self):
        """Generate the compiled (.py) MIB file"""

        # Check if the compiled MIB (.py file) already exists
        home = util.get_home_dir()
        self.mib_dir = mib_dir = os.path.join(home, ".pysnmp/mibs/")
        if (os.path.exists(os.path.join(mib_dir, self.mib + ".py"))):
            return

        cli_dir = os.path.dirname(os.path.abspath(__file__))
        mib_path = os.path.join(cli_dir, "mib")
        cmd = ["mibdump.py", "--mib-source={}".format(mib_path), self.mib]
        runner.run(cmd)

    def _translate_to_snmpset_val_type(self, key, val):
        """Translate SNMP param to a value-type pair that snmpset understands
        """
        # TODO: Fix s400LOFrequency.0, which is not writable due to being a
        # Counter64 object.
        new_val = val
        if ("s400ModulationStandard" in key):
            if (val in STANDARD_SNMP_TABLE):
                new_val = STANDARD_SNMP_TABLE[val]
        if ("s400Modcod" in key):
            if (val in MODCOD_SNMP_TABLE):
                new_val = MODCOD_SNMP_TABLE[val]
        if ("RowStatus" in key):
            if (val in SNMP_ROW_STATUS_TABLE):
                new_val = SNMP_ROW_STATUS_TABLE[val]
        if (val in ["disable", "enable"]):
            new_val = int(val == "enable")
        if (val in ["disabled", "enabled"]):
            new_val = int(val == "enabled")
        if (val in ["vertical", "horizontal"]):
            new_val = int(val == "horizontal")

        # Value type
        if isinstance(val, str):
            val_type = "s"
        elif (("LBandFrequency" in key)
              or ("SymbolRate" in key and "SymbolRateAuto" not in key)
              or ("s400MpePid1Pid" in key)):
            val_type = "u"
        else:
            val_type = "i"

        return new_val, val_type

    def _get(self, *variables):
        """Get one or more variables via SNMP

        Args:
            Tuple with the variables to fetch via SNMP.

        Returns:
            List of tuples with the fetched keys and values.

        """
        obj_types = []
        for var in variables:
            oid_args = (self.mib, var[0], var[1]) if isinstance(var, tuple) \
                else (self.mib, var, 0)
            obj = ObjectType(
                ObjectIdentity(*oid_args).addMibSource(self.mib_dir))
            obj_types.append(obj)

        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(self.engine, CommunityData('public'),
                   UdpTransportTarget((self.address, self.port)),
                   ContextData(), *obj_types))

        if errorIndication:
            logger.error(errorIndication)
        elif errorStatus:
            logger.error(
                '%s at %s' %
                (errorStatus.prettyPrint(),
                 errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        else:
            res = list()
            for varBind in varBinds:
                logger.debug(' = '.join([x.prettyPrint() for x in varBind]))
                res.append(tuple([x.prettyPrint() for x in varBind]))
            return res

    def _set(self, *key_vals):
        """Set variable via SNMP

        Args:
            variable : variable to set via SNMP.
            value    : value to set on the given variable.

        Returns:
            bool: Whether the request was successful.

        """
        if (self.dry):
            # Convert to the corresponding net-snmp command
            for key, val in key_vals:
                # SNMP OID
                if (isinstance(key, tuple)):
                    key = _tuple_to_dotted_str(key)
                else:
                    key += ".0"  # scalar values must have a .0 suffix
                val, val_type = self._translate_to_snmpset_val_type(key, val)
                print("> snmpset -v 2c -c private {}:{} {}::{} {} {}".format(
                    self.address, self.port, self.mib, key, val_type, val))
            return True

        obj_types = []
        for key, val in key_vals:
            oid_args = (self.mib, key[0], key[1]) if isinstance(key, tuple) \
                else (self.mib, key, 0)
            obj = ObjectType(
                ObjectIdentity(*oid_args).addMibSource(self.mib_dir), val)
            obj_types.append(obj)

        errorIndication, errorStatus, errorIndex, varBinds = next(
            setCmd(self.engine, CommunityData('private'),
                   UdpTransportTarget((self.address, self.port), timeout=10.0),
                   ContextData(), *obj_types))

        if errorIndication:
            logger.error(errorIndication)
        elif errorStatus:
            logger.error(
                '%s at %s' %
                (errorStatus.prettyPrint(),
                 errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        else:
            for varBind in varBinds:
                logger.debug(' = '.join([x.prettyPrint() for x in varBind]))

        return errorIndication is None and errorStatus == 0

    def _walk(self):
        """SNMP Walk

        Returns:
            Dictionary with configurations fetched via SNMP.

        """
        iterator = nextCmd(
            self.engine, CommunityData('public'),
            UdpTransportTarget((self.address, self.port)), ContextData(),
            ObjectType(
                ObjectIdentity(self.mib, '', 0).addMibSource(self.mib_dir)))
        res = {}
        for errorIndication, errorStatus, errorIndex, varBinds in iterator:
            if errorIndication:
                logger.error(errorIndication)
            elif errorStatus:
                logger.error(
                    '%s at %s' %
                    (errorStatus.prettyPrint(),
                     errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
            else:
                for varBind in varBinds:
                    logger.debug(varBind)
                    varBindList = [x.prettyPrint() for x in varBind]
                    key = varBindList[0].replace(self.mib + "::", "")
                    if (len(varBindList) > 2):
                        res[key] = tuple(varBindList[1:])
                    else:
                        res[key] = varBindList[1]
        return res


class S400Client(SnmpClient):
    """Novra S400 SNMP Client"""

    def __init__(self, demod, address, port, dry=False):
        super().__init__(address, port, mib='NOVRA-s400-MIB', dry=dry)
        self.demod = demod

    def check_reachable(self):
        if self.dry:
            return
        cfg = self._get('s400FirmwareVersion')
        if not cfg:
            logger.error("s400 receiver at {} is unreachable".format(
                self.address))
            sys.exit(1)

    def get_stats(self):
        """Get demodulator statistics

        Returns:
            Dictionary with the receiver stats following the format expected by
            the Monitor class (from monitor.py), i.e., each dictionary element
            as a tuple "(value, unit)".

        """
        res = self._get('s400SignalLockStatus' + self.demod,
                        's400SignalStrength' + self.demod,
                        's400CarrierToNoise' + self.demod,
                        's400UncorrectedPackets' + self.demod,
                        's400BER' + self.demod)

        if res is None:
            return

        signal_lock_raw = res[0][1]
        signal_raw = res[1][1]
        c_to_n_raw = res[2][1]
        uncorr_raw = res[3][1]
        ber_raw = res[4][1]

        # Parse
        signal_lock = (signal_lock_raw == 'locked')

        # NOTE: the S400 could have unlocked while the SNMP requests were still
        # being served (the _get request is not an atomic snapshot). As a
        # result, s400SignalLockStatus could be True while some or all of the
        # succeeding metrics (s400SignalStrength to s400BER) could be empty if
        # the S400 unlocked in this interim. In this case, assume the S400 is
        # actually unlocked to prevent parsing of empty metrics.
        raw_metrics = [signal_raw, c_to_n_raw, ber_raw, uncorr_raw]
        if any([x == '' for x in raw_metrics]):
            signal_lock = False

        stats = {'lock': (signal_lock, None)}

        # Metrics that require locking
        if (signal_lock):
            if (signal_raw == '< 70'):
                logger.warning(
                    "Signal level not accurately measured (below -70 dBm)")
            else:
                stats['level'] = (float(signal_raw), "dBm")

            if (c_to_n_raw == '< 3'):
                logger.warning("SNR not accurately measured (below 3 dB)")
            else:
                stats['snr'] = (float(c_to_n_raw), "dB")

            stats['ber'] = (float(ber_raw), None)
            stats['pkt_err'] = (int(uncorr_raw), None)

        return stats

    def print_demod_config(self):
        """Get demodulator configurations via SNMP

        Returns:
            Bool indicating whether the demodulator configurations were printed
            successfully.

        """
        cfg = self._walk()
        if not cfg:
            return False

        # Map dictionary to more informative labels organized in sections
        label_map = {
            "Demodulator": {
                's400ModulationStandard' + self.demod + '.0': "Standard",
                's400LBandFrequency' + self.demod + '.0': "L-band Frequency",
                's400SymbolRate' + self.demod + '.0': "Symbol Rate",
                's400Modcod' + self.demod + '.0': "MODCOD"
            },
            "LNB Options": {
                's400LNBSupply.0': "LNB Power Supply",
                's400LOFrequency.0': "LO Frequency",
                's400Polarization.0': "Polarization",
                's400Enable22KHzTone.0': "22 kHz Tone",
                's400LongLineCompensation.0': "Long Line Compensation"
            },
            "MPE Options": {
                's400MpePid1Pid.0': "MPE PID",
                's400MpePid1RowStatus.0': "MPE PID Status"
            }
        }

        print("Firmware Version: {}".format(cfg['s400FirmwareVersion.0']))
        for section in label_map:
            print("{}:".format(section))
            for key in cfg:
                if key in label_map[section]:
                    label = label_map[section][key]
                    # Post-process the value on special cases
                    if (label == "MODCOD"):
                        val = "VCM" if cfg[key] == "31" else cfg[key]
                    elif (label == "Standard"):
                        val = cfg[key].upper()
                    else:
                        val = cfg[key]
                    print("- {}: {}".format(label, val))
        return True

    def configure(self, info, freq_corr):
        """Configure the S400

        Args:
            info (dict): User info dictionary.
            freq_corr (float): Frequency correction in MHz.

        """
        logger.info("Configuring the S400 receiver at {} via SNMP".format(
            self.address))

        l_band_freq = int(round(info['freqs']['l_band'] + freq_corr, 2) * 1e6)
        lo_freq = int(info['freqs']['lo'] * 1e6)
        sym_rate = defs.sym_rate[info['sat']['alias']]
        if (info['lnb']['pol'].lower() == "dual"
                and 'v1_pointed' in info['lnb'] and info['lnb']['v1_pointed']):
            pol = "horizontal" if (info['lnb']["v1_psu_voltage"] >= 16) else \
                "vertical"
        else:
            pol = "horizontal" if (info['sat']['pol'] == "H") else "vertical"
        if (info['lnb']['universal']
                and info['freqs']['dl'] > defs.ku_band_thresh):
            tone = 'enable'
        else:
            tone = 'disable'

        # Organize the target SNMP configs in the order in which they should be
        # applied to the S400 and by section. Ultimately, these are only
        # applied if not already set in the current config.
        current_cfg = self._walk()
        target_cfg = {
            'Interface RF{}'.format(self.demod): [
                ('s400ModulationStandard' + self.demod, 'dvbs2'),
                ('s400LBandFrequency' + self.demod, l_band_freq),
                ('s400SymbolRate' + self.demod, sym_rate),
                ('s400SymbolRateAuto' + self.demod, 'disable'),
            ],
            'LNB parameters': [
                ('s400LOFrequency', lo_freq),
                ('s400Polarization', pol),
                ('s400LongLineCompensation', 'disable'),
            ],
            'RF{} service'.format(self.demod): [
                ('s400Modcod' + self.demod, 'auto'),
                ('s400ForwardEntireStream' + self.demod, 'disable'),
            ]
        }

        # The MPE PIDs are kept on a table, on which three steps are required
        # to set a value (1 - set the row status to createAndWait; 2 - set the
        # target value; 3 - set the row status to active). If another PID is
        # already set, we must destroy its row first.
        mpe_section = "MPE PIDs"
        target_cfg[mpe_section] = []
        no_skip = set()
        for i_pid, pid in enumerate(defs.pids):
            val_oid = ('s400MpePid' + self.demod + 'Pid', i_pid)
            status_oid = ('s400MpePid' + self.demod + 'RowStatus', i_pid)
            val_oid_str = _tuple_to_dotted_str(val_oid)
            status_oid_str = _tuple_to_dotted_str(status_oid)
            if val_oid_str in current_cfg and status_oid_str in current_cfg:
                if current_cfg[val_oid_str] == str(pid) and \
                        current_cfg[status_oid_str] == 'active':
                    continue  # already set
                else:
                    target_cfg[mpe_section].append((status_oid, 'destroy'))
            target_cfg[mpe_section].append((status_oid, 'createAndWait'))
            target_cfg[mpe_section].append((val_oid, pid))
            target_cfg[mpe_section].append((status_oid, 'active'))
            # If we detected that we need to change the MPE row here, do not
            # skip its columns later. This prevents a scenario like the
            # following. Suppose the RowStatus column is already set to active,
            # but the PID is wrong. In this case, the logic that follows would
            # want to change the PID only, and not the RowStatus, whereas, in
            # reality, we need to change both. The RowStatus must go over two
            # or three states in a row (destroy -> createAndWait -> active).
            no_skip.add(val_oid_str)
            no_skip.add(status_oid_str)

        target_cfg["LNB power"] = [
            ('s400LNBSupply', 'enabled'),
            ('s400Enable22KHzTone', tone),
        ]

        for section in target_cfg.keys():
            set_calls = 0
            if self.dry:
                logger.info(section)
            else:
                logger.info("Configuring {}".format(section))

            for config_tuple in target_cfg[section]:
                key, val = config_tuple
                if isinstance(key, tuple):
                    key = _tuple_to_dotted_str(key)
                else:
                    key += '.0'

                # Apply the configuration only if not set yet
                if key in current_cfg:
                    current_val = current_cfg[key]

                    # Convert to int in case the value is an int
                    try:
                        current_val = int(current_val)
                    except ValueError:
                        pass

                    if val == current_val and key not in no_skip:
                        logger.debug("Option {} already set to {}".format(
                            key, val))
                        continue  # already set

                set_calls += 1
                if not self._set(config_tuple):
                    if (not self.dry):
                        logger.error("SNMP configuration error")
                    return

            if self.dry and set_calls == 0:
                logger.info("- Already configured")

        if (not self.dry):
            logger.info("Receiver configured successfully")


def _parse_address(user_info, arg_addr):
    """Parse the receiver's IP address"""
    # If the command-line address argument is defined, prioritize it over the
    # address configured on the JSON config file
    if (arg_addr is not None):
        raw_addr = arg_addr
    elif "rx_ip" in user_info["setup"]:
        raw_addr = user_info["setup"]["rx_ip"]
    else:
        raw_addr = defs.default_standalone_ip_addr

    try:
        validated_addr = ip_address(raw_addr)
    except ValueError:
        logger.error("{} is not a valid IPv4 address".format(raw_addr))
        return
    return str(validated_addr)


def subparser(subparsers):  # pragma: no cover
    p = subparsers.add_parser('standalone',
                              description="Standalone DVB-S2 receiver manager",
                              help='Manage the standalone DVB-S2 receiver',
                              formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-a', '--address', help="Standalone receiver\'s IP address")
    p.add_argument('-p',
                   '--port',
                   default=161,
                   type=int,
                   help="Port of the receiver\'s SNMP agent")
    p.add_argument('-d',
                   '--demod',
                   default="1",
                   choices=["1", "2"],
                   help="Target demodulator within the S400")
    p.set_defaults(func=print_help)

    subsubparsers = p.add_subparsers(title='subcommands',
                                     help='Target sub-command')

    # Configuration
    p1 = subsubparsers.add_parser(
        'config',
        aliases=['cfg'],
        description='Initial configurations',
        help='Configure the standalone receiver and the host')
    p1.add_argument('-i',
                    '--interface',
                    default=None,
                    help='Network interface connected to the standalone \
                    receiver')
    p1.add_argument('-y',
                    '--yes',
                    default=False,
                    action='store_true',
                    help="Default to answering Yes to configuration prompts")
    p1.add_argument('--host-only',
                    default=False,
                    action='store_true',
                    help="Configure the host only and skip the receiver "
                    "configuration")
    p1.add_argument('--rx-only',
                    default=False,
                    action='store_true',
                    help="Configure the receiver only and skip the host "
                    "configuration")
    p1.add_argument("--dry-run",
                    action='store_true',
                    default=False,
                    help="Print all commands but do not execute them")
    p1.add_argument('--freq-corr',
                    default=0,
                    type=float,
                    help='Carrier frequency offset correction in kHz')
    p1.set_defaults(func=cfg_standalone)

    # Monitoring
    p2 = subsubparsers.add_parser(
        'monitor',
        description="Monitor the standalone receiver",
        help='Monitor the standalone receiver',
        formatter_class=ArgumentDefaultsHelpFormatter)
    # Add the default monitoring options used by other modules
    monitoring.add_to_parser(p2)
    p2.set_defaults(func=monitor)

    return p


def _common(args):
    user_info = config.read_cfg_file(args.cfg, args.cfg_dir)
    if (user_info is None):
        return

    util.check_configured_setup_type(user_info, defs.standalone_setup_type,
                                     logger)

    return user_info


def cfg_standalone(args):
    """Configure the standalone receiver and the host

    Set all parameters required on the standalone receiver: signal, LNB, and
    MPE parameters. Then, configure the host to communicate with the the
    standalone DVB-S2 receiver by setting reverse-path filters and firewall
    configurations.

    """
    user_info = _common(args)
    if (user_info is None):
        return

    if (not args.host_only):
        freq_corr_mhz = args.freq_corr / 1e3
        if round(freq_corr_mhz, 2) != freq_corr_mhz:
            logger.error(
                "Please specify the frequency correction parameter as "
                "a multiple of 10 kHz")
            sys.exit(1)

    # Configure the subprocess runner
    runner.set_dry(args.dry_run)

    # IP Address
    rx_ip_addr = _parse_address(user_info, args.address)

    if (not args.rx_only):
        if 'netdev' not in user_info['setup']:
            assert (args.interface is not None), \
                ("Please specify the network interface through option "
                 "\"-i/--interface\"")

        interface = args.interface if (args.interface is not None) else \
            user_info['setup']['netdev']

        # Check if all dependencies are installed
        if (not dependencies.check_apps(["iptables"])):
            return

        rp.set_filters([interface], prompt=(not args.yes), dry=args.dry_run)
        firewall.configure([interface],
                           defs.src_ports,
                           user_info['sat']['ip'],
                           igmp=True,
                           prompt=(not args.yes),
                           dry=args.dry_run)

    if (not args.host_only):
        util.print_header("Receiver Configuration")
        s400 = S400Client(args.demod, rx_ip_addr, args.port, dry=args.dry_run)
        s400.check_reachable()
        s400.configure(user_info, freq_corr_mhz)


def _get_monitor(args):
    """Create an object of the Monitor class

    Args:
        args : Parser arguments.

    """
    return monitoring.Monitor(args.cfg_dir,
                              logfile=args.log_file,
                              scroll=args.log_scrolling,
                              min_interval=args.log_interval,
                              server=args.monitoring_server,
                              port=args.monitoring_port,
                              report=args.report,
                              report_opts=monitoring.get_report_opts(args),
                              utc=args.utc)


def monitor(args, monitor: monitoring.Monitor = None):
    """Monitor the standalone DVB-S2 receiver"""
    # User info
    user_info = _common(args)
    if (user_info is None):
        return

    # IP Address
    rx_ip_addr = _parse_address(user_info, args.address)

    # Client to the S400's SNMP agent
    s400 = S400Client(args.demod, rx_ip_addr, args.port)

    util.print_header("Novra S400 Receiver")
    s400.check_reachable()
    s400.print_demod_config()

    # Log Monitoring
    if monitor is None:
        monitor = _get_monitor(args)

    util.print_header("Receiver Monitoring")

    # Fetch the receiver stats periodically
    c_time = time.time()
    while (not monitor.disable_event.is_set()):
        try:
            stats = s400.get_stats()

            if (stats is not None):
                monitor.update(stats)

            next_print = c_time + args.log_interval
            if (next_print > c_time):
                time.sleep(next_print - c_time)
            c_time = time.time()

        except KeyboardInterrupt:
            break


def print_help(args):
    """Re-create argparse's help menu for the standalone command"""
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(title='', help='')
    parser = subparser(subparsers)
    print(parser.format_help())
