import json
import logging
import requests
import sys
import threading
import time
from argparse import ArgumentDefaultsHelpFormatter
from ipaddress import ip_address
from urllib.parse import urlencode

from . import config
from . import defs
from . import dependencies
from . import monitoring
from . import tsp
from . import util
from .upnp import UPnP

logger = logging.getLogger(__name__)


class SatIp():
    """Sat-IP Client

    Finds a Sat-IP server via UPnP, authenticates with the server, and fetches
    DVB-S2 frontend metrics.

    """
    def __init__(self, ip_addr=None, port=8000):
        """Constructor

        Args:
            ip_addr : IP address of the Sat-IP server.
            port : Sat-IP server's HTTP port.

        """
        self.session = None

        if (ip_addr is not None):
            self.set_addr(ip_addr, port)
        else:
            self.base_url = None
            self.host = None

    def _parse_fe_info(self, fe_info):
        """Parse frontend information returned by the server"""
        signal_level = ((10 * float(fe_info['sq'])) - 3440) / 48
        quality = float(fe_info['ber']) * 100 / 15
        lock = fe_info['ls'] == 'yes'
        # Note:
        # - The 'sq' metric is mapped to the signal level in dBm.
        # - The 'ber' value returned by the server (the antenna) is a number
        #   from 0 to 15 related to the signal quality metric mentioned in
        #   Section 3.5.7 of the Sat-IP specification.
        return {
            'lock': (lock, None),
            'level': (signal_level, 'dBm'),
            'quality': (quality, '%')
        }

    def _set_from_ssdp_dev(self, dev):
        """Set the base URL and host based on info discovered via SSDP"""
        self.base_url = dev['base_url']
        self.host = dev['host']

    def set_addr(self, ip_addr, port=8000):
        """Set the base URL and host address directly"""
        self.base_url = "http://" + ip_addr + ":" + str(port)
        self.host = ip_addr

    def discover(self, interactive=True, src_port=None):
        """Discover the Sat-IP receivers in the local network via UPnP"""
        upnp = UPnP(src_port)
        devices = upnp.discover()

        if (len(devices) == 0):
            return

        # Filter the Sat-IP devices
        sat_ip_devices = [{
            'host': d.host,
            'base_url': d.base_url
        } for d in devices if d.friendly_name == "SELFSAT-IP"]
        # Note: convert to dictionary so that _ask_multiple_choice can
        # deep-copy the selected element (which would not work for the original
        # SSDPDevice object).

        if (len(sat_ip_devices) == 0):
            return

        if (len(sat_ip_devices) > 1):
            if (not interactive):
                logger.warning("Found multiple Sat-IP receivers.")
                logger.warning("Selecting the receiver at {}".format(
                    sat_ip_devices[0]['host']))
                logger.info(
                    "You can specify the receiver using option -a/--addr or "
                    "run in interactive mode")
                self._set_from_ssdp_dev(sat_ip_devices[0])
            else:
                logger.info("Found multiple Sat-IP receivers.")
                selected = util._ask_multiple_choice(
                    sat_ip_devices,
                    "Select the Sat-IP receiver by IP address:",
                    "Sat-IP receiver",
                    lambda x: "Receiver at {}".format(x['host']))
                self._set_from_ssdp_dev(selected)
        else:
            self._set_from_ssdp_dev(sat_ip_devices[0])

    def login(self, username, password):
        """Login with the Sat-IP HTTP server"""
        # Cache the credentials to allow auto reconnection
        self.username = username
        self.password = password

        url = self.base_url + "/cgi-bin/login.cgi"
        self.session = requests.Session()
        r = self.session.post(url,
                              data={
                                  'cmd': 'login',
                                  'username': username,
                                  'password': password
                              })
        r.raise_for_status()

    def fe_stats(self):
        """Read DVB-S2 stats"""
        url = self.base_url + "/cgi-bin/index.cgi"
        rv = self.session.get(url, params={'cmd': 'frontend_info'})

        try:
            info = rv.json()
        except json.decoder.JSONDecodeError:
            if ("/cgi-bin/login.cgi" in rv.text and rv.status_code == 200):
                logger.warning("Sat-IP server has closed the session. "
                               "Reconnecting.")
                self.login(self.username, self.password)
            return

        if 'frontends' not in info:
            return

        for fe in rv.json()['frontends']:
            if fe['frontend']['ip'] != 'none':
                return self._parse_fe_info(fe['frontend'])


def _parse_modcod(modcod):
    """Convert a given modcod into a dict with modulation type and code rate"""
    mtypes = ['qpsk', '8psk', '16apsk', '32apsk']
    for mtype in mtypes:
        if mtype in modcod:
            fec = modcod.replace(mtype, '')
            return {'mtype': mtype, 'fec': fec}
    raise ValueError("Unsupported MODCOD {}".format(modcod))


