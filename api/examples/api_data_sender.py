#!/usr/bin/env python2
"""
Post data to the Satellite API for transmission via Blockstream Satellite
"""

import os, sys, argparse, textwrap, struct, zlib, requests, json, logging, time
import gnupg, getpass
from math import ceil


# Example user-specific message header
USER_HEADER_FORMAT = '255sxi'

class Order:
    """API Transmission Order

    Args:
        server: API server address where the order lives

    """
    def __init__(self, server):
        # Get order UUID and Authorization Token from user input
        uuid = raw_input("UUID: ") or None
        if (uuid is None):
            raise ValueError("Order UUID is required")

        auth_token = raw_input("Authentication Token: ") or None
        if (auth_token is None):
            raise ValueError("Authentication Token is required")

        self.uuid       = uuid
        self.auth_token = auth_token
        self.server     = server

        # Check the order in the server
        r = requests.get(server + '/order/' + uuid,
                         headers = {
                             'X-Auth-Token': auth_token
                         })

        if (r.status_code != requests.codes.ok):
            if "errors" in r.json():
                for error in r.json()["errors"]:
                    print("ERROR: " + error["title"] + "\n" + error["detail"])

        r.raise_for_status()

        self.order = r.json()
        logging.debug(json.dumps(r.json(), indent=4, sort_keys=True))

    def bump(self):
        """Bump the order
        """
        if (self.order["status"] == "transmitting"):
            raise ValueError("Cannot bump - order is already in transmission")

        if (self.order["status"] == "sent"):
            raise ValueError("Cannot bump - order was already transmitted")

        if (self.order["unpaid_bid"] > 0):
            unpaid_bid_msg = "(%d msat paid, %d msat unpaid)" %(
                self.order["bid"], self.order["unpaid_bid"])
        else:
            unpaid_bid_msg = ""

        previous_bid = self.order["bid"] + self.order["unpaid_bid"]
        tx_len       = calc_tx_len(self.order["message_size"])

        print("Previous bid was %s msat for %s bytes %s" %(
            previous_bid, tx_len,
            unpaid_bid_msg))

        print("Paid bid ratio is currently %s msat/byte" %(
            self.order["bid_per_byte"]))
        print("Total (paid + unpaid) bid ratio is currently %s msat/byte" %(
            float(previous_bid) / tx_len))

        # Ask for new bid
        bid = ask_bid(tx_len, previous_bid)

        # Post bump request
        r = requests.post(self.server + '/order/' + self.uuid + "/bump",
                          data={
                              'bid_increase': bid - previous_bid,
                              'auth_token': self.auth_token
                          })

        if (r.status_code != requests.codes.ok):
            if "errors" in r.json():
                for error in r.json()["errors"]:
                    print("ERROR: " + error["title"] + "\n" + error["detail"])

        r.raise_for_status()

        # Print the response
        print("Order bumped successfully")
        print("--\nNew Lightning Invoice Number:\n%s\n" %(
            r.json()["lightning_invoice"]["payreq"]))
        print("--\nNew Amount Due:\n%s millisatoshis\n" %(
            r.json()["lightning_invoice"]["msatoshi"]))

        logging.debug("API Response:")
        logging.debug(json.dumps(r.json(), indent=4, sort_keys=True))

    def delete(self):
        """Delete the order
        """

        # Post delete request
        r = requests.delete(self.server + '/order/' + self.uuid,
                            headers = {
                             'X-Auth-Token': self.auth_token
                            })

        if (r.status_code != requests.codes.ok):
            if "errors" in r.json():
                for error in r.json()["errors"]:
                    print("ERROR: " + error["title"] + "\n" + error["detail"])

        r.raise_for_status()

        # Print the response
        print("Order deleted successfully")

        logging.debug("API Response:")
        logging.debug(json.dumps(r.json(), indent=4, sort_keys=True))


def calc_tx_len(msg_len):
    """Compute the number of bytes actually transmitted for a message

    The message is carried in the payload of Blocksat packets. Each packet can
    fits up to 2048 bytes and adds 16 bytes of overhead.

    Args:
        msg_len : Length of the user message to be transmitted

    """

    return msg_len + int(16 * ceil(float(msg_len) / 2048))


