"""Standalone Receiver"""
import ipaddress
import logging
import os
import time
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from pysnmp.hlapi import SnmpEngine, ObjectType, ObjectIdentity, \
     getCmd, setCmd, nextCmd, CommunityData, ContextData, UdpTransportTarget

from . import rp, firewall, defs, config, dependencies, util, monitoring

logger = logging.getLogger(__name__)
runner = util.ProcessRunner(logger)


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
        assert (ipaddress.ip_address(address))  # parse address
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

    def _get(self, *variables):
        """Get one or more variables via SNMP

        Args:
            Tuple with the variables to fetch via SNMP.

        Returns:
            List of tuples with the fetched keys and values.

        """
        obj_types = []
        for var in variables:
            if isinstance(var, tuple):
                obj = ObjectType(
                    ObjectIdentity(self.mib, var[0],
                                   var[1]).addMibSource(self.mib_dir))
            else:
                obj = ObjectType(
                    ObjectIdentity(self.mib, var,
                                   0).addMibSource(self.mib_dir))
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

        """
        if (self.dry):
            # Convert to the corresponding net-snmp command
            # TODO: convert the string values that actually represent integers.
            for key, val in key_vals:
                if (isinstance(key, tuple)):
                    key = ".".join([str(x) for x in key])
                val_type = "s" if isinstance(val, str) else "i"
                print("> snmpset -v 2c -c public {}:{} {}::{} {} {}".format(
                    self.address, self.port, self.mib, key, val_type, val))
            return

        obj_types = []
        for key, val in key_vals:
            if isinstance(key, tuple):
                obj = ObjectType(
                    ObjectIdentity(self.mib, key[0],
                                   key[1]).addMibSource(self.mib_dir), val)
            else:
                obj = ObjectType(
                    ObjectIdentity(self.mib, key,
                                   0).addMibSource(self.mib_dir), val)
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
        stats = {'lock': (signal_lock, None)}

        # Metrics that require locking
        #
        # NOTE: the S400 does not return the signal level if unlocked.
        if (signal_lock):
            level = float('nan') if (signal_raw
                                     == '< 70') else float(signal_raw)
            cnr = float('nan') if (c_to_n_raw == '< 3') else float(c_to_n_raw)
            stats['snr'] = (cnr, "dB")
            stats['level'] = (level, "dBm")
            stats['ber'] = (float(ber_raw), None)
            stats['pkt_err'] = (int(uncorr_raw), None)

        return stats

    def print_demod_config(self):
        """Get demodulator configurations via SNMP

        Returns:
            Bool indicating whether the demodulator configurations were printed
            successfully.

        """
        res = self._get(
            's400FirmwareVersion',
            # Demodulator
            's400ModulationStandard' + self.demod,
            's400LBandFrequency' + self.demod,
            's400SymbolRate' + self.demod,
            's400Modcod' + self.demod,
            # LNB
            's400LNBSupply',
            's400LOFrequency',
            's400Polarization',
            's400Enable22KHzTone',
            's400LongLineCompensation',
            # MPE
            ('s400MpePid1Pid', 0),
            ('s400MpePid1Pid', 1),
            ('s400MpePid1RowStatus', 0),
            ('s400MpePid1RowStatus', 1))

        if (res is None):
            return False

        # Form dictionary with the S400 configs
        cfg = {}
        for res in res:
            key = res[0].replace('NOVRA-s400-MIB::s400', '')
            val = res[1]
            cfg[key] = val

        # Map dictionary to more informative labels
        demod_label_map = {
            'ModulationStandard' + self.demod + '.0': "Standard",
            'LBandFrequency' + self.demod + '.0': "L-band Frequency",
            'SymbolRate' + self.demod + '.0': "Symbol Rate",
            'Modcod' + self.demod + '.0': "MODCOD",
        }
        lnb_label_map = {
            'LNBSupply.0': "LNB Power Supply",
            'LOFrequency.0': "LO Frequency",
            'Polarization.0': "Polarization",
            'Enable22KHzTone.0': "22 kHz Tone",
            'LongLineCompensation.0': "Long Line Compensation"
        }
        mpe_label_map = {
            'MpePid1Pid.0': "MPE PID",
            'MpePid1RowStatus.0': "MPE PID Status"
        }
        label_map = {
            "Demodulator": demod_label_map,
            "LNB Options": lnb_label_map,
            "MPE Options": mpe_label_map
        }

        print("Firmware Version: {}".format(cfg['FirmwareVersion.0']))
        for map_key in label_map:
            print("{}:".format(map_key))
            for key in cfg:
                if key in label_map[map_key]:
                    label = label_map[map_key][key]
                    if (label == "MODCOD"):
                        val = "VCM" if cfg[key] == "31" else cfg[key]
                    elif (label == "Standard"):
                        val = cfg[key].upper()
                    else:
                        val = cfg[key]
                    print("- {}: {}".format(label, val))
        return True

    def configure(self, info):
        """Configure the S400"""
        logger.info("Configuring the S400 receiver at {} via SNMP".format(
            self.address))

        # Local parameters
        l_band_freq = int(info['freqs']['l_band'] * 1e6)
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

        # Fetch and delete the current MPE PIDs
        if (not self.dry):
            logger.info("Resetting MPE PIDs")
            current_cfg = self._walk()
        else:
            current_cfg = {}
        mpe_prefix = 's400MpePid' + self.demod
        for key in current_cfg:
            mpe_row_status = mpe_prefix + "RowStatus"
            if mpe_row_status in key:
                self._set((tuple(key.split(".")), 'destroy'))

        # Configure via SNMP
        logger.info("Configuring interface RF{}".format(self.demod))
        self._set(('s400ModulationStandard' + self.demod, 'dvbs2'))
        self._set(('s400LBandFrequency' + self.demod, l_band_freq))
        self._set(('s400SymbolRate' + self.demod, sym_rate))
        self._set(('s400SymbolRateAuto' + self.demod, 'disable'))

        logger.info("Setting LNB parameters")
        self._set(('s400LOFrequency', lo_freq))
        self._set(('s400Polarization', pol))
        self._set(('s400LongLineCompensation', 'disable'))

        logger.info("Configuring the RF{} service".format(self.demod))
        self._set(('s400Modcod' + self.demod, 'auto'))
        self._set(('s400ForwardEntireStream' + self.demod, 'disable'))

        # Set the target PIDs
        for i_pid, pid in enumerate(defs.pids):
            logger.info("Adding MPE PID {}".format(pid))
            self._set((('s400MpePid' + self.demod + 'RowStatus', i_pid),
                       'createAndWait'))
            self._set((('s400MpePid' + self.demod + 'Pid', i_pid), pid))
            self._set(
                (('s400MpePid' + self.demod + 'RowStatus', i_pid), 'active'))

        logger.info("Turning on the LNB power")
        self._set(('s400LNBSupply', 'enabled'))
        if (tone == 'enable'):
            logger.info("Enabling the LNB 22kHz tone")
        self._set(('s400Enable22KHzTone', tone))

        if (not self.dry):
            logger.info("Receiver configured successfully")


def subparser(subparsers):
    p = subparsers.add_parser('standalone',
                              description="Standalone DVB-S2 receiver manager",
                              help='Manage the standalone DVB-S2 receiver',
                              formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-a',
                   '--address',
                   default="192.168.1.2",
                   help="Address of the receiver's SNMP agent")
    p.add_argument('-p',
                   '--port',
                   default=161,
                   type=int,
                   help="Port of the receiver's SNMP agent")
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


def cfg_standalone(args):
    """Configure the standalone receiver and the host

    Set all parameters required on the standalone receiver: signal, LNB, and
    MPE parameters. Then, configure the host to communicate with the the
    standalone DVB-S2 receiver by setting reverse-path filters and firewall
    configurations.

    """
    user_info = config.read_cfg_file(args.cfg, args.cfg_dir)

    if (user_info is None):
        return

    # Configure the subprocess runner
    runner.set_dry(args.dry_run)

    if (not args.rx_only):
        if 'netdev' not in user_info['setup']:
            assert(args.interface is not None), \
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
        util._print_header("Receiver Configuration")
        s400 = S400Client(args.demod,
                          args.address,
                          args.port,
                          dry=args.dry_run)
        s400.configure(user_info)


def monitor(args):
    """Monitor the standalone DVB-S2 receiver"""

    # User info
    config.read_cfg_file(args.cfg, args.cfg_dir)

    # Client to the S400's SNMP agent
    s400 = S400Client(args.demod, args.address, args.port)

    util._print_header("Novra S400 Receiver")

    if (not s400.print_demod_config()):
        logger.error("s400 receiver at {}:{} is unreachable".format(
            s400.address, s400.port))
        return

    # Log Monitoring
    monitor = monitoring.Monitor(args.cfg_dir,
                                 logfile=args.log_file,
                                 scroll=args.log_scrolling,
                                 min_interval=args.log_interval,
                                 server=args.monitoring_server,
                                 port=args.monitoring_port,
                                 report=args.report,
                                 report_opts=monitoring.get_report_opts(args),
                                 utc=args.utc)

    util._print_header("Receiver Monitoring")

    # Fetch the receiver stats periodically
    c_time = time.time()
    while (True):
        try:
            stats = s400.get_stats()

            if (stats is None):
                return

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
