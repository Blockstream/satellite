import logging, json, requests, textwrap
from . import bidding, pkt


logger = logging.getLogger(__name__)


class ApiOrder:
    """API Transmission Order

    Handles the payment/bidding for transmission of API messages.

    Args:
        server  : API server address where the order lives
        seq_num : Sequence number corresponding to this API message

    """
    def __init__(self, server, seq_num=None):
        # Get order UUID and Authorization Token from user input
        self.uuid       = None
        self.auth_token = None

        # API server address
        self.server = server

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

    def _fetch(self, uuid, auth_token):
        """Fetch a specific order from the server"""
        r = requests.get(self.server + '/order/' + uuid,
                         headers = {
                             'X-Auth-Token': auth_token
                         })

        if (r.status_code != requests.codes.ok):
            self._print_errors(r)

        r.raise_for_status()

        self.uuid       = uuid
        self.auth_token = auth_token
        self.order      = r.json()
        logger.debug(json.dumps(r.json(), indent=4, sort_keys=True))

    def send(self, data, bid):
        """Send the transmission order

        Args:
            data : Data as bytes array to broadcast over satellite
            bid  : Bid in msats

        Returns:
            Dictionary with order metadata

        """
        assert(isinstance(data, bytes))

        # Post request to the API
        r = requests.post(self.server + '/order',
                          data={'bid': bid},
                          files={'file': data})

        # In case of failure, check the API error message
        if (r.status_code != requests.codes.ok and
            r.headers['content-type'] == "application/json"):
            self._print_errors(r)

        # Raise error if response status indicates failure
        r.raise_for_status()

        # Print the response
        logger.info("Data successfully queued for transmission\n")

        print("--\nAuthentication Token:\n%s" %(r.json()["auth_token"]))
        print("--\nUUID:\n%s" %(r.json()["uuid"]))
        print("--\nLightning Invoice Number:\n%s" %(
            r.json()["lightning_invoice"]["payreq"]))
        print("--\nAmount Due:\n%s millisatoshis\n" %(
            r.json()["lightning_invoice"]["msatoshi"]))

        logger.debug("API Response:")
        logger.debug(json.dumps(r.json(), indent=4, sort_keys=True))

        return r.json()

    def get_data(self):
        """Get data content sent over an API order"""
        logger.debug("Fetch message #%s from API" %(self.seq_num))

        r = requests.get(self.server + '/message/' + str(self.seq_num))

        r.raise_for_status()

        if (r.status_code == requests.codes.ok):
            data        = r.content
            return data

    def confirm_tx(self, regions, tls_cert=None, tls_key=None):
        """Confirm transmission of an API message

        Args:
            regions     : Regions that were covered by the transmission
            tls_key     : API client key
            tls_cert    : API client certificate

        """
        assert(self.seq_num is not None)

        if (regions is None) or (tls_cert is None) or (tls_key is None):
            return

        assert(isinstance(regions, list))

        logger.info("Confirm transmission of message {} on regions {}".format(
            self.seq_num, regions))

        r = requests.post(self.server + '/order/tx/' + str(self.seq_num),
                          data = {
                              'regions': json.dumps(regions)
                          },
                          cert = (tls_cert, tls_key))

        if not r.ok:
            logger.error("Failed to confirm Tx of message {} "
                         "[status code {}]".format(self.seq_num, r.status_code))
            self._print_errors(r)
        else:
            logger.info("Server response: " + r.json()['message'])

    def confirm_rx(self, region, tls_cert=None, tls_key=None):
        """Confirm reception of an API message

        Args:
            region     : Coverage region
            tls_key    : API client key
            tls_cert   : API client certificate

        """
        assert(self.seq_num is not None)

        if (region is None) or (tls_cert is None) or (tls_key is None):
            return

        logger.info("Confirm reception of API message {} on region {}".format(
            self.seq_num, region))

        r = requests.post(self.server + '/order/rx/' + str(self.seq_num),
                          data = {
                              'region' : region
                          },
                          cert = (tls_cert, tls_key))

        if not r.ok:
            logger.error("Failed to confirm Rx of message {} "
                         "[status code {}]" %(self.seq_num, r.status_code))
            self._print_errors(r)
        else:
            logger.info("Server response: " + r.json()['message'])

    def bump(self, bid=None, uuid=None, auth_token=None):
        """Bump the order

        Args:
            bid        : New bid in msats. If not defined, prompt user.
            uuid       : Order UUID. If not defined, prompt user.
            auth_token : Authentication token. If not defined, prompt user.

        Returns:
            Dictionary with order metadata

        """

        if (uuid is None or auth_token is None):
            uuid, auth_token = self._prompt_for_uuid_token()

        # Fetch the order to be bumped
        self._fetch(uuid, auth_token)

        if (self.order["status"] == "transmitting"):
            raise ValueError("Cannot bump order - already in transmission")

        if (self.order["status"] == "sent" or
            self.order["status"] == "received"):
            raise ValueError("Cannot bump order - already transmitted")

        if (self.order["status"] == "cancelled"):
            raise ValueError("Order already cancelled")

        if (self.order["unpaid_bid"] > 0):
            unpaid_bid_msg = "(%d msat paid, %d msat unpaid)" %(
                self.order["bid"], self.order["unpaid_bid"])
        else:
            unpaid_bid_msg = ""

        previous_bid = self.order["bid"] + self.order["unpaid_bid"]
        tx_len       = pkt.calc_ota_msg_len(self.order["message_size"])

        logger.info("Previous bid was %s msat for %s bytes %s" %(
            previous_bid, tx_len,
            unpaid_bid_msg))

        logger.info("Paid bid ratio is currently %s msat/byte" %(
            self.order["bid_per_byte"]))
        logger.info("Total (paid + unpaid) bid ratio is currently %s msat/byte" %(
            float(previous_bid) / tx_len))

        if (bid is None):
            # Ask for new bid
            bid = bidding.ask_bid(tx_len, previous_bid)

        assert(isinstance(bid, int))

        # Post bump request
        r = requests.post(self.server + '/order/' + self.uuid + "/bump",
                          data={
                              'bid_increase': bid - previous_bid,
                              'auth_token': self.auth_token
                          })

        if (r.status_code != requests.codes.ok):
            self._print_errors(r)

        r.raise_for_status()

        # Print the response
        logger.info("Order bumped successfully\n")

        print("--\nNew Lightning Invoice Number:\n%s\n" %(
            r.json()["lightning_invoice"]["payreq"]))
        print("--\nNew Amount Due:\n%s millisatoshis\n" %(
            r.json()["lightning_invoice"]["msatoshi"]))

        logger.debug("API Response:")
        logger.debug(json.dumps(r.json(), indent=4, sort_keys=True))

        return r.json()

    def delete(self, uuid=None, auth_token=None):
        """Delete the order

        Args:
            uuid       : Order UUID. If not defined, prompt user.
            auth_token : Authentication token. If not defined, prompt user.

        Returns:
            API response

        """

        if (uuid is None or auth_token is None):
            uuid, auth_token = self._prompt_for_uuid_token()

        # Fetch the order to be bumped
        self._fetch(uuid, auth_token)

        # Post delete request
        r = requests.delete(self.server + '/order/' + self.uuid,
                            headers = {
                             'X-Auth-Token': self.auth_token
                            })

        if (r.status_code != requests.codes.ok):
            self._print_errors(r)

        r.raise_for_status()

        # Print the response
        logger.info("Order deleted successfully")

        logger.debug("API Response:")
        logger.debug(json.dumps(r.json(), indent=4, sort_keys=True))

        return r.json()