def ask_bid(data_size, prev_bid=None):
    """Ask for user bid

    Args:
        data_size : Size of the transmit data in bytes
        prev_bid  : Previous bid, if any

    """

    if (prev_bid is not None):
        # Suggest a 5% higher msat/byte ratio
        prev_ratio      = float(prev_bid) / data_size
        suggested_ratio = 1.05 * prev_ratio
        min_bid         = data_size * suggested_ratio
    else:
        min_bid = data_size * 50

    bid     = raw_input("Your " +
                        ("new total " if prev_bid is not None else "") +
                        "bid to transmit %d bytes " %(data_size) +
                        "(in millisatoshis): [%d] " %(min_bid)) \
                        or min_bid
    bid     = int(bid)

    if (prev_bid is not None):
        print("Bump bid by %d msat to a total of %d msat (%.2f msat/byte)" %(
            bid - prev_bid, bid, float(bid) / data_size))
    else:
        print("Post data with bid of %d millisatoshis (%.2f msat/byte)" %(
            bid, float(bid) / data_size))

    return bid


def main():
    parser = argparse.ArgumentParser(
        description=textwrap.dedent('''\
        Example data sender application

        Sends a file to the Satellite API for transmission via Blockstream
        Satellite. By default, encapsulates the file into a user-specific
        message structure containing the data checksum and the file name,
        encrypts the entire structure using GnuPG and posts to the API.

        Supports commands to bump and delete an order that was sent previously.

        '''),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-f', '--file', help='File to send through API')
    group.add_argument('-m', '--message', help='Text message to send through API')
    parser.add_argument('-g', '--gnupghome', default=".gnupg",
                        help='GnuPG home directory (default: .gnupg)')
    parser.add_argument('-p', '--port',
                        default=None,
                        help='Satellite API server port (default: None)')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--net', choices=['main', 'test'],
                       default=None,
                       help='Choose Mainnet (main) or Testnet (test) ' +
                       'Satellite API (default: main)')
    group.add_argument('-s', '--server',
                       default='https://api.blockstream.space',
                       help='Satellite API server address (default: ' +
                       'https://api.blockstream.space)')
    parser.add_argument('-r', '--recipient', default=None,
                        help='Public key fingerprint of the desired ' + \
                        'recipient. If not defined, the recipient will ' + \
                        'be automatically set to the host corresponding to ' + \
                        'the first public key in the keyring. (default: None)')
    parser.add_argument('--trust', default=False, action="store_true",
                        help='Assume that recipient public key is fully ' +\
                        ' trusted (default: False)')
    parser.add_argument('--sign', default=False, action="store_true",
                        help='Sign message in addition to encrypting ' +\
                        ' (default: False)')
    parser.add_argument('--sign-key', default=None,
                        help='Fingerprint of key to use when signing the ' +\
                        'encrypted data. If not set, default key from ' + \
                        'keyring will be used for signing. (default: False)')
    parser.add_argument('--send-raw', default=False,
                        action="store_true",
                        help='Send file directly, without any user-specific ' +
                        'data structure (default: false)')
    parser.add_argument('--plaintext', default=False,
                        action="store_true",
                        help='Send as plaintext, i.e. without encryption ' +
                        '(default: false)')
    parser.add_argument('--password', default=False,
                        action="store_true",
                        help='Whether to access GPG keyring with a password ' +
                        '(default: false)')
    parser.add_argument('--debug', action='store_true',
                        help='Debug mode (default: false)')
    # Optional actions
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-b', '--bump', action='store_true',
                       help='Bump the bid of an order (default: false)')
    group.add_argument('-d', '--delete', action='store_true',
                       help='Delete an order (default: false)')
    args        = parser.parse_args()
    filename    = args.file
    text_msg    = args.message
    gnupghome   = args.gnupghome
    port        = args.port
    server      = args.server
    net         = args.net
    send_raw    = args.send_raw
    plaintext   = args.plaintext

    # Switch debug level
    if (args.debug):
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
        logging.debug('[Debug Mode]')

    if (net is not None and net == "main"):
        server = "https://api.blockstream.space"
    elif (net is not None and net == "test"):
        server = "https://api.blockstream.space/testnet"

    # Process the server address
    server_addr = server

    if (port is not None):
        server_addr = server + ":" + port

    # Check if bump or delete
    if (args.bump or args.delete):
        order = Order(server_addr)

    if (args.bump):
        if (order.order["status"] == "cancelled"):
            raise ValueError("Order already cancelled")
        order.bump()
        exit()

    if (args.delete):
        order.delete()
        exit()

    # GPG object
    gpg = gnupg.GPG(gnupghome = gnupghome)

    # Is there a password for GPG keyring?
    if (args.password):
        gpg_password = getpass.getpass()
    else:
        gpg_password = None

    # Read the file, append header, encrypt and transmit to the Satellite API
    if (text_msg is not None):
        data     = text_msg.encode('utf-8')
        basename = time.strftime("%Y%m%d%H%M%S")
    else:
        basename = os.path.basename(filename)

        with open(filename, 'rb') as f:
            data  = f.read()
        assert(len(data) > 0)

    print("File has %d bytes" %(len(data)))

    # Pack data into data structure (header + data), if enabled
    if (send_raw):
        plain_data = data
    else:
        # The header contains a CRC32 checksum of the data as well as a
        # string with the file name.
        header     = struct.pack(USER_HEADER_FORMAT,
                                 basename,
                                 zlib.crc32(data))
        plain_data = header + data

        print("Packed in data structure with a total of %d bytes" %(
            len(plain_data)))

    # Encrypt, unless configured otherwise
    if (plaintext):
        msg_data     = plain_data
        msg_len      = len(plain_data)
    else:
        # Recipient public key
        if (args.recipient is None):
            # Use the first public key from keyring if recipient is not defined
            public_keys = gpg.list_keys()
            public_key  = public_keys[0]
            recipient   = public_key["fingerprint"]
            print("Encrypt for recipient %s" %(recipient))
        else:
            recipient   = args.recipient
            print("Encrypt for chosen recipient %s" %(recipient))

        # Digital signature, if desired
        if (args.sign and args.sign_key is not None):
            sign_cfg = args.sign_key
            print("Sign message using key %s" %(args.sign_key))
        elif (args.sign and args.sign_key is None):
            sign_cfg = True
            print("Sign message using default key")
        else:
            sign_cfg = False

        # Encrypt
        encrypted_obj = gpg.encrypt(plain_data, recipient,
                                    always_trust = args.trust,
                                    sign = sign_cfg,
                                    passphrase = gpg_password)
        if (not encrypted_obj.ok):
            print(encrypted_obj.stderr)
            raise ValueError(encrypted_obj.status)

        cipher_data   = str(encrypted_obj)
        print("Encrypted version of the data structure has %d bytes" %(
            len(cipher_data)))

        # Final message sent to API for transmission
        msg_data     = cipher_data
        msg_len      = len(cipher_data)

    # Actual number of bytes used for satellite transmission
    tx_len = calc_tx_len(msg_len)

    print("Satellite transmission will use %d bytes" %(tx_len))

    # Ask user for bid
    bid = ask_bid(tx_len)

    # Post request to the API
    r = requests.post(server_addr + '/order',
                      data={'bid': bid},
                      files={'file': msg_data})

    # In case of failure, check the API error message
    if (r.status_code != requests.codes.ok and
        r.headers['content-type'] == "application/json"):
        if "errors" in r.json():
            for error in r.json()["errors"]:
                print("ERROR: " + error["title"] + "\n" + error["detail"])

    # Raise error if response status indicates failure
    r.raise_for_status()

    # Print the response
    print("Data successfully transmitted")
    print("--\nAuthentication Token:\n%s" %(r.json()["auth_token"]))
    print("--\nUUID:\n%s" %(r.json()["uuid"]))
    print("--\nLightning Invoice Number:\n%s" %(
        r.json()["lightning_invoice"]["payreq"]))
    print("--\nAmount Due:\n%s millisatoshis\n" %(
        r.json()["lightning_invoice"]["msatoshi"]))

    logging.debug("API Response:")
    logging.debug(json.dumps(r.json(), indent=4, sort_keys=True))


if __name__ == '__main__':
    main()
