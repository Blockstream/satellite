import logging
import os
import socket

import requests

from blocksatcli import cache, defs

from . import utils
from .components.worker import start_job
from .qt import QObject, QThreadPool, Signal

logger = logging.getLogger(__name__)


class ConfigManager(QObject):
    """Manage the global configuration and states"""

    sig_on_internet = Signal(bool)
    sig_is_api_server_valid = Signal(bool)
    sig_api_server = Signal(str)
    sig_cfg_dir = Signal(str)  # User config directory
    sig_gpg_home = Signal(str)

    def __init__(self, cfg_dir=None) -> None:
        super().__init__()

        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(1)

        # GUI configuration
        self.gui_cfg_dir = cfg_dir or utils.get_default_cfg_dir()
        self.gui_cache = cache.Cache(self.gui_cfg_dir, ".blocksatgui")
        self.gui_cache.load()

        # User configuration
        self.cfg_dir = (cfg_dir or self.gui_cache.get('config.cfg_dir')
                        or utils.get_default_cfg_dir())
        self.gpg_home = self.gui_cache.get('config.gpg_home') or '.gnupg'
        self.gpg_dir = os.path.join(self.cfg_dir, self.gpg_home)

        # Update the GPG directory when the config directory changes.
        # The name of the home directory stays the same but the path changes.
        self.sig_cfg_dir.connect(lambda: self.set_gpg_home(self.gpg_home))

        self.on_internet = False
        self.api_valid = False

        self._load_cache()

    def _load_cache(self):
        api_server = self.gui_cache.get('api_server')
        if api_server is not None:
            self.set_api_server(self.gui_cache.get('api_server'))
        else:
            self.set_default_api_server()

    def _process_is_api_reachable_and_valid(self, worker):
        """Process the response to the request to check the API"""
        if worker.error is not None or worker.result is None:
            is_reachable, is_valid = False, False
        else:
            is_reachable, is_valid = worker.result

        logger.debug(f"Internet available: {is_reachable}")
        logger.debug(f"Valid API: {is_valid}")

        self.set_on_internet(is_reachable)
        self.set_api_valid(is_valid)

    def set_default_api_server(self):
        self.set_api_server(defs.api_server_url['main'])

    def set_api_server(self, api_server):
        self.api_server = api_server
        self.sig_api_server.emit(api_server)
        self.gui_cache.set('api_server', api_server)
        self.gui_cache.save()

    def set_on_internet(self, on_internet):
        self.on_internet = on_internet
        self.sig_on_internet.emit(on_internet)

    def set_api_valid(self, api_valid):
        self.api_valid = api_valid
        self.sig_is_api_server_valid.emit(api_valid)

    def is_server_valid(self):
        start_job(func=check_internet_and_api,
                  args=(self.api_server, ),
                  callback=self._process_is_api_reachable_and_valid,
                  thread_pool=self.thread_pool)

    def set_cfg_dir(self, cfg_dir):
        self.cfg_dir = cfg_dir
        self.save_gui_cache('config.cfg_dir', cfg_dir)
        self.sig_cfg_dir.emit(cfg_dir)

    def set_gpg_home(self, gpg_home):
        self.gpg_home = gpg_home
        self.save_gui_cache('config.gpg_home', gpg_home)
        self.gpg_dir = os.path.join(self.cfg_dir, self.gpg_home)
        self.sig_gpg_home.emit(self.gpg_home)

    def update(self):
        logger.debug("Checking internet and API")
        self.is_server_valid()

    def save_gui_cache(self, key, data):
        self.gui_cache.load()
        if data is None:
            self.gui_cache.delete(key)
        else:
            self.gui_cache.set(key, data)
        self.gui_cache.save()


def on_internet():
    """Check if internet is available by testing against google DNS server"""
    host = "8.8.8.8"
    port = 53
    try:
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        logger.error("No internet available")
        return False


def is_api_valid(server):
    """Check if API is valid"""
    is_valid = False
    try:
        url = os.path.join(server, 'info')
        r = requests.get(url, timeout=3)
    except requests.HTTPError as e:
        logger.error("API connection failed with status code {0}".format(
            e.response.requests.status_codes))
    except requests.ConnectionError:
        logger.error("API not found {}".format(server))
    except TimeoutError:
        logger.error("Connection to {} timeout".format(server))
    else:
        if isinstance(r, requests.Response):
            try:
                res = r.json()
                req_fields = ["lightning-dir", "num_active_channels"]
                if all([field in res for field in req_fields]):
                    is_valid = True
            except ValueError:
                pass

    return is_valid


def check_internet_and_api(server):
    internet_available = on_internet()
    api_valid = is_api_valid(server)
    return internet_available, api_valid
