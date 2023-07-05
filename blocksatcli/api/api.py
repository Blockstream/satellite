"""Blocksat API"""
import json
import logging
import os
import shlex
import subprocess
import textwrap
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from shutil import which

import qrcode

from . import bidding, net
from . import msg as api_msg
from .. import config as blocksatcli_config
from .. import defs
from .demorx import DemoRx
from .gpg import Gpg, config_keyring
from .listen import ApiListener
from .order import ApiOrder, ApiChannel, \
    API_CHANNELS,\
    SENDABLE_API_CHANNELS,\
    PAID_API_CHANNELS,\
    ORDER_STATUS,\
    ORDER_QUEUES
from .pkt import calc_ota_msg_len

logger = logging.getLogger(__name__)
server_map = {
    'main': "https://api.blockstream.space",
    'test': "https://api.blockstream.space/testnet"
}


def _get_server_addr(net, server):
    if (net is None):
        return server
    else:
        return server_map[net]


def config(args):
    """API config command"""
    gnupghome = os.path.join(args.cfg_dir, args.gnupghome)
    gpg = Gpg(gnupghome, verbose=args.verbose, interactive=True)
    config_keyring(gpg, log_if_configured=True)


def send(args):
    """Send a message over satellite"""
    gnupghome = os.path.join(args.cfg_dir, args.gnupghome)
    server_addr = _get_server_addr(args.net, args.server)

    # Instantiate the GPG wrapper object if running with encryption or signing
    if (not args.plaintext or args.sign):
        gpg = Gpg(gnupghome, interactive=True)
        config_keyring(gpg)
    else:
        gpg = None

    # A passphrase is required if signing
    if (args.sign and (not args.no_password)):
        gpg.prompt_passphrase('Password to private key used for message '
                              'signing: ')

    # File or text message to send over satellite
    if (args.file is None):
        if (args.message is None):
            data = input("Type a message: ").encode()
            print()
        else:
            data = args.message.encode()
        basename = None
    else:
        basename = os.path.basename(args.file)
        with open(args.file, 'rb') as f:
            data = f.read()

    assert (len(data) > 0), \
        "Empty {}".format("file" if args.file else "message")

    # Put file or text within an API message
    msg = api_msg.generate(data,
                           filename=basename,
                           plaintext=args.plaintext,
                           encapsulate=(not args.send_raw),
                           sign=args.sign,
                           fec=args.fec,
                           gpg=gpg,
                           recipient=args.recipient,
                           trust=args.trust,
                           sign_key=args.sign_key,
                           fec_overhead=args.fec_overhead)

    # Actual number of bytes used for satellite transmission
    tx_len = calc_ota_msg_len(msg.get_length())
    logger.info("Satellite transmission will use %d bytes" % (tx_len))

    # Ask user for bid or take it from argument
    if (args.channel in PAID_API_CHANNELS):
        bid = args.bid if args.bid else bidding.ask_bid(tx_len)
    else:
        bid = None

    # API transmission order
    order = ApiOrder(server_addr, tls_cert=args.tls_cert, tls_key=args.tls_key)
    res = order.send(msg.get_data(), bid, args.regions, args.channel)
    print()

    # Only the paid API channels return a Lightning invoice for the
    # transmission order
    if (args.channel in PAID_API_CHANNELS):
        payreq = res["lightning_invoice"]["payreq"]

        # Print QR code
        try:
            qr = qrcode.QRCode()
            qr.add_data(payreq)
            qr.print_ascii()
        except UnicodeError:
            qr.print_tty()

        # Execute arbitrary command with the Lightning invoice
        if (args.invoice_exec):
            cmd = shlex.split(args.invoice_exec.replace("{}", payreq))
            logger.debug("Execute:\n> {}".format(" ".join(cmd)))
            subprocess.run(cmd)

    # Wait until the transmission completes (after the ground station confirms
    # reception). Stop if it is canceled.
    if (args.no_wait):
        return

    try:
        target_state = ['sent', 'cancelled']
        order.wait_state(target_state)
    except KeyboardInterrupt:
        pass


