import json
import logging
import os
import time
from enum import Enum

import requests

from ..cache import Cache
from . import bidding, pkt
from .error import log_error_and_exit, log_errors
from .invoice import print_invoice

logger = logging.getLogger(__name__)


class ApiChannel(Enum):
    ALL = 0
    USER = 1
    AUTH = 3
    GOSSIP = 4
    BTC_SRC = 5


API_CHANNELS = [x.value for x in ApiChannel]
API_CHANNEL_SSE_NAME = {
    ApiChannel.USER.value: 'transmissions',
    ApiChannel.AUTH.value: 'auth',
    ApiChannel.GOSSIP.value: 'gossip',
    ApiChannel.BTC_SRC.value: 'btc-src',
}
SENDABLE_API_CHANNELS = [x for x in API_CHANNELS if x != ApiChannel.ALL.value]
PAID_API_CHANNELS = [ApiChannel.USER.value]
ORDER_STATUS = [
    'pending', 'paid', 'transmitting', 'sent', 'received', 'cancelled',
    'expired', 'confirming'
]
ORDER_QUEUES = [
    'pending', 'paid', 'transmitting', 'confirming', 'queued', 'sent',
    'rx-pending', 'received', 'retransmitting'
]


class ApiOrder:
    """API Transmission Order

    Handles the payment/bidding for transmission of API messages.

    Args:
        server   : API server address where the order lives
        seq_num  : Sequence number corresponding to this API message
        tls_key  : API client key
        tls_cert : API client certificate

    """

    def __init__(self,
                 server,
                 seq_num=None,
                 tls_cert=None,
                 tls_key=None,
                 capture_error=False):
        self.uuid = None
        self.auth_token = None
        self.ln_invoice = None
        self.order = {}
        self.capture_error = capture_error

        # API server address
        self.server = server

        # TLS key/cert
        self.tls_cert = tls_cert
        self.tls_key = tls_key
        self.admin = tls_cert is not None and tls_key is not None

        # Transmission sequence number, if defined
        self.seq_num = seq_num

    def _prompt_for_uuid_token(self):
        """Ask user to provide the UUID and authentication token"""
        uuid = input("UUID: ") or None
        if (uuid is None):
            raise ValueError("Order UUID is required")

        auth_token = input("Authentication Token: ") or None
        if (auth_token is None):
            raise ValueError("Authentication Token is required")

        return uuid, auth_token

    def _fetch(self):
        """Fetch a specific order from the server"""
        assert (self.uuid is not None)
        assert (self.auth_token is not None)

        endpoint = '/admin/order/' if self.admin else '/order/'
        r = requests.get(self.server + endpoint + self.uuid,
                         headers={'X-Auth-Token': self.auth_token},
                         cert=(self.tls_cert, self.tls_key))

        if (r.status_code != requests.codes.ok):
            log_error_and_exit(r, logger, sys_exit_out=self.capture_error)

        r.raise_for_status()

        self.order = r.json()
        logger.debug(json.dumps(r.json(), indent=4, sort_keys=True))

    def get(self, uuid=None, auth_token=None):
        """Get the API order information

        Args:
            uuid       : Order UUID. If not defined, prompt user.
            auth_token : Authentication token. If not defined, prompt user.

        """
        if (uuid is None or auth_token is None):
            uuid, auth_token = self._prompt_for_uuid_token()

        self.uuid = uuid
        self.auth_token = auth_token
        self._fetch()

    def get_orders(self, status: list, channel=1, queue='queued', limit=20):
        """Get API orders with a target status

        Args:
            status (list): Filter the list of orders to contain orders with the
                the status in this list only.
            channel (int): Target channel. Defaults to channel 1.
            queue (str): Queue from which the order can be fetched (pending,
                queued, or sent orders). Defaults to the 'queued' queue.
            limit (int): Maximum number of orders on the result.

        Returns:
            list: List with the filtered orders.

        """
        assert queue in ORDER_QUEUES
        assert status is None or [x in ORDER_STATUS for x in status]
        endpoint = '/admin/orders/' + queue if self.admin \
            else '/orders/' + queue
        r = requests.get(self.server + endpoint,
                         params={
                             'channel': channel,
                             'limit': limit
                         },
                         headers={'X-Auth-Token': self.auth_token},
                         cert=(self.tls_cert, self.tls_key))

        if (r.status_code != requests.codes.ok):
            log_error_and_exit(r, logger, sys_exit_out=self.capture_error)

        r.raise_for_status()

        orders = r.json()

        if status is None:
            return orders

        filtered_orders = []
        for order in orders:
            if order['status'] in status:
                filtered_orders.append(order)

        return filtered_orders

    def send(self, data, bid, regions=None, channel=None):
        """Send the transmission order

        Args:
            data : Data as bytes array to broadcast over satellite
            bid  : Bid in msat
            regions : List of regions over which to send the order.

        Returns:
            Dictionary with order metadata

        """
        assert (isinstance(data, bytes))

        req_data = {}

        if bid is not None:
            req_data['bid'] = bid
        if (regions is not None and len(regions) > 0):
            req_data['regions'] = json.dumps(regions)
        if (channel is not None):
            req_data['channel'] = channel

        # Post request to the API
        endpoint = '/admin/order' if self.admin else '/order'
        r = requests.post(self.server + endpoint,
                          data=req_data,
                          files={'file': data},
                          cert=(self.tls_cert, self.tls_key))

        # In case of failure, check the API error message
        if (r.status_code != requests.codes.ok):
            log_error_and_exit(r, logger, sys_exit_out=self.capture_error)

        # Raise error if response status indicates failure
        r.raise_for_status()

        # Save the UUID and authentication token from the response
        res = r.json()
        self.uuid = res['uuid']
        self.auth_token = res['auth_token']

        # Print the response
        logger.debug("API Response:")
        logger.debug(json.dumps(res, indent=4, sort_keys=True))

        logger.info("Data successfully queued for transmission\n")
        print("--\nUUID:\n%s" % (res["uuid"]))
        print("--\nAuthentication Token:\n%s" % (res["auth_token"]))

        if ("lightning_invoice" in res):
            self.ln_invoice = res["lightning_invoice"]
            print_invoice(self.ln_invoice)

        return res

    def get_data(self):
        """Get data content sent over an API order"""
        logger.debug("Fetch message #%s from API" % (self.seq_num))

        endpoint = '/admin/message/' if self.admin else '/message/'
        r = requests.get(self.server + endpoint + str(self.seq_num),
                         cert=(self.tls_cert, self.tls_key))

        r.raise_for_status()

        if (r.status_code == requests.codes.ok):
            data = r.content
            return data

    def wait_state(self, target, timeout=120):
        """Wait until the order achieves a target state (or states)

        Args:
            target : String or list of strings with the state(s) to wait
                     for. When given as a list, this function waits until any
                     of the states is achieved.
            timeout : Timeout in seconds.

        Returns:
            (bool) Whether the state was successfully reached.

        """
        assert (isinstance(target, str) or isinstance(target, list))

        state_seen = {
            'pending': False,
            'paid': False,
            'transmitting': False,
            'sent': False,
            'received': False,
            'cancelled': False,
            'expired': False,
            'confirming': False
        }
        msg = {
            'pending': "- Waiting for payment confirmation...",
            'paid': "- Payment confirmed. Ready to launch transmission...",
            'transmitting': "- Transmission started...",
            'sent': "- Order successfully transmitted",
            'received': "- Reception confirmed by the ground station",
            'cancelled': "- Transmission cancelled",
            'expired': "- Order expired",
            'confirming': "- Confirming transmission...",
        }
        requires = {
            'pending': [],
            'paid': ['pending'],
            'transmitting': ['pending', 'paid'],
            'confirming': ['pending', 'paid', 'transmitting'],
            'sent': ['pending', 'paid', 'transmitting', 'confirming'],
            'received':
            ['pending', 'paid', 'transmitting', 'confirming', 'sent'],
            'cancelled': ['pending'],
            'expired': ['pending']
        }

        if (not isinstance(target, list)):
            target = [target]
        assert ([state in state_seen.keys() for state in target])

        s_time = time.time()
        self._stop_wait_state = False
        while (self._stop_wait_state is False):
            self._fetch()

            if (self.order['status'] in state_seen
                    and not state_seen[self.order['status']]):
                state_seen[self.order['status']] = True

                # If the status is not polled fast enough, some intermediate
                # states may not be seen. Mark the implied states as observed
                # and print their messages.
                for prereq_state in requires[self.order['status']]:
                    if (not state_seen[prereq_state]):
                        state_seen[prereq_state] = True
                        print(msg[prereq_state])

                # Print the current state
                print(msg[self.order['status']])

            if (any([state_seen[x] for x in target])):
                break

            c_time = time.time()
            if ((c_time - s_time) > timeout):
                print("Timeout")
                break

            time.sleep(0.5)

        return ('status' in self.order and self.order['status'] in target)

    def stop_wait_state(self):
        """Stop waiting for the order to achieve a target state"""
        self._stop_wait_state = True

    def confirm_tx(self, regions):
        """Confirm transmission of an API message

        Args:
            regions : Regions that were covered by the transmission

        """
        assert (self.seq_num is not None)

        if ((regions is None) or (self.tls_cert is None)
                or (self.tls_key is None)):
            return

        assert (isinstance(regions, list))

        logger.info("Confirm transmission of message {} on regions {}".format(
            self.seq_num, regions))

        r = requests.post(self.server + '/order/tx/' + str(self.seq_num),
                          data={'regions': json.dumps(regions)},
                          cert=(self.tls_cert, self.tls_key))

        if not r.ok:
            logger.error("Failed to confirm Tx of message {} "
                         "[status code {}]".format(self.seq_num,
                                                   r.status_code))
            log_errors(logger, r)
        else:
            logger.info("Server response: " + r.json()['message'])

    def confirm_rx(self, region):
        """Confirm reception of an API message

        Args:
            region : Coverage region

        """
        assert (self.seq_num is not None)

        if ((region is None) or (self.tls_cert is None)
                or (self.tls_key is None)):
            return

        logger.info("Confirm reception of API message {} on region {}".format(
            self.seq_num, region))

        r = requests.post(self.server + '/order/rx/' + str(self.seq_num),
                          data={'region': region},
                          cert=(self.tls_cert, self.tls_key))

        if not r.ok:
            logger.error("Failed to confirm Rx of message {} "
                         "[status code {}]".format(self.seq_num,
                                                   r.status_code))
            log_errors(logger, r)
        else:
            logger.info("Server response: " + r.json()['message'])

    def bump(self, bid=None):
        """Bump the order

        Args:
            bid : New bid in msat. If not defined, prompt user.

        Returns:
            Dictionary with order metadata

        """
        if (not self.order):
            self._fetch()

        if (self.order["status"] == "transmitting"):
            raise ValueError("Cannot bump order - already in transmission")

        if (self.order["status"] == "sent"
                or self.order["status"] == "received"):
            raise ValueError("Cannot bump order - already transmitted")

        if (self.order["status"] == "cancelled"
                or self.order["status"] == "expired"):
            raise ValueError("Order already {}".format(self.order["status"]))

        if (self.order["unpaid_bid"] > 0):
            unpaid_bid_msg = "(%d msat paid, %d msat unpaid)" % (
                self.order["bid"], self.order["unpaid_bid"])
        else:
            unpaid_bid_msg = ""

        previous_bid = self.order["bid"] + self.order["unpaid_bid"]
        tx_len = pkt.calc_ota_msg_len(self.order["message_size"])

        logger.info("Previous bid was {:d} msat for {:d} bytes {}".format(
            previous_bid, tx_len, unpaid_bid_msg))

        logger.info("Paid bid ratio is currently {:.2f} msat/byte".format(
            self.order["bid_per_byte"]))
        logger.info("Total (paid + unpaid) bid ratio is currently {:.2f} "
                    "msat/byte".format(float(previous_bid) / tx_len))

        if (bid is None):
            # Ask for new bid
            bid = bidding.ask_bid(tx_len, previous_bid)

        assert (isinstance(bid, int))

        # Post bump request
        r = requests.post(self.server + '/order/' + self.uuid + "/bump",
                          data={
                              'bid_increase': bid - previous_bid,
                              'auth_token': self.auth_token
                          },
                          cert=(self.tls_cert, self.tls_key))

        if (r.status_code != requests.codes.ok):
            log_error_and_exit(r, logger, sys_exit_out=self.capture_error)

        r.raise_for_status()

        # Print the response
        res = r.json()
        logger.debug("API Response:")
        logger.debug(json.dumps(res, indent=4, sort_keys=True))

        logger.info("Order bumped successfully\n")
        print_invoice(res["lightning_invoice"])

        return res

    def delete(self):
        """Delete the order

        Returns:
            API response

        """
        if (not self.order):
            self._fetch()

        # Post delete request
        endpoint = '/admin/order/' if self.admin else '/order/'
        r = requests.delete(self.server + endpoint + self.uuid,
                            headers={'X-Auth-Token': self.auth_token},
                            cert=(self.tls_cert, self.tls_key))

        if (r.status_code != requests.codes.ok):
            log_error_and_exit(r, logger, sys_exit_out=self.capture_error)

        r.raise_for_status()

        # Print the response
        logger.info("Order deleted successfully")

        logger.debug("API Response:")
        logger.debug(json.dumps(r.json(), indent=4, sort_keys=True))

        return r.json()

    def record_tx_log(self, cfg_dir: str):
        """Record the transmission information locally"""
        if (self.auth_token is None or self.uuid is None):
            logger.error("Cannot record tx log. Auth token or UUID not set")
            return

        cache = Cache(os.path.join(cfg_dir, "api"), filename="tx_log.json")
        record = {'auth_token': self.auth_token}
        if self.ln_invoice:
            record['invoices'] = [self.ln_invoice]
        cache.set(self.uuid, record)
        cache.save()
        return True

    def record_tx_bump_log(self, cfg_dir: str, invoice: dict):
        """Record the bump transaction information locally"""
        cache = Cache(os.path.join(cfg_dir, "api"), filename="tx_log.json")
        record = cache.get(self.uuid)
        if record:
            record['invoices'].append(invoice)
            cache.set(self.uuid, record)
            cache.save()
            return True
        return False
