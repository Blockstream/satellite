#!/usr/bin/env python
"""
Post data to Ionosphere API for transmission via Blockstream Satellite
"""

import os, sys, argparse, textwrap, struct, zlib, requests, json, logging
import gnupg


# Example user-specific message header
USER_HEADER_FORMAT = '255sxi'


def main():
    parser = argparse.ArgumentParser(
        description=textwrap.dedent('''\
        Example data sender application

        Sends a file to the Ionosphere API for transmission via Blockstream
        Satellite. By default, encapsulates the file into a user-specific
        message structure containing the data checksum and the file name,
        encrypts the entire structure using GnuPG and posts to the API.

        Supports commands to bump and delete an order that was sent previously.

        '''),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-f', '--file', help='File to send through API')
    parser.add_argument('-g', '--gnupghome', default=".gnupg",
                        help='GnuPG home directory (default: .gnupg)')
    parser.add_argument('-p', '--port',
                        default=None,
                        help='Ionosphere API server port (default: None)')
    parser.add_argument('-s', '--server',
                        default='https://satellite.blockstream.com',
                        help='Ionosphere API server address (default: ' +
                        'https://satellite.blockstream.com)')
    parser.add_argument('--send-raw', default=False,
                        action="store_true",
                        help='Send file directly, without any user-specific ' +
                        'data structure (default: false)')
    parser.add_argument('--debug', action='store_true',
                        help='Debug mode (default: false)')
    args        = parser.parse_args()
    filename    = args.file
    gnupghome   = args.gnupghome
    port        = args.port
    server      = args.server
    send_raw    = args.send_raw

    # Switch debug level
    if (args.debug):
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
        logging.debug('[Debug Mode]')

    # Process the server address
    server_addr = server

    if (port is not None):
        server_addr = server + ":" + port

    if (server_addr == 'https://satellite.blockstream.com'):
        server_addr += '/api'

    # GPG object
    gpg = gnupg.GPG(gnupghome = gnupghome)

    # Import public GPG keys
    public_keys = gpg.list_keys()

    # Use the first public key in case there are multiple
    public_key = public_keys[0]

    # Read the file, append header, encrypt and transmit to the Ionosphere API
    with open(filename, 'rb') as f:
        data  = f.read()

        print("File has %d bytes" %(len(data)))

        # Pack data into data structure (header + data), if enabled
        if (not send_raw):
            # The header contains a CRC32 checksum of the data as well as a
            # string with the file name.
            header     = struct.pack(USER_HEADER_FORMAT,
                                     os.path.basename(filename),
                                     zlib.crc32(data))
            plain_data = header + data

            print("Packed in data structure with a total of %d bytes" %(
                len(plain_data)))
        else:
            plain_data = data

        # Encrypt
        recipient   = public_key["fingerprint"]
        cipher_data = str(gpg.encrypt(plain_data, recipient))

        # Final transmit data
        tx_data     = cipher_data
        tx_len      = len(cipher_data)

        print("Encrypted version of the data structure has %d bytes" %(
            tx_len))

        # Ask user for bid
        min_bid = tx_len * 50

        bid     = raw_input("Your bid to transmit %d bytes " %(tx_len) +
                            "(in millisatoshis): [%d] " %(min_bid)) \
                            or min_bid
        bid     = int(bid)

        print("Post data with bid of %d millisatoshis (%.2f msat/byte)" %(
            bid, float(bid)/tx_len))

        # Post request to the API
        r = requests.post(server_addr + '/order',
                          data={'bid': bid},
                          files={'file': tx_data})

        # In case of failure, check the API error message
        if (r.status_code != requests.codes.ok):
            if "errors" in r.json():
                for error in r.json()["errors"]:
                    print("ERROR: " + error)

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