def listen(args):
    """Listen to API messages received over satellite"""
    gnupghome = os.path.join(args.cfg_dir, args.gnupghome)

    if (args.save_dir is not None):
        if (not os.path.exists(args.save_dir)):
            logger.error("Directory {} does not exist".format(args.save_dir))
            return
        download_dir = args.save_dir
    else:
        download_dir = os.path.join(args.cfg_dir, "api", "downloads")

    # Override some options based on the mutual exclusive --gossip and
    # --btc-src arguments, if present
    if (args.gossip):
        channel = ApiChannel.GOSSIP.value
        args.plaintext = True
    elif (args.btc_src):
        channel = ApiChannel.BTC_SRC.value
        args.plaintext = True
    else:
        channel = args.channel

    if (args.gossip or args.btc_src):
        if (args.channel != ApiChannel.USER.value):
            logger.warning("Option {} overrides --channel".format(
                "--gossip" if args.gossip else "--btc-src"))

    server_addr = _get_server_addr(args.net, args.server)
    historian_cli = os.path.join(args.historian_path, 'historian-cli') \
        if (args.historian_path) else 'historian-cli'

    # Argument validation and special cases
    if (args.gossip):
        if (which(historian_cli) is None):
            logger.error("Option --gossip requires the historian-cli "
                         "application but could not find it")
            logger.info("Use option --historian-path to specify the path to "
                        "historian-cli")
            raise ValueError("Could not find the historian-cli application")

        if (args.stdout):
            raise ValueError("Argument --gossip is not allowed with argument "
                             "--stdout")
        elif (args.no_save):
            raise ValueError("Argument --gossip is not allowed with argument "
                             "--no-save")

        gossip_opts = {
            'cli': historian_cli,
            'dest': args.historian_destination
        }
    else:
        gossip_opts = None

    if (args.exec):
        # Do not support the option in plaintext mode
        if (args.plaintext):
            raise ValueError("Option --exec is not allowed in plaintext mode")

        # Require either --sender or --insecure
        if (args.sender is None and not args.insecure):
            raise ValueError("Option --exec requires a specified --sender")

        # Warn about unsafe commands
        base_exec_cmd = shlex.split(args.exec)[0]
        unsafe_cmds = ["/bin/bash", "bash", "/bin/sh", "sh", "rm"]
        if (base_exec_cmd in unsafe_cmds):
            logger.warning("Running {} on --exec is considered unsafe".format(
                base_exec_cmd))

    # GPG wrapper object
    if (not args.plaintext or args.sender):
        gpg = Gpg(gnupghome, interactive=True)
        config_keyring(gpg)
    else:
        gpg = None

    # Define the interface used to listen for messages
    if (args.interface):
        interface = args.interface
    elif (args.demo):
        interface = "lo"
    else:
        # Infer the interface based on the user's setup
        user_info = blocksatcli_config.read_cfg_file(args.cfg, args.cfg_dir)
        interface = blocksatcli_config.get_net_if(user_info)
    logger.info("Listening on interface: {}".format(interface))

    if not args.no_save:
        logger.info("Downloads will be saved at: {}".format(download_dir))

    # A passphrase is required for decryption (but not for signature
    # verification)
    if (not args.plaintext and not args.no_password):
        gpg.prompt_passphrase('GPG keyring password for decryption: ')

    # Listen continuously
    listen_loop = ApiListener()
    listen_loop.run(gpg,
                    download_dir,
                    args.sock_addr,
                    interface,
                    channel,
                    args.plaintext,
                    args.save_raw,
                    sender=args.sender,
                    stdout=args.stdout,
                    no_save=args.no_save,
                    echo=args.echo,
                    exec_cmd=args.exec,
                    gossip_opts=gossip_opts,
                    server_addr=server_addr,
                    tls_cert=args.tls_cert,
                    tls_key=args.tls_key,
                    region=args.region)


def bump(args):
    """Bump the bid of an API order"""
    server_addr = _get_server_addr(args.net, args.server)

    # Fetch the ApiOrder
    order = ApiOrder(server_addr, tls_cert=args.tls_cert, tls_key=args.tls_key)
    order.get(args.uuid, args.auth_token)

    # Bump bid
    try:
        res = order.bump(args.bid)
    except ValueError as e:
        logger.error(e)
        return

    # Print QR code
    qr = qrcode.QRCode()
    qr.add_data(res["lightning_invoice"]["payreq"])
    qr.print_ascii()


