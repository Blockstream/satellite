import glob
import json
import logging
import requests
import os
import shutil
import sys
import threading
import time
import zipfile
from argparse import ArgumentDefaultsHelpFormatter
from distutils.version import StrictVersion
from ipaddress import ip_address
from urllib.parse import urlencode, quote

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

    def _assert_addr(self):
        """Assert that the Sat-IP device address has been discovered already"""
        if (self.base_url is None):
            raise RuntimeError("Sat-IP device address must be discovered or "
                               "informed first")

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

    def check_fw_version(self, min_version="3.1.18"):
        """Check if the Sat-IP server has the minimum required firmware version

        Returns:
            Boolean indicating whether the current firmware version satisfies
            the minimum required version. None if the attempt to read the
            current firmware version fails.

        """
        self._assert_addr()

        # Fetch the firmware version
        url = self.base_url + "/gmi_sw_ver.txt"
        r = requests.get(url)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(str(e))
            return None

        current_version = StrictVersion(r.text.strip('\n'))
        if (current_version < StrictVersion(min_version)):
            logger.error("A firmware upgrade is required on the Sat-IP "
                         "receiver.")
            logger.info("The current firmware version is {}, but the minimum "
                        "required version is {}.".format(
                            current_version, min_version))
            return False
        return True

    def set_urllib3_logger_critical(func):
        """Wrapper to change the urllib3 logging level while calling func

        This function is meant to avoid the MissingHeaderBodySeparatorDefect
        error leading to urllib3.exceptions.HeaderParsingError when parsing the
        headers. The urllib3's logging level is restricted before calling the
        given function. Subsequently, it is restored to the original level.

        """
        def inner(*args, **kwargs):
            urllib3_logger = logging.getLogger('urllib3')
            urllib3_logging_level = urllib3_logger.level
            urllib3_logger.setLevel(logging.CRITICAL)
            r = func(*args, **kwargs)
            urllib3_logger.setLevel(urllib3_logging_level)
            return r

        return inner

    @set_urllib3_logger_critical
    def _gmifu_req(self, params=None, files=None, method='post'):
        gmifu_server = os.path.join(self.base_url, "cgi-bin/gmifu.cgi")
        if (method == 'post'):
            r = requests.post(gmifu_server, params=params, files=files)
        else:
            r = requests.get(gmifu_server, params=params)

        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(str(e))
            return
        return r

    def upgrade_fw(self,
                   cfg_dir,
                   interactive=True,
                   factory_default='0',
                   no_wait=False):
        """Upgrade the Selfsat Sat-IP antenna's firmware

        Args:
            cfg_dir : User's configuration directory.
            interactive : Whether to run in interactive mode.
            factory_default : Whether to restore the factory default configs.
            no_wait : Do not wait for the complete reboot in the end.

        Returns:
            Boolean indicating whether the upgrade was successful.

        """
        self._assert_addr()

        if (interactive and not util._ask_yes_or_no("Proceed?")):
            logger.info("Aborting")
            return False

        logger.info("Upgrading the Sat-IP receiver's firmware.")

        # Initialize the upgrade procedure
        resp = self._gmifu_req(params={'cmd': 'fu_cmd_init'})
        if (resp is None):
            return False

        init_resp = resp.json()
        logger.debug("Firmware upgrade init response:")
        logger.debug(init_resp)
        if (init_resp['status'] != "0"):
            logger.error("({}) {}".format(init_resp['status'],
                                          init_resp['desc']))
            return False

        # Download the latest firmware version
        filename = quote("SAT>IP UPGRADE FIRMWARE.zip")
        download_url = os.path.join(
            ("https://s3.ap-northeast-2.amazonaws.com/"
             "logicsquare-seoul/a64d56aa-567b-4053-bc84-12c2e58e46a6/"),
            filename)
        tmp_dir = os.path.join(cfg_dir, "tmp")
        download_dir = os.path.join(tmp_dir, "sat-ip-fw")

        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        logger.info("Downloading the latest firmware version...")
        download_path = util.download_file(download_url,
                                           download_dir,
                                           dry_run=False,
                                           logger=logger)
        if (download_path is None):
            return False

        # Unzip the downloaded file
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            zip_ref.extractall(download_dir)

        # Find the software update .supg file:
        supg_files = glob.glob(os.path.join(download_dir, "**/*.supg"),
                               recursive=True)
        if (len(supg_files) > 1):
            logger.warning("Found multiple firmware update files")
            logger.info("Selecting {}".format(supg_files[0]))

        # Send the FW update file to the Sat-IP device
        logger.info("Uploading new firmware version to the Sat-IP server...")
        resp = self._gmifu_req(
            params={
                'cmd': 'fu_cmd_upload_file',
                'val': 'update'
            },
            files={'fw_signed_updfile': open(supg_files[0], 'rb')})

        # Cleanup the temporary download directory
        shutil.rmtree(tmp_dir)

        if (resp is None):
            return False

        # Get the update info
        resp = self._gmifu_req(params={'cmd': 'fu_cmd_get_upd_info'})
        if (resp is None):
            return False

        # Parse
        update_info = resp.json()
        logger.debug("Update info:")
        logger.debug(update_info)
        if ('thisver' not in update_info or 'newver' not in update_info):
            logger.error("Failed to parse the firmware update information")
            return False
        this_sw_ver = StrictVersion(update_info['thisver']['sw_ver'])
        new_sw_ver = StrictVersion(update_info['newver']['sw_ver'])

        # Check if the download really contains a newer version
        if (this_sw_ver >= new_sw_ver):
            logger.error("Downloaded firmware update does not contain a more "
                         "recent version.")
            logger.info("Downloaded version {}, but the Sat-IP server is "
                        "already running version {}.".format(
                            new_sw_ver, this_sw_ver))
            # Cancel the upgrade
            logger.info("Canceling the firmware upgrade.")
            resp = self._gmifu_req(params={'cmd': 'fu_cmd_cancel_upd'})
            return False

        # Start the update
        logger.info(
            "Upgrading firmware from version {} to version {}...".format(
                this_sw_ver, new_sw_ver))
        resp = self._gmifu_req(params={
            'cmd': 'fu_cmd_start_update',
            'factdft': factory_default
        })
        if (resp is None):
            return False

        # Reboot in the end
        logger.info("Upgrade done. Rebooting...")
        resp = self._gmifu_req(params={
            'cmd': 'fu_cmd_reboot',
            'factdft': factory_default
        })
        if (resp is None):
            return False

        # If so desired, wait until the device comes back
        if (no_wait):
            return True

        time.sleep(10)
        while (True):
            try:
                r = self._gmifu_req(method='get')
                if (r.ok):
                    break
            except requests.exceptions.ConnectionError:
                time.sleep(1)

        return True

    def login(self, username, password):
        """Login with the Sat-IP HTTP server"""
        self._assert_addr()
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
        """Read DVB-S2 frontend stats"""
        self._assert_addr()
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
    # Force scrolling logs if tsp is configured to print to stdout or if
    # operating in debug mode
    scrolling = tsp.prints_to_stdout(args) or args.debug or args.log_scrolling

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
            if (not handler.scroll):
                print()
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
    p.add_argument('--no-fe-monitoring',
                   default=True,
                   action='store_false',
                   dest='fe_monitoring',
                   help="Do not monitor the Sat-IP server's physical frontend "
                   "(DVB-S2 demodulator and tuner). Use this option when the "
                   "server does not provide a login page or to avoid "
                   "authentication conflicts between concurrent clients.")
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

    # Check if the Sat-IP device has the minimum required firmware version
    min_fw_version = "3.1.18" if args.fe_monitoring else "2.2.19"
    fw_version_ok = sat_ip.check_fw_version(min_fw_version)

    # Try to upgrade the firmware if necessary
    if (fw_version_ok is False):
        fw_upgrade_ok = sat_ip.upgrade_fw(args.cfg_dir)
        if (not fw_upgrade_ok):
            logger.error("Failed to upgrade the Sat-IP receiver's firmware")
            return
        # Check the version again after the upgrade
        fw_version_ok = sat_ip.check_fw_version()

    if (not fw_version_ok):
        return

    # Log in with the Sat-IP HTTP server to monitor the DVB-S2 frontend
    if (args.fe_monitoring):
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
    if (args.fe_monitoring):
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
