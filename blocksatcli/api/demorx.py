#!/usr/bin/env python3
"""
Read API data directly via internet and output to pipe
"""

import json
import logging
import time

import requests

from .. import defs
from . import net
from .order import ApiOrder, API_CHANNEL_SSE_NAME
from .pkt import BlocksatPkt, BlocksatPktHandler

logger = logging.getLogger(__name__)
MAX_SEQ_NUM = 2**31  # Maximum transmission sequence number


class DemoRx():
    """Demo receiver
    """

    def __init__(self,
                 server,
                 socks,
                 kbps,
                 tx_event,
                 channel,
                 regions=None,
                 tls_cert=None,
                 tls_key=None,
                 poll=False,
                 sock_by_region=False):
        """ DemoRx Constructor

        Args:
            server   : API server address where the order lives.
            socks    : Instances of UdpSock over which to send the packets
            kbps     : Target bit rate in kbps.
            tx_event : SSE event to use as trigger for transmissions.
            channel  : API channel number.
            regions  : Regions to process and potentially confirm Tx.
            tls_key  : API client key (for Tx confirmation).
            tls_cer  : API client certificate (for Tx confirmation).
            poll     : Poll messages directly from the Satellite API queue
                instead of listening to server-sent events.
            sock_by_region : Map each UdpSock to a region so that each socket
                serves messages on a single region only. Requires the socks
                parameter to have the same length as the regions parameter.


        """
        # Validate args
        assert (isinstance(socks, list))
        assert (all([isinstance(x, net.UdpSock) for x in socks]))

        # Configs
        self.server = server
        self.socks = socks
        self.kbps = kbps
        self.tx_event = tx_event
        self.channel = channel
        self.regions_list = defs.satellite_regions if not regions else regions
        self.regions_set = set(self.regions_list)
        self.tls_cert = tls_cert
        self.tls_key = tls_key
        self.poll = poll
        self.admin = tls_cert is not None and tls_key is not None

        if sock_by_region and len(self.regions_list) != len(socks):
            raise ValueError(
                "Number of sockets must be equal to the number of regions")
        self.sock_by_region = sock_by_region

    def _send_pkts(self, pkts, socks):
        """Transmit Blocksat packets of the API message over all sockets

        Transmit and sleep (i.e., block) to guarantee the target bit rate.

        Args:
            pkts : List of BlocksatPkt objects to be send over sockets
            socks : List of sockets over which to send packets.

        """
        assert (isinstance(pkts, list))
        assert (all([isinstance(x, BlocksatPkt) for x in pkts]))

        byte_rate = self.kbps * 1e3 / 8  # bytes / sec
        next_tx = time.time()
        for i, pkt in enumerate(pkts):
            # Send the same packet on all sockets
            for sock in socks:
                sock.send(pkt.pack())
                logger.debug("Send packet %d - %d bytes" % (i, len(pkt)))

            # Throttle
            if (byte_rate > 0):
                tx_delay = len(pkt) / byte_rate
                next_tx += tx_delay
                sleep = next_tx - time.time()
                if (sleep > 0):
                    time.sleep(sleep)

    def _handle_event(self, event_data):
        """Handle event broadcast by the SSE server

        Args:
            event_data (dict): Event data.

        """
        order = json.loads(event_data)
        logger.debug("Order: " + json.dumps(order, indent=4, sort_keys=True))

        # Proceed when the event matches the target Tx trigger event
        if (order["status"] != self.tx_event):
            return

        self._handle_order(order)

    def _handle_order(self, order_info):
        """Fetch the order data and send it over UDP

        Args:
            order_info (dict): Dictionary with the order's Tx sequence number
                and message size.

        """

        # The 'regions' field of the order info has different contents in
        # polling and SSE mode. In SSE mode, it contains the missing regions
        # for transmission, whereas, in polling mode (reading from
        # /order/:uuid), it contains all the original regions, regardless of
        # whether or not the transmission is pending. Nevertheless, when
        # operating in polling mode as admin (fetching from
        # /admin/order/:uuid), the order info includes the "tx_confirmations"
        # field, which can be used to adjust the regions field such that it
        # contains the missing regions only.
        order_regions = set(order_info['regions'])
        if 'tx_confirmations' in order_info:
            confirmed_tx_regions = set(order_info['tx_confirmations'])
            order_regions = order_regions - confirmed_tx_regions

        # Ensure the order includes a region covered by this instance
        served_regions = order_regions & self.regions_set
        if (served_regions == set()):
            logger.debug("Demo-Rx region(s) not covered by this order")
            return

        seq_num = order_info["tx_seq_num"]
        logger.info("Message %-5d\tSize: %d bytes\t" %
                    (seq_num, order_info["message_size"]))

        # Get the API message data
        order = ApiOrder(self.server,
                         seq_num=seq_num,
                         tls_cert=self.tls_cert,
                         tls_key=self.tls_key)
        data = order.get_data()

        if (data is None):
            logger.debug("Empty message. Skipping...")
            return

        # Define the sockets over which the order should be transmitted
        tx_socks = []
        if self.sock_by_region:
            for region, sock in zip(self.regions_list, self.socks):
                if region in order_regions:
                    tx_socks.append(sock)
        else:
            tx_socks = self.socks

        # Split API message data into Blocksat packet(s)
        tx_handler = BlocksatPktHandler()
        tx_handler.split(data, seq_num, self.channel)
        pkts = tx_handler.get_frags(seq_num)

        if (self.kbps > 0):
            logger.debug("Transmission is going to take: "
                         "{:g} sec".format(len(data) * 8 / (self.kbps * 1e3)))

        # Send the packet(s)
        self._send_pkts(pkts, tx_socks)

        # Send transmission confirmation to the server
        order.confirm_tx(list(served_regions))

    def run_sse_client(self):
        """Server-sent Events (SSE) Client"""
        logger.info("Connecting with Satellite API server...")
        sleep = False
        while (True):
            try:
                if sleep:
                    time.sleep(2)
                    sleep = False

                sse_channel = API_CHANNEL_SSE_NAME[self.channel]
                endpoint = '/admin/subscribe/' if self.admin else '/subscribe/'
                r = requests.get(self.server + f"{endpoint}{sse_channel}",
                                 stream=True,
                                 cert=(self.tls_cert, self.tls_key))
                r.raise_for_status()

                logger.info("Connected. Waiting for events...\n")

                # Continuously wait for events
                event_line = 'event:' + sse_channel
                event_next = False
                for line in r.iter_lines():
                    if not line:
                        continue

                    dec_line = line.decode()

                    if dec_line.startswith(':'):  # comment to be ignored
                        continue

                    logger.debug(line)

                    if dec_line.startswith(event_line):
                        event_next = True
                        continue

                    if event_next and dec_line.startswith('data:'):
                        self._handle_event(dec_line.replace('data:', ''))
                        event_next = False

            except requests.exceptions.HTTPError as e:
                logger.error(e)
                break

            except requests.exceptions.ChunkedEncodingError as e:
                logger.debug(e)
                pass

            except requests.exceptions.ConnectionError as e:
                logger.debug(e)
                sleep = True
                pass

            except requests.exceptions.RequestException as e:
                logger.debug(e)
                sleep = True
                pass

            except KeyboardInterrupt:
                exit()

            logger.info("Reconnecting...")

    def run_poll_client(self):
        """Polling-based client"""
        order_mgr = ApiOrder(self.server,
                             tls_cert=self.tls_cert,
                             tls_key=self.tls_key)
        tx_set = set()
        while (True):
            try:
                tx_orders = order_mgr.get_orders(['transmitting'],
                                                 self.channel,
                                                 queue='transmitting')

                # There can only be one order in transmitting state at a time
                if len(tx_orders) > 1:
                    logger.warning("More than one order in transmitting "
                                   "state on channel {}".format(self.channel))

                # Filter out any repeated orders (already transmitted), except
                # for those the server is explicitly retransmitting.
                new_orders = list()
                for order_info in tx_orders:
                    is_retransmission = 'retransmission' in order_info and \
                        order_info['retransmission'] is not None and \
                        'retry_count' in order_info['retransmission']
                    tx_attempt = 0 if not is_retransmission else \
                        order_info['retransmission']['retry_count']
                    order_id = "{}-{}".format(order_info['tx_seq_num'],
                                              tx_attempt)
                    if order_id not in tx_set:
                        tx_set.add(order_id)
                        new_orders.append(order_info)

                if new_orders:
                    for order_info in new_orders:
                        logger.debug(
                            "Order: " +
                            json.dumps(order_info, indent=4, sort_keys=True))
                        self._handle_order(order_info)
                else:
                    time.sleep(1)

            except requests.exceptions.ConnectionError as e:
                logger.debug(e)
                time.sleep(1)
                pass
            except KeyboardInterrupt:
                exit()

    def run(self):
        """Run the demo-rx transmission loop"""
        if self.poll:
            self.run_poll_client()
        else:
            self.run_sse_client()
