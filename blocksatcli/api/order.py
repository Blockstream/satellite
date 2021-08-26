import json
import logging
import requests
import textwrap
import time
from . import bidding, pkt

logger = logging.getLogger(__name__)


class ApiOrder:
    """API Transmission Order

    Handles the payment/bidding for transmission of API messages.

    Args:
        server   : API server address where the order lives
        seq_num  : Sequence number corresponding to this API message
        tls_key  : API client key
        tls_cert : API client certificate

    """
    def __init__(self, server, seq_num=None, tls_cert=None, tls_key=None):
        self.uuid = None
        self.auth_token = None
        self.order = {}

        # API server address
        self.server = server

        # TLS key/cert
        self.tls_cert = tls_cert
        self.tls_key = tls_key

        # Transmission sequence number, if defined
        self.seq_num = seq_num

    def _print_error(self, error):
        """Print error returned by API server"""
        h = ("-----------------------------------------"
             "-----------------------------")
        if (isinstance(error, dict)):
            error_str = ""
            if ("title" in error):
                error_str += error["title"]
            if ("code" in error):
                error_str += " (code: {})".format(error["code"])
            logger.error(h)
            logger.error(textwrap.fill(error_str))
            if ("detail" in error):
                logger.error(textwrap.fill(error["detail"]))
            logger.error(h)
        else:
            logger.error(error)

    def _print_errors(self, r):
        """Print all errors returned on JSON response"""
        try:
            if "errors" in r.json():
                for error in r.json()["errors"]:
                    self._print_error(error)
        except ValueError:
            logger.error(r.text)

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

        r = requests.get(self.server + '/order/' + self.uuid,
                         headers={'X-Auth-Token': self.auth_token},
                         cert=(self.tls_cert, self.tls_key))

        if (r.status_code != requests.codes.ok):
            self._print_errors(r)

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

    def send(self, data, bid):
        """Send the transmission order

        Args:
            data : Data as bytes array to broadcast over satellite
            bid  : Bid in msats

        Returns:
            Dictionary with order metadata

        """
        assert (isinstance(data, bytes))

        # Post request to the API
        r = requests.post(self.server + '/order',
                          data={'bid': bid},
                          files={'file': data},
                          cert=(self.tls_cert, self.tls_key))

        # In case of failure, check the API error message
        if (r.status_code != requests.codes.ok
                and r.headers['content-type'] == "application/json"):
            self._print_errors(r)

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
            print("--\nAmount Due:\n%s millisatoshis\n" %
                  (res["lightning_invoice"]["msatoshi"]))
            print("--\nLightning Invoice Number:\n%s" %
                  (res["lightning_invoice"]["payreq"]))

        return res

    def get_data(self):
        """Get data content sent over an API order"""
        logger.debug("Fetch message #%s from API" % (self.seq_num))

        r = requests.get(self.server + '/message/' + str(self.seq_num),
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
            'expired': False
        }
        msg = {
            'pending': "- Waiting for payment confirmation...",
            'paid': "- Payment confirmed. Ready to launch transmission...",
            'transmitting': "- Order in transmission...",
            'sent': "- Order successfully transmitted",
            'received': "- Reception confirmed by the ground station",
            'cancelled': "- Transmission cancelled",
            'expired': "- Order expired"
        }
        requires = {
            'pending': [],
            'paid': ['pending'],
            'transmitting': ['pending', 'paid'],
            'sent': ['pending', 'paid', 'transmitting'],
            'received': ['pending', 'paid', 'transmitting', 'sent'],
            'cancelled': ['pending'],
            'expired': ['pending']
        }

        if (not isinstance(target, list)):
            target = [target]
        assert ([state in state_seen.keys() for state in target])

        s_time = time.time()
        while (True):
            self._fetch()

            if (not state_seen[self.order['status']]):
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
            self._print_errors(r)
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
            self._print_errors(r)
        else:
            logger.info("Server response: " + r.json()['message'])

    def bump(self, bid=None):
        """Bump the order

        Args:
            bid : New bid in msats. If not defined, prompt user.

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
            self._print_errors(r)

        r.raise_for_status()

        # Print the response
        logger.info("Order bumped successfully\n")

        print("--\nNew Lightning Invoice Number:\n%s\n" %
              (r.json()["lightning_invoice"]["payreq"]))
        print("--\nNew Amount Due:\n%s millisatoshis\n" %
              (r.json()["lightning_invoice"]["msatoshi"]))

        logger.debug("API Response:")
        logger.debug(json.dumps(r.json(), indent=4, sort_keys=True))

        return r.json()

    def delete(self):
        """Delete the order

        Returns:
            API response

        """
        if (not self.order):
            self._fetch()

        # Post delete request
        r = requests.delete(self.server + '/order/' + self.uuid,
                            headers={'X-Auth-Token': self.auth_token},
                            cert=(self.tls_cert, self.tls_key))

        if (r.status_code != requests.codes.ok):
            self._print_errors(r)

        r.raise_for_status()

        # Print the response
        logger.info("Order deleted successfully")

        logger.debug("API Response:")
        logger.debug(json.dumps(r.json(), indent=4, sort_keys=True))

        return r.json()