def get(args):
    """Get an API order"""
    server_addr = _get_server_addr(args.net, args.server)

    # Fetch the ApiOrder
    order = ApiOrder(server_addr, tls_cert=args.tls_cert, tls_key=args.tls_key)
    order.get(args.uuid, args.auth_token)
    print(json.dumps(order.order, indent=4))


def list_orders(args):
    server_addr = _get_server_addr(args.net, args.server)
    order = ApiOrder(server_addr, tls_cert=args.tls_cert, tls_key=args.tls_key)
    res = order.get_orders(args.status, args.channel, args.queue, args.limit)
    print(json.dumps(res, indent=4))


def delete(args):
    """Cancel an API order"""
    server_addr = _get_server_addr(args.net, args.server)

    # Fetch the ApiOrder
    order = ApiOrder(server_addr, tls_cert=args.tls_cert, tls_key=args.tls_key)
    order.get(args.uuid, args.auth_token)

    # Delete it
    order.delete()


def demo_rx(args):
    """Demo satellite receiver"""
    server_addr = _get_server_addr(args.net, args.server)

    # Open one socket for each interface:
    socks = list()
    for interface in args.interface:
        sock = net.UdpSock(args.dest, interface, mcast_rx=False)
        sock.set_mcast_tx_opts(args.ttl, args.dscp)
        socks.append(sock)

    rx = DemoRx(server_addr,
                socks,
                args.bitrate,
                args.event,
                args.channel,
                args.regions,
                args.tls_cert,
                args.tls_key,
                args.poll,
                sock_by_region=args.if_by_region)
    rx.run()


