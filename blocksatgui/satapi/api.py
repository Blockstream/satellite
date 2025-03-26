import logging
import os

from blocksatcli import main
from blocksatcli.api import bidding, listen
from blocksatcli.api import msg as api_msg
from blocksatcli.api import pkt
from blocksatcli.api.api import get_server_addr
from blocksatcli.api.gpg import Gpg
from blocksatcli.api.order import ApiOrder
from blocksatcli.cache import Cache

from ..components import threadlogger, worker
from ..config import ConfigManager
from ..qt import QObject, QThreadPool, Signal

parser = main.get_parser()
logger = logging.getLogger(__name__)


class SatApi(QObject):

    sig_listener_state = Signal(str)
    sig_stop_listener = Signal()
    sig_gpg_pubkeys = Signal(list)
    sig_gpg_privkeys = Signal(list)
    sig_stop_wait_tx_payment = Signal()

    def __init__(self, config_manager: ConfigManager):
        super().__init__()

        self.config_manager = config_manager
        self.server = self.config_manager.api_server
        self.gui_cache = self.config_manager.gui_cache
        self.config_manager.sig_api_server.connect(self.set_server)
        self.gnupg_home = os.path.join(self.config_manager.cfg_dir, '.gnupg')
        self.gpg = Gpg(self.gnupg_home, interactive=False)
        api_dir = os.path.join(self.config_manager.cfg_dir, 'api')
        default_dir = os.path.join(api_dir, 'downloads')
        self.save_dir = (self.config_manager.gui_cache.get('api.save_dir')
                         or default_dir)
        self.bitcoin_net = (
            self.config_manager.gui_cache.get('api.bitcoin_net') or None)
        self.tx_logs_cache = Cache(api_dir, "tx_log.json")
        self.rx_info = None
        self._api_thread = QThreadPool()

    def set_server(self, server):
        self.server = server

    def set_rx_config(self, rx_config):
        """Set the loaded receiver configuration file"""
        self.rx_info = rx_config

    def save_cache(self, key, data):
        """Save data to cache"""
        self.gui_cache.load()
        if data is None:
            self.gui_cache.delete(key)
        else:
            self.gui_cache.set(key, data)
        self.gui_cache.save()

    def set_save_dir(self, save_dir):
        """Set the save directory"""
        self.save_dir = save_dir
        self.save_cache('api.save_dir', save_dir)

    def set_bitcoin_net(self, bitcoin_net):
        """Set the bitcoin network"""
        self.bitcoin_net = bitcoin_net
        self.save_cache('api.bitcoin_net', bitcoin_net)

    def _parse_args(self, cmd):
        args = parser.parse_args(cmd)

        # Set global options
        args.capture_error = True
        args.server = self.server if self.server is not None else None
        args.net = self.bitcoin_net if self.bitcoin_net is not None else None

        return args

    def _start_job(self, func, args=(), kwargs={}, callback=None):
        """Start a job in a separate thread"""
        worker.start_job(func=func,
                         args=args,
                         kwargs=kwargs,
                         callback=callback,
                         thread_pool=self._api_thread)

    def send(self, data, bid, is_file=False, callback=None, **kwargs):
        """Send message or file over Satellite API"""

        cmd = ['api', 'send']
        args = self._parse_args(cmd)
        args.no_wait = True
        args.bid = bid

        # Set optional arguments
        for key, value in kwargs.items():
            setattr(args, key, value)

        if is_file:
            args.file = data
        else:
            args.message = data

        self._start_job(args.func,
                        args=(
                            args,
                            self.gpg,
                        ),
                        kwargs={'capture_error': True},
                        callback=callback)

    def listen(self, output=None, **kwargs):
        cmd = ['api', 'listen']
        args = self._parse_args(cmd)

        # Set optional arguments
        for key, value in kwargs.items():
            setattr(args, key, value)

        if output is not None:
            logger = threadlogger.set_logger_handler('satapi_listen', output)
            listen.logger = logger  # Set custom logger
            api_msg.logger = logger

        # Set download directory
        args.save_dir = self.save_dir
        if (not os.path.exists(self.save_dir)):
            os.makedirs(self.save_dir)

        # Instantiate the listener object and connect the stop signal to the
        # listener stop method. Therefore, the listener can be stopped by
        # emitting the stop signal from the main thread.
        listen_loop = listen.ApiListener(recv_timeout=5)
        self.sig_stop_listener.connect(lambda: listen_loop.stop())

        def _callback(self):
            self.sig_listener_state.emit('stopped')

        self._start_job(args.func,
                        args=(
                            args,
                            listen_loop,
                            self.gpg,
                        ),
                        callback=lambda _: _callback(self))
        self.sig_listener_state.emit('started')

    def stop_listener(self):
        """Stop listening for incoming messages"""
        # No listener thread running
        if self._api_thread.activeThreadCount() == 0:
            self.sig_listener_state.emit('stopped')
            return

        self.sig_listener_state.emit('stopping')
        self.sig_stop_listener.emit()

    def suggest_bid(self, data_size, prev_bid=None):
        """Suggest a valid bid for the given data transmission length"""
        return bidding.suggest_bid(data_size, prev_bid)

    def calc_tx_size(self,
                     data,
                     is_file=False,
                     plaintext=False,
                     send_raw=False,
                     sign=False,
                     fec=False,
                     gpg=None,
                     recipient=None,
                     trust=False,
                     sign_key=None,
                     fec_overhead=0.1,
                     **kwargs):
        """Calculate the number of bytes used for satellite transmission"""
        if is_file:
            basename = data
            with open(data, 'rb') as f:
                data = f.read()
        else:
            data = data.encode()
            basename = None

        message = api_msg.generate(data,
                                   filename=basename,
                                   plaintext=plaintext,
                                   encapsulate=(not send_raw),
                                   sign=sign,
                                   fec=fec,
                                   gpg=gpg,
                                   recipient=recipient,
                                   trust=trust,
                                   sign_key=sign_key,
                                   fec_overhead=fec_overhead)
        return self.calc_ota_msg_len(message.get_length())

    def calc_ota_msg_len(self, msg_len):
        """Calculate the number of bytes used for satellite transmission"""
        return pkt.calc_ota_msg_len(msg_len)

    def get_gpg_keylist(self, private=False):
        """Get list of GPG keys"""

        def _callback(self, worker, private=False):
            if worker.error is not None:
                logger.info('Error getting GPG keylist')
                logger.error(worker.error.traceback)
                return

            if not worker.result:
                return

            keys = []
            for k in worker.result:
                keys.append({
                    'uids': k['uids'][0],
                    'fingerprint': k['fingerprint']
                })

            if private:
                self.sig_gpg_privkeys.emit(keys)
            else:
                self.sig_gpg_pubkeys.emit(keys)

        gpg = Gpg(self.gnupg_home, interactive=False)
        self._start_job(
            gpg.gpg.list_keys,
            args=(private, ),
            callback=lambda worker: _callback(self, worker, private))

    def has_gpg_pubkey(self):
        """Check if a public key is available"""
        return self.gpg.get_default_public_key() is not None

    def get_order_list(self,
                       status=None,
                       queue="queued",
                       limit=20,
                       callback=None):
        """Get list of queued messages"""
        cmd = ['api', 'list']
        args = self._parse_args(cmd)
        args.status = status
        args.queue = queue
        args.limit = limit
        self._start_job(args.func,
                        args=(args, ),
                        kwargs={
                            'verbose': False,
                            'capture_error': True
                        },
                        callback=callback)

    def get_order(self, uuid, auth_token, callback=None):
        """Get order information"""
        cmd = ['api', 'get']
        args = self._parse_args(cmd)
        args.uuid = uuid
        args.auth_token = auth_token
        self._start_job(args.func,
                        args=(args, ),
                        kwargs={
                            'verbose': False,
                            'capture_error': True
                        },
                        callback=callback)

    def delete_order(self, uuid, auth_token, callback=None):
        """Delete order"""
        cmd = ['api', 'delete']
        args = self._parse_args(cmd)
        args.uuid = uuid
        args.auth_token = auth_token
        self._start_job(args.func,
                        args=(args, ),
                        kwargs={'capture_error': True},
                        callback=callback)

    def bump_order(self, bid, uuid, auth_token, callback=None):
        """Bump order"""
        cmd = ['api', 'bump']
        args = self._parse_args(cmd)
        args.bid = bid
        args.uuid = uuid
        args.auth_token = auth_token
        self._start_job(args.func,
                        args=(args, ),
                        kwargs={'capture_error': True},
                        callback=callback)

    def wait_tx_payment(self, uuid, auth_token, callback=None):
        """Wait for payment of a transaction

        In the current implementation, there is no way to check for the invoice
        status. Therefore, this method checks for the transmission state. If
        the transmission is in the 'paid' or posterior state, it is assumed
        that the payment has been received.

        """
        target_state = ['paid']
        server = get_server_addr(self.bitcoin_net, self.server)
        order = ApiOrder(server)
        order.uuid = uuid
        order.auth_token = auth_token
        self.sig_stop_wait_tx_payment.connect(order.stop_wait_state)
        self._start_job(order.wait_state,
                        args=(target_state, ),
                        callback=callback)

    def stop_threads(self):
        """Stop all threads"""
        self.stop_listener()