def _get_monitor(args):
    """Create an object of the Monitor class

    Args:
        args      : SDR parser arguments
        sat_name  : Satellite name

    """
    # Force scrolling logs if tsp is configured to print to stdout
    scrolling = tsp.prints_to_stdout(args) or args.log_scrolling

    return monitoring.Monitor(args.cfg_dir,
                              logfile=args.log_file,
                              scroll=scrolling,
                              min_interval=args.log_interval,
                              server=args.monitoring_server,
                              port=args.monitoring_port,
                              report=args.report,
                              report_opts=monitoring.get_report_opts(args),
                              utc=args.utc)


def _monitoring_thread(sat_ip, handler):
    """Loop used to monitor the DVB-S2 frontend on a thread"""
    while (True):
        time.sleep(1)

        status = sat_ip.fe_stats()

        if (status is None):
            logger.warning("Failed to fetch the frontend status.")
            continue

        handler.update(status)


def subparser(subparsers):
    """Parser for sdr command"""
    p = subparsers.add_parser('sat-ip',
                              description="Launch a Sat-IP receiver",
                              help='Launch a Sat-IP receiver',
                              formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-a', '--addr', help='Sat-IP antenna IP address')
    p.add_argument('-m',
                   '--modcod',
                   choices=defs.modcods.keys(),
                   default='qpsk3/5',
                   metavar='',
                   help="DVB-S2 modulation and coding (MODCOD) scheme. "
                   "Choose from: " + ", ".join(defs.modcods.keys()))
    p.add_argument('-u',
                   '--username',
                   default="admin",
                   help='Sat-IP client username')
    p.add_argument('-p',
                   '--password',
                   default="admin",
                   help='Sat-IP client password')
    p.add_argument('--ssdp-src-port',
                   type=int,
                   help="Source port set on SSDP packets used to discover the "
                   "Sat-IP server(s) in the network")
    tsp.add_to_parser(p)
    monitoring.add_to_parser(p)
    p.set_defaults(func=launch)
    return p


def launch(args):
    info = config.read_cfg_file(args.cfg, args.cfg_dir)
    if (info is None):
        return

    if (info['setup']['type'] != defs.sat_ip_setup_type):
        logger.error("Setup not configured for {} receiver".format(
            defs.sat_ip_setup_type))
        logger.info("Run \"blocksat-cli cfg\" to re-configure your setup")
        sys.exit(1)

    if (not dependencies.check_apps(['tsp'])):
        return

    # Discover or define the IP address to communicate with the Sat-IP server
    sat_ip = SatIp()
    if args.addr is None:
        sat_ip.discover(src_port=args.ssdp_src_port)
        if (sat_ip.host is None):
            logger.error("Could not find a Sat-IP receiver")
            logger.info("Check your network or specify the receiver address "
                        "through option -a/--addr")
            sys.exit(1)
    else:
        addr = args.addr
        try:
            ip_address(addr)
        except ValueError as e:
            logger.error(e)
            sys.exit(1)
        sat_ip.set_addr(addr)

    # Login with the Sat-IP HTTP server
    sat_ip.login(args.username, args.password)

    # Tuning parameters
    modcod = _parse_modcod(args.modcod)
    pilots = 'on' if defs.pilots else 'off'
    sym_rate = defs.sym_rate[info['sat']['alias']]
    params = {
        'src': 1,
        'freq': info['sat']['dl_freq'],
        'pol': info['sat']['pol'].lower(),
        'ro': defs.rolloff,
        'msys': 'dvbs2',
        'mtype': modcod['mtype'],
        'plts': pilots,
        'sr': int(sym_rate / 1e3),
        'fec': modcod['fec'].replace('/', ''),
        'pids': ",".join([str(pid) for pid in defs.pids])
    }
    url = "http://" + sat_ip.host + "/?" + urlencode(params)

    # Run tsp
    tsp_handler = tsp.Tsp()
    if (not tsp_handler.gen_cmd(args,
                                in_plugin=['-I', 'http', url, '--infinite'])):
        return
    logger.debug("Run:")
    logger.debug(" ".join(tsp_handler.cmd))
    tsp_handler.run()

    # Launch the monitoring thread
    monitor = _get_monitor(args)
    t = threading.Thread(target=_monitoring_thread,
                         args=(sat_ip, monitor),
                         daemon=True)
    t.start()

    try:
        tsp_handler.proc.communicate()
    except KeyboardInterrupt:
        tsp_handler.proc.kill()

    print()