def subparser(subparsers):  # pragma: no cover
    """Subparser for usb command"""
    p = subparsers.add_parser('api',
                              description="Blockstream Satellite API",
                              help='Blockstream Satellite API',
                              formatter_class=ArgumentDefaultsHelpFormatter)

    # Common API app arguments
    p.add_argument(
        '-g',
        '--gnupghome',
        default=".gnupg",
        help="GnuPG home directory, by default created inside the config "
        "directory specified via --cfg-dir option")
    server_addr = p.add_mutually_exclusive_group()
    server_addr.add_argument(
        '--net',
        choices=server_map.keys(),
        default=None,
        help="Choose between the Mainnet API server (main) or the Testnet API \
        server (test)")
    server_addr.add_argument('-s',
                             '--server',
                             default=server_map['main'],
                             help="Satellite API server address")
    p.add_argument(
        '--tls-cert',
        default=None,
        help="Certificate for client-side authentication with the API server")
    p.add_argument(
        '--tls-key',
        default=None,
        help="Private key for client-side authentication with the API server")
    p.set_defaults(func=print_help)

    subsubparsers = p.add_subparsers(title='subcommands',
                                     help='Target sub-command')

    # Config
    p1 = subsubparsers.add_parser(
        'config',
        aliases=['cfg'],
        description="Configure GPG keys",
        help="Configure GPG keys",
        formatter_class=ArgumentDefaultsHelpFormatter)
    p1.add_argument('-v',
                    '--verbose',
                    action='store_true',
                    default=False,
                    help="Verbose mode")
    p1.set_defaults(func=config)

    # Sender
    p2 = subsubparsers.add_parser(
        'send',
        aliases=['tx'],
        description=textwrap.dedent('''\

        Sends a file or a text message to the Satellite API for transmission
        via Blockstream Satellite. By default, runs the following sequence: 1)
        encapsulates the message into a structure containing the data checksum
        and the file name; 2) encrypts the entire structure using GnuPG; and 3)
        posts to the encrypted object to the API server for transmission.

        '''),
        help="Broadcast message through the Satellite API",
        formatter_class=ArgumentDefaultsHelpFormatter)
    msg_group = p2.add_mutually_exclusive_group()
    msg_group.add_argument('-f', '--file', help='File to send through the API')
    msg_group.add_argument('-m',
                           '--message',
                           help='Text message to send through the API')
    p2.add_argument('--bid',
                    default=None,
                    type=int,
                    help="Bid (in millisatoshis) for the message transmission")
    p2.add_argument(
        '-c',
        '--channel',
        type=int,
        default=ApiChannel.USER.value,
        choices=SENDABLE_API_CHANNELS,
        help="API transmission channel over which the message should be sent.")
    p2.add_argument(
        '--regions',
        nargs="+",
        choices=range(0, len(defs.satellites)),
        type=int,
        help="Satellites beams over which to send the message. Select "
        "one or multiple beams by numbers from 0 to 5 according to the "
        "following mapping: {}. Do not specify any region if the goal is "
        "to broadcast the message worldwide through all beams.".format(
            ", ".join([
                "{} for {}".format(i, x['alias'])
                for i, x in enumerate(defs.satellites)
            ])))
    p2.add_argument(
        '-r',
        '--recipient',
        default=None,
        help="Public key fingerprint of the desired recipient. If not "
        "defined, the recipient will be automatically set to the first "
        "public key in the keyring")
    p2.add_argument(
        '--trust',
        default=False,
        action="store_true",
        help="Assume that the recipient\'s public key is fully trusted")
    p2.add_argument('--sign',
                    default=False,
                    action="store_true",
                    help="Sign message in addition to encrypting it")
    p2.add_argument(
        '--sign-key',
        default=None,
        help="Fingerprint of the private key to be used when signing the "
        "message. If not set, the default key from the keyring will be used")
    p2.add_argument(
        '--send-raw',
        default=False,
        action="store_true",
        help="Send the raw file or text message, i.e., without the data "
        "structure that includes the file name and checksum")
    p2.add_argument(
        '--plaintext',
        default=False,
        action="store_true",
        help="Send data in plaintext format, i.e., without encryption")
    p2.add_argument(
        '--fec',
        default=False,
        action="store_true",
        help="Send data with forward error correction (FEC) encoding")
    p2.add_argument(
        '--fec-overhead',
        default=0.1,
        type=float,
        help="Target ratio between the overhead FEC chunks and the original "
        "chunks. For example, 0.1 implies one overhead (redundant) chunk for "
        "every 10 original chunks")
    p2.add_argument(
        '--no-password',
        default=False,
        action="store_true",
        help="Whether to access the GPG keyring without a password")
    p2.add_argument(
        '--invoice-exec',
        help="Execute command with the Lightning invoice. Replaces the string "
        "\'{}\' with the Lightning bolt11 invoice string.")
    p2.add_argument(
        '--no-wait',
        default=False,
        action="store_true",
        help="Return immediately after submitting an API transmission order. "
        "Do not wait for the payment and transmission confirmations")
    p2.set_defaults(func=send)

    # Listen
    p3 = subsubparsers.add_parser(
        'listen',
        aliases=['rx'],
        description=textwrap.dedent('''\

        Receives Satellite API messages sent over the Blockstream Satellite
        network. By default, assumes the incoming messages are generated by the
        "api send" command, which transmits encapsulated and encrypted
        messages. Thus, it first attempts to decrypt the data using a local
        GnuPG key. On successful decryption, this application validates the
        integrity of the data and saves it into the download directory.

        '''),
        help="Listen to API messages",
        formatter_class=ArgumentDefaultsHelpFormatter)
    p3.add_argument(
        '--sock-addr',
        default=defs.api_dst_addr,
        help="Multicast UDP address (ip:port) used to listen for API data")
    intf_arg = p3.add_mutually_exclusive_group()
    intf_arg.add_argument('-i',
                          '--interface',
                          default=None,
                          help="Network interface that receives API data")
    intf_arg.add_argument(
        '-d',
        '--demo',
        action="store_true",
        default=False,
        help="Use the same interface as the demo-rx tool, i.e., the loopback "
        "interface")
    p3.add_argument(
        '-c',
        '--channel',
        type=int,
        default=ApiChannel.USER.value,
        choices=API_CHANNELS,
        help="Listen to a specific API transmission channel. If set to 0, "
        "listen to all channels. By default, listen to user transmissions, "
        "which are sent on channel 1")
    p3.add_argument(
        '--save-raw',
        default=False,
        action="store_true",
        help="Save the raw decrypted data into the download directory while "
        "ignoring the existence of a data encapsulation structure")
    p3.add_argument(
        '--plaintext',
        default=False,
        action="store_true",
        help="Do not try to decrypt the incoming messages. Instead, assume "
        "they are in plaintext format and save them as files named with "
        "timestamps. Note this operation mode saves all incoming messages, "
        "including those broadcast by other users. In contrast, the default "
        "mode (with decryption) only saves the successfully decrypted "
        "messages.")
    p3.add_argument(
        '--sender',
        default=None,
        help="Public key fingerprint of a target sender used to filter the "
        "incoming messages. When specified, the application processes only "
        "the messages that are digitally signed by the selected sender, "
        "including clearsigned messages.")
    p3.add_argument('--no-password',
                    default=False,
                    action="store_true",
                    help="Set to access GPG keyring without a password")
    p3.add_argument(
        '--echo',
        default=False,
        action='store_true',
        help="Print the contents of all incoming text messages to the "
        "console, as long as these messages are decodable in UTF-8")
    stdout_exec_arg_group = p3.add_mutually_exclusive_group()
    stdout_exec_arg_group.add_argument(
        '--stdout',
        default=False,
        action='store_true',
        help="Serialize the received data to stdout instead of saving on a "
        "file")
    stdout_exec_arg_group.add_argument(
        '--no-save',
        default=False,
        action='store_true',
        help="Do not save the files decoded from the received API messages")
    stdout_exec_arg_group.add_argument(
        '--exec',
        help="Execute arbitrary shell command for each downloaded file. "
        "Use the magic string \'{}\' to represent the file path within the "
        "command. For instance, run \"--exec \'cat {}\'\" to print every "
        "incoming file to stdout. For security, this option must be used in "
        "conjunction with the --sender option to limit the execution of the "
        "specified command to digitally signed messages from a specified "
        "sender only. See option --insecure for an alternative.")
    p3.add_argument(
        "--save-dir",
        default=None,
        help="Directory where the decoded messages are saved. When not "
        "specified, defaults to the \"api/downloads\" subdirectory within the "
        "configuration directory (by default at \"~/.blocksat/\").")
    p3.add_argument(
        '--insecure',
        default=False,
        action="store_true",
        help="Run the --exec option while receiving messages from any sender. "
        "In this case, any successfully decrypted message (i.e., any message) "
        "encrypted using your public key will trigger the --exec command, "
        "which is considered insecure. Use at your own risk and avoid unsafe "
        "commands.")
    btc_src_gossip_arg_group1 = p3.add_mutually_exclusive_group()
    btc_src_gossip_arg_group1.add_argument(
        '--gossip',
        default=False,
        action="store_true",
        help="Configure the application to receive Lightning gossip snapshots "
        "and load them using the historian-cli application. This argument "
        "overrides the following options: 1) --plaintext (enabled); and 2) "
        "--channel (set to {}).".format(ApiChannel.GOSSIP.value))
    btc_src_gossip_arg_group1.add_argument(
        '--btc-src',
        default=False,
        action="store_true",
        help="Configure the application to receive API messages carrying the "
        "Bitcoin Satellite and Bitcoin Core source codes. This argument "
        "overrides the following options: 1) --plaintext (enabled); and 2) "
        "--channel (set to {}).".format(ApiChannel.BTC_SRC.value))
    p3.add_argument(
        '--historian-path',
        default=None,
        help="Path to the historian-cli application. If not set, look for "
        "historian-cli globally")
    p3.add_argument(
        '--historian-destination',
        default=None,
        help="Destination for gossip snapshots, formatted as "
        "[nodeid]@[ipaddress]:[port]. If not set, historian-cli attempts to "
        "discover the destination automatically. This parameter is provided "
        "as a positional argument of command \'historian-cli snapshot load\', "
        "which is called for each downloaded file in gossip mode (i.e., when "
        "argument --gossip is set).")
    p3.add_argument('-r',
                    '--region',
                    choices=range(0, 6),
                    type=int,
                    help="Coverage region for Rx confirmations")
    p3.set_defaults(func=listen)

    # Bump
    p4 = subsubparsers.add_parser(
        'bump',
        description="Bump bid of an API message order",
        help="Bump bid of an API message order",
        formatter_class=ArgumentDefaultsHelpFormatter)
    p4.add_argument(
        '--bid',
        default=None,
        type=int,
        help="New bid (in millisatoshis) for the message transmission")
    p4.add_argument('-u',
                    '--uuid',
                    default=None,
                    help="API order's universally unique identifier (UUID)")
    p4.add_argument('-a',
                    '--auth-token',
                    default=None,
                    help="API order's authentication token")
    p4.set_defaults(func=bump)

    # Delete
    p5 = subsubparsers.add_parser(
        'delete',
        aliases=['del'],
        description="Delete API message order",
        help="Delete API message order",
        formatter_class=ArgumentDefaultsHelpFormatter)
    p5.add_argument('-u',
                    '--uuid',
                    default=None,
                    help="API order's universally unique identifier (UUID)")
    p5.add_argument('-a',
                    '--auth-token',
                    default=None,
                    help="API order's authentication token")
    p5.set_defaults(func=delete)

    # Demo receiver
    p6 = subsubparsers.add_parser(
        'demo-rx',
        description=textwrap.dedent('''\

        Demo Blockstream Satellite Receiver, used to test the API data listener
        application without an actual satellite receiver. A real satellite
        receiver receives UDP packets sent over satellite and relays these
        packets to a host PC, where the API data listener application runs.
        This application imitates this behavior and produces equivalent UDP
        packets to the API data listener. The difference is that it fetches the
        data through the internet, rather than receiving via satellite.

        '''),
        help='Run demo satellite receiver',
        formatter_class=ArgumentDefaultsHelpFormatter)
    p6.add_argument(
        '--poll',
        action='store_true',
        default=False,
        help='Poll transmitting messages from the API queue instead of '
        'listening to server-sent event notifications.')
    p6.add_argument(
        '-d',
        '--dest',
        default=defs.api_dst_addr,
        help="Destination address (ip:port) to which API data will be sent")
    p6.add_argument(
        '-i',
        '--interface',
        nargs="+",
        help="Network interface(s) over which to send the API data. If \
        multiple interfaces are provided, the same packets are sent over all \
        interfaces.",
        default=["lo"])
    p6.add_argument('-c',
                    '--channel',
                    type=int,
                    default=ApiChannel.USER.value,
                    choices=SENDABLE_API_CHANNELS,
                    help="Target API transmission channel")
    p6.add_argument(
        '-r',
        '--regions',
        nargs="+",
        choices=range(0, len(defs.satellites)),
        type=int,
        help="Coverage region of the demo receiver. Optionally define "
        "multiple arguments to simulate reception from multiple satellite "
        "beams simultaneously. An empty list implies all regions.")
    p6.add_argument(
        '--if-by-region',
        action='store_true',
        default=False,
        help="Map each network interface to a single region. "
        "Requires the same number of arguments on the -i/--interface "
        "and -r/--regions options.")
    p6.add_argument('--ttl',
                    type=int,
                    default=1,
                    help="Time-to-live to set on multicast packets")
    p6.add_argument(
        '--dscp',
        type=int,
        default=0,
        help="Differentiated services code point (DSCP) to set on the output \
        multicast IP packets")
    p6.add_argument(
        '--bitrate',
        type=float,
        default=1000,
        help="Maximum bit rate of the output packet stream in kbps. "
        "Set 0 to transmit as fast as the socket(s) can handle.")
    p6.add_argument('-e',
                    '--event',
                    choices=["transmitting", "sent"],
                    default="sent",
                    help='SSE event that should trigger packet transmissions')
    p6.set_defaults(func=demo_rx)

    # Get message
    p7 = subsubparsers.add_parser(
        'get',
        description="Get an API message order",
        help="Get an API message order",
        formatter_class=ArgumentDefaultsHelpFormatter)
    p7.add_argument('-u',
                    '--uuid',
                    default=None,
                    help="Universally unique identifier (UUID)")
    p7.add_argument('-a',
                    '--auth-token',
                    default=None,
                    help="Authentication token")
    p7.set_defaults(func=get)

    # List orders
    p8 = subsubparsers.add_parser(
        'list',
        description="List transmission orders on the server queue",
        help="List transmission orders on the server queue",
        formatter_class=ArgumentDefaultsHelpFormatter)
    p8.add_argument('-c',
                    '--channel',
                    type=int,
                    default=ApiChannel.USER.value,
                    choices=SENDABLE_API_CHANNELS,
                    help="Order transmission channel")
    p8.add_argument('--status',
                    choices=ORDER_STATUS,
                    default=None,
                    nargs='+',
                    help="Target order status")
    p8.add_argument('--queue',
                    choices=ORDER_QUEUES,
                    default='queued',
                    help="Target order queue")
    p8.add_argument('--limit',
                    type=int,
                    default=20,
                    help="Limit for the number of orders returned")
    p8.set_defaults(func=list_orders)

    return p


def print_help(args):
    """Re-create argparse's help menu for the api command"""
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(title='', help='')
    parser = subparser(subparsers)
    print(parser.format_help())
