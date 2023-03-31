"""Receiver monitoring API"""
import json
import logging
import os
import queue
import sys
import threading
import time
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

import requests

from . import util
from . import defs
from . import config
from .cache import Cache
from .api import api
from .api.gpg import Gpg, is_gpg_keyring_set
from .api.listen import ApiListener
from .api.order import ApiChannel

logger = logging.getLogger(__name__)
DEFAULT_SERVER_URL = "https://satellite.blockstream.space/monitoring"


def _privacy_explainer():
    util.print_sub_header("Reported Metrics")

    util.fill_print("The reported metrics vary according to the receiver type "
                    "and consist of a subset of the following:")
    print("  - Demodulator lock status.")
    print("  - Signal level.")
    print("  - Signal-to-noise ratio (SNR).")
    print("  - Bit error ratio (BER).")
    print("  - Signal quality.")
    print("  - Packet error count.")

    util.prompt_for_enter()
    util.print_sub_header("Registration Procedure")

    util.fill_print(
        "An initial registration procedure is necessary to confirm \
    you are running a functional satellite receiver. Our server will send you \
    a verification code over satellite and wait for reception \
    confirmation. This application, in turn, will wait for the \
    verification code and, upon successful reception, will \
    confirm it to the server (over the internet).")

    util.prompt_for_enter()
    util.print_sub_header("Collected Information")

    util.fill_print("In addition to the receiver metrics reported \
    periodically by the CLI, we collect the following information on the \
    initial registration:")

    print("  1) Your location (city, country, and state).")
    print("  2) Your public GPG key, created and used by the Satellite API "
          "apps.\n")

    util.fill_print("Note that any identification information held by the \
    GPG public key will be included in the data sent to Blockstream. For \
    instance, the username, e-mail address, and the optional comment \
    attached to the key on its creation.")

    util.fill_print("Additionally, the CLI will automatically send some \
    hardware information during registration. More specifically, it will \
    communicate the adopted receiver type, the antenna model or size, and \
    the LNB specifications. No other personal data is required nor collected.")

    util.prompt_for_enter()

    util.print_sub_header("Why We Collect The Information")

    util.fill_print("The location information (city, country, and state) \
    collected on registration allows us to analyze the receiver performances \
    worldwide and continuously improve the service. For example, it enables \
    the identification of weak coverage spots. By reporting it, you will help \
    us improve the Blockstream Satellite service. Besides, note we do not \
    need the receiver's exact geolocation, only the coarse city/state \
    coordinates.")

    util.fill_print("The public GPG key collected on registration is used for \
    the initial registration procedure and, subsequently, for authenticating \
    your requests to the monitoring API.")

    util.fill_print("Please refer to further information at:")

    print(defs.user_guide_url + "doc/monitoring.html\n")

    util.prompt_for_enter()


def _register_explainer():
    os.system('clear')
    util.print_header("Receiver Monitoring")

    util.fill_print("Option --report enables periodic reporting of receiver \
    performance metrics to Blockstream's monitoring server. This information \
    is sent over the internet and is used to help us improve the satellite \
    communications service.")

    util.fill_print("For registration, we require the following information:")

    print("  1) Your location (city, country, and state, if applicable).")
    print("  2) Your public GPG key, created and used by the Satellite API "
          "apps.\n")

    util.fill_print(
        "If you have never used the Satellite API before, you will \
    be prompted to create a new GPG keypair next. Otherwise, you will be \
    prompted for your GPG passphrase and location.")

    print_privacy_info = util.ask_yes_or_no(
        "See more info about the collected data and registration procedure?",
        default='n')

    os.system('clear')

    if (print_privacy_info):
        _privacy_explainer()


def _ask_address():
    confirmed = False
    while (not confirmed):
        # City (required)
        city = util.string_input("City")

        # State (optional)
        state = input("State: ")
        if (len(state) > 0):
            address = "{}, {}".format(city, state)
        else:
            address = city

        # Country (required)
        country = util.string_input("Country")

        # Wait until the user confirms the full address
        address += ", {}".format(country)
        confirmed = util.ask_yes_or_no("\"{}\"?".format(address))

    return address


class BsMonitoring():
    """Blockstream Satellite Monitoring API

    This class handles the communication with the Monitoring API used to
    monitor Blockstream Satellite receivers who opt-in to report their receiver
    status metrics.

    When constructed for the first time, this class attempts to register the
    receiver with the Monitoring API. After successful registration, it will
    cache the account UUID locally on the config file.

    Note the Monitoring API requires a new account (i.e., a new UUID) for each
    unique combination of satellite, receiver type, and GPG fingerprint. Hence,
    each configuration (i.e., each config file on a given config directory)
    will register a new account and obtain a unique UUID.

    When the receiver is already registered, as indicated by the local config
    file, this class proceeds with metric reporting right away.

    """

    def __init__(self,
                 cfg,
                 cfg_dir,
                 server_url,
                 gnupghome,
                 passphrase=None,
                 interactive=True,
                 lazy=False):
        """Construct the BsMonitoring object

        Args:
            cfg (str): User configuration.
            cfg_dir (str): Configuration directory.
            server_url (str): Monitoring API server URL.
            gnupghome (str):  GnuPG home directory.
            passphrase (str, optional): GPG private key passphrase for
                non-interactive mode. When not defined, the user is prompted
                for the passphrase instead. Defaults to None.
            interactive (bool, optional): Whether to run in interactive mode.
            lazy (bool, optional): When True, the constructor returns before
                running the initial interactive setup. Defaults to False.
        """
        self.cfg = cfg
        self.cfg_dir = cfg_dir
        self.server_url = server_url
        self.gpg = Gpg(os.path.join(cfg_dir, gnupghome))

        if (passphrase is not None):
            self.gpg.set_passphrase(passphrase)

        self.interactive = interactive
        self.api_pwd = None
        self.api_cfg_dir = os.path.join(self.cfg_dir, 'monitoring_api')

        # Check if this receiver setup is already registered
        self.user_info = config.read_cfg_file(cfg, cfg_dir)
        self.registered = 'monitoring' in self.user_info and \
            self.user_info['monitoring']['registered']
        self.disabled = False

        if lazy:
            return

        # Register with the Monitoring API if necessary
        self.rx_lock_event = threading.Event()
        if not self.registered:
            self._register()
        else:
            self._setup_registered()

    def has_matching_keys(self):
        """Check if the GPG key used for monitoring is available"""
        fingerprint = self.user_info['monitoring']['fingerprint']
        matching_keys = self.gpg.gpg.list_keys(True, keys=fingerprint)
        if (len(matching_keys) == 0):
            logger.error("Could not find key {} in the local "
                         "keyring.".format(fingerprint))
        return len(matching_keys) > 0

    def _setup_registered(self):
        """Setup for a receiver that is already registered

        If already registered, confirm that the registered GPG key is available
        in the keyring and prompt for the GPG private key passphrase required
        to sign report data. Load also the non-GPG password from the local
        encrypted password file.

        """
        logger.info("Loading the Monitoring API reporting credentials")

        if not self.has_matching_keys():
            # In non-interactive mode, delete the credentials and try
            # registering again with no prompt to the user. There is no concern
            # with losing the credentials here because the Monitoring API
            # informs when a registering account already exists and is already
            # verified. Also, the password can be regenerated as needed.
            try_again = not self.interactive or util.ask_yes_or_no(
                "Reset the Monitoring API credentials and try registering "
                "with a new key?",
                default="n")
            if (try_again):
                self.delete_credentials()
                self._register()
            else:
                print("Aborting")
                sys.exit(1)

            # Return regardless. If the key is not available, don't bother
            # about the password.
            return

        self.gpg.prompt_passphrase('Please enter your GPG passphrase to '
                                   'sign receiver reports: ')

        # If the passphrase is wrong, it will not be possible decrypt an
        # existing password nor generate a new encrypted one. Also, it will not
        # be possible to sign reports with the private key, so there is nothing
        # else to do. Disable the reporting.
        if not self.gpg.test_passphrase(
                self.user_info['monitoring']['fingerprint']):
            logger.error("Disabling the Rx status reporting")
            self.disabled = True
            return

        if not self.has_password():
            self.gen_api_password()
        else:
            self.load_api_password()

        logger.info("Ready to report the Rx status to the Monitoring API")

    def delete_credentials(self):
        """Remove the registration info from the local config file"""
        self.user_info.pop('monitoring')
        config.write_cfg_file(self.cfg, self.cfg_dir, self.user_info)
        self.registered = False

    def _save_credentials(self, uuid, fingerprint, has_password=False):
        """Record the successful registration locally on the JSON config"""
        self.user_info['monitoring'] = {
            'registered': True,
            'uuid': uuid,
            'fingerprint': fingerprint,
            'has_password': has_password
        }
        config.write_cfg_file(self.cfg, self.cfg_dir, self.user_info)
        self.registered = True

    def _get_api_password_file_path(self):
        fingerprint = self.user_info['monitoring']['fingerprint']
        return os.path.join(self.api_cfg_dir,
                            f'{fingerprint}_{self.cfg}_pwd.gpg')

    def has_password(self):
        return ('monitoring' in self.user_info) and \
            ('has_password' in self.user_info['monitoring']) and \
            (self.user_info['monitoring']['has_password'])

    def _save_api_password(self, password):
        """Encrypt and save the monitoring password locally

        Args:
            password (str): Monitoring password
        """
        if not os.path.exists(self.api_cfg_dir):
            os.mkdir(self.api_cfg_dir)

        # Encrypt the password using the user's public key
        recipient = self.user_info['monitoring']['fingerprint']
        enc_password = self.gpg.encrypt(password, recipient).data
        api_pwd_file = self._get_api_password_file_path()
        with open(api_pwd_file, 'wb') as fd:
            fd.write(enc_password)

        logger.info(f"Saved the encrypted password at {api_pwd_file}")

        # Flag the password availability on the user configuration file
        self.user_info['monitoring']['has_password'] = True
        config.write_cfg_file(self.cfg, self.cfg_dir, self.user_info)

    def load_api_password(self):
        """Load the password used for non-GPG authentication

        When already defined, the password is available locally on an encrypted
        file. This function decrypts it and loads the password.

        """
        api_pwd_file = self._get_api_password_file_path()
        if not os.path.exists(api_pwd_file):
            logger.error(f"Password file {api_pwd_file} does not exist")
            return

        with open(api_pwd_file, 'rb') as fd:
            enc_password = fd.read()

        dec_password = self.gpg.decrypt(enc_password)

        if not dec_password.ok:
            logger.error(
                "Unable to decrypt the password for report authentication ({})"
                .format(dec_password.status))
            return

        self.api_pwd = dec_password.data.decode()

        # The config file may indicate there is no password (if changing gpg
        # home dirs), but now we know there is a password that can be decrypted
        # with the given fingerprint. So update the info.
        self.user_info['monitoring']['has_password'] = True
        config.write_cfg_file(self.cfg, self.cfg_dir, self.user_info)

    def gen_api_password(self):
        """Generate password for non-GPG-authenticated requests

        This is the password used as a lightweight authentication mechanism in
        specific endpoints that accept it as an alternative to the main
        authentication approach based on a detached GPG signature.

        """
        if self.api_pwd is not None:
            return

        request_payload = {}
        self.sign_request(request_payload)
        rv = requests.post(os.path.join(self.server_url, 'accounts',
                                        "password"),
                           json=request_payload)

        if (rv.status_code != requests.codes.ok):
            logger.error("Password generation failed")
            logger.error("{} ({})".format(rv.reason, rv.status_code))
        else:
            logger.info("Created a new password to authenticate reports")
            self.api_pwd = rv.json()['new_password']
            self._save_api_password(self.api_pwd)

    def _register_interactive(self):
        """Interactive configuration of the user setup

        Executes the following steps:
            1) Shows the registration explainer;
            2) Ensures a GPG keyring is set up;
            3) Loads and validates the GPG passphrase for decoding;
            4) Collects the user address interactively.

        Returns:
            str: The collected address or None in case of failure.

        """
        cache = Cache(self.cfg_dir)

        # Show the explainer when running the registration for the first time
        # for this configuration
        if (cache.get(self.cfg + '.monitoring.explainer') is None):
            _register_explainer()

        # Cache flag indicating that the explainer has been shown already
        cache.set(self.cfg + '.monitoring.explainer', True)
        cache.save()

        # Create a GPG keyring and a keypair if necessary
        api.config_keyring(self.gpg)

        # Make sure the GPG passphrase is available. The passphrase can be
        # collected on key creation for a new keyring. On the other hand, it
        # wouldn't be available yet at this point for a pre-existing keyring.
        if (self.gpg.passphrase is None):
            print()
            util.fill_print("Please inform your GPG passphrase to decode the "
                            "encrypted verification code sent over satellite")
            self.gpg.prompt_passphrase("GPG passphrase: ")

        # Make sure the passphrase works
        fingerprint = self.gpg.get_default_priv_key()['fingerprint']
        if not self.gpg.test_passphrase(fingerprint):
            logger.error("Aborting the registration with the Monitoring API")
            self.registration_running = False
            self.registration_failure = True
            return

        os.system('clear')

        # In interactive mode, the address is either loaded from the cache or
        # provided by the user
        use_cached_address = False
        cached_address = cache.get(self.cfg + '.monitoring.location')
        if cached_address is not None:
            use_cached_address = util.ask_yes_or_no(
                "Reporting from \"{}\"?".format(cached_address))

        if use_cached_address:
            address = cached_address
        else:
            util.fill_print(
                "Please inform you city, state (if applicable), and country:")
            address = _ask_address()
            cache.set(self.cfg + '.monitoring.location', address)
            cache.save()

        os.system('clear')
        return address

    def _register(self, address=None):
        """Run the registration procedure

        The procedure is divided in two steps:

        1) Interaction with the user;
        2) Interaction with the API.

        This method implements step 1 and dispatches step 2 on a thread. Step 2
        has to run on a thread because it needs the receiver lock first. By
        running on a thread, the main (parent) thread can proceed to
        initializing the receiver.

        Args:
            address (str, optional): Receiver's address used in non-interactive
                mode. Defaults to None.

        """
        self.registration_running = True
        self.registration_failure = False
        logger.info("Initiating the registration with the Monitoring API")

        if self.interactive:
            res = self._register_interactive()
            if res is None:
                return
            # Use the address collected interactively, not the one provided by
            # argument:
            _address = res
        else:
            # In non-interactive mode, the caller must take care of the steps
            # otherwise implemented by the interactive routine. Also, in this
            # case, the address must be provided by argument.
            assert is_gpg_keyring_set(self.gpg.gpghome)
            assert self.gpg.passphrase is not None
            assert address is not None
            _address = address

        # Registration parameters
        fingerprint = self.gpg.get_default_priv_key()['fingerprint']
        pubkey = self.gpg.gpg.export_keys(fingerprint)
        satellite = self.user_info['sat']['alias']
        rx_type = config.get_rx_model(self.user_info)
        antenna = config.get_antenna_model(self.user_info)
        lnb = config.get_lnb_model(self.user_info)

        # Run step 2 on a thread
        t1 = threading.Thread(target=self._register_thread,
                              daemon=True,
                              args=(fingerprint, pubkey, _address, satellite,
                                    rx_type, antenna, lnb))
        t1.start()

    def _register_thread(self,
                         fingerprint,
                         pubkey,
                         address,
                         satellite,
                         rx_type,
                         antenna,
                         lnb,
                         attempts=5):
        """Complete the registration procedure after receiver locking

        Sends the registration request to the Monitoring API and waits for the
        validation code sent over satellite through a Satellite API message.

        Args:
            fingerprint      : User GnuPG fingerprint
            pubkey           : User GnuPG public key
            address          : User address
            satellite        : Satellite covering the user location
            rx_type          : Receiver type (vendor and model)
            antenna          : Antenna type and size
            lnb              : LNB model
            attempts         : Maximum number of registration attempts

        """
        logger.info(
            "Waiting for Rx lock to initiate the registration with the "
            "monitoring server")
        self.rx_lock_event.wait()

        logger.info("Receiver locked. Ready to initiate the registration with "
                    "the monitoring server.")
        logger.info("Launching the API listener to receive the verification "
                    "code sent over satellite")

        # Run the API listener loop
        #
        # Note the validation code is:
        # - Encrypted to us (the Monitoring API encrypts using our public key)
        # - Sent as a raw (non-encapsulated) API message
        # - Sent over the API channel dedicated for authentication messages
        download_dir = None  # Don't save messages
        interface = config.get_net_if(self.user_info)
        recv_queue = queue.Queue()  # save API donwloads on this queue
        listen_loop = ApiListener(recv_queue=recv_queue)
        listen_thread = threading.Thread(target=listen_loop.run,
                                         daemon=True,
                                         args=(self.gpg, download_dir,
                                               defs.api_dst_addr, interface),
                                         kwargs={
                                             'channel': ApiChannel.AUTH.value,
                                             'plaintext': False,
                                             'save_raw': True,
                                             'no_save': True
                                         })
        listen_thread.start()

        failure = False
        account_endpoint = os.path.join(self.server_url, 'accounts')
        while (attempts > 0):
            rv = requests.post(account_endpoint,
                               json={
                                   'fingerprint': fingerprint,
                                   'publickey': pubkey,
                                   'city': address,
                                   'satellite': satellite,
                                   'receiver_type': rx_type,
                                   'antenna': antenna,
                                   'lnb': lnb
                               })

            if (rv.status_code != requests.codes.ok):
                logger.error("Failed to register receiver with the monitoring "
                             "server")
                logger.error("{} ({})".format(rv.reason, rv.status_code))

                # If the initial registration call fails, declare failure right
                # away and break the loop. The problem likely won't go away if
                # we try again (e.g., a server error or invalid pubkey).
                failure = True
                break

            uuid = rv.json()['uuid']
            verified = rv.json()['verified']

            if (verified):
                logger.info("Receiver already registered and verified")
                self._save_credentials(uuid, fingerprint)
                # If we are trying to register an account that already exists,
                # chances are that the config dir already has its non-GPG
                # password file. If not, try to redefine the password.
                self.load_api_password()
                self.gen_api_password()  # will generate only if necessary
                break

            try:
                validation_key = recv_queue.get(timeout=10)
                recv_queue.task_done()
            except queue.Empty:
                logger.warning("Failed to receive the verification code. "
                               "Trying again...")
                attempts -= 1
                continue

            rv = requests.patch(account_endpoint,
                                json={
                                    'uuid': uuid,
                                    'validation_key': validation_key.decode()
                                })

            if (rv.status_code != requests.codes.ok):
                logger.error("Verification failed")
                logger.error("{} ({})".format(rv.reason, rv.status_code))
                attempts -= 1
                if (attempts > 0):
                    logger.warning("Trying again...")
                    time.sleep(1)
            else:
                logger.info("Functional receiver successfully validated")
                logger.info(
                    "Ready to report the Rx status to the Monitoring API")
                self._save_credentials(uuid, fingerprint)
                # Now that the account is verified, we can generate the
                # password for non-GPG-authenticated requests
                self.gen_api_password()
                break

        if (attempts == 0):
            logger.error("Maximum number of registration attempts reached")
            logger.error("Please check if your receiver is running properly "
                         "and restart the application to try again")
            failure = True

        self.registration_running = False
        self.registration_failure = failure

        # Stop the API listener
        listen_loop.stop()
        listen_thread.join()

    def get_metric_endpoint(self):
        return os.path.join(self.server_url, "metrics")

    def sign_request(self, data, password_allowed=False):
        """Sign a dictionary of metrics to be reported to the monitoring API

        This function signs a request sent to the monitoring API. Two
        possibilities exist for signing: with a detached GPG signature of the
        payload or the account's password generated by the monitoring API.

        When using the GPG signature, this function first adds the accounts's
        UUID to the payload. Then, it uses the default local GPG privkey to
        generate a detached signature of the JSON-dumped payload data including
        the UUID. Lastly, it appends the detached signature to the request.

        When using the password, it first checks if the password is allowed for
        the given request and if the account has already generated such a
        password. In the positive case, it includes the receiver's UUID and the
        password in the request payload.

        Args:
            data : Dictionary with the request payload data.
            password_allowed (bool, optional): Whether a non-GPG password-based
                authentication is allowed for this request. Defaults to False.

        """
        assert (self.registered)
        data['uuid'] = self.user_info['monitoring']['uuid']

        if password_allowed and self.api_pwd:
            data['password'] = self.api_pwd
        else:
            fingerprint = self.user_info['monitoring']['fingerprint']
            data['signature'] = str(
                self.gpg.sign(json.dumps(data),
                              fingerprint,
                              clearsign=False,
                              detach=True))
            if (data['signature'] == ''):
                logger.error('GPG signature failed')


def not_registered_error():
    logger.error("This receiver is not registered with the Monitoring API yet")
    logger.info("Run the receiver with option \'--report\' to sign up and "
                "start reporting")


def show_info(args):
    user_info = config.read_cfg_file(args.cfg, args.cfg_dir)
    if 'monitoring' not in user_info:
        return not_registered_error()

    if args.json:
        print(json.dumps(user_info['monitoring'], indent=4))
        return

    print("| {:30s} | {:40s} |".format("Info", "Value"))
    print("|{:32s}|{:42s}|".format(32 * "-", 42 * '-'))
    for key, value in user_info['monitoring'].items():
        if key == 'uuid':
            key = key.upper()
        else:
            key = key.capitalize()
        print("| {:30s} | {:40s} |".format(key.replace('_', ' '), str(value)))


def _load_bs_monitoring(args):
    bs_monitoring = BsMonitoring(args.cfg,
                                 args.cfg_dir,
                                 args.server,
                                 args.gnupghome,
                                 args.passphrase,
                                 lazy=True)

    if not bs_monitoring.registered:
        not_registered_error()
        return

    if not bs_monitoring.has_matching_keys():
        logger.warning(
            "Please confirm the GPG home (option \'--gnupghome\') is "
            "set correctly")
        return

    return bs_monitoring


def set_password(args):
    bs_monitoring = _load_bs_monitoring(args)
    if bs_monitoring is None:
        return

    bs_monitoring.gpg.prompt_passphrase('Please enter your GPG passphrase to '
                                        'decrypt/encrypt the password: ')

    if not bs_monitoring.gpg.test_passphrase(
            bs_monitoring.user_info['monitoring']['fingerprint']):
        return

    if bs_monitoring.has_password():
        bs_monitoring.load_api_password()

    if bs_monitoring.api_pwd is not None:
        logger.info("Found existing password at {}.".format(
            bs_monitoring._get_api_password_file_path()))
        if not util.ask_yes_or_no("Reset password?", default='n'):
            print("Aborting")
            return
        # Let the password generation function generate a new one
        bs_monitoring.api_pwd = None

    bs_monitoring.gen_api_password()


def add_to_parser(parser):
    """Add monitoring API options to parser"""
    p = parser.add_argument_group(
        'Blockstream Monitoring API reporting options')
    p.add_argument(
        '--report-gnupghome',
        default=".gnupg",
        help="GPG home directory holding the keypair configured for "
        "authentication with the Monitoring API, relative to the "
        "config directory set by option --cfg-dir")
    p.add_argument(
        '--report-passphrase',
        default=None,
        help="Passphrase to the private GPG key used to authenticate with "
        "the Monitoring API. When undefined (default), the program prompts "
        "for the passphrase instead.")


def subparser(subparsers):  # pragma: no cover
    p = subparsers.add_parser(
        'reporting',
        description="Manage the reporting to the Monitoring API",
        help='Manage the reporting to the Monitoring API',
        formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('--server',
                   type=str,
                   default=DEFAULT_SERVER_URL,
                   help="Monitoring API server address")
    p.add_argument(
        '--gnupghome',
        '--gpghome',
        default=".gnupg",
        help="GPG home directory holding the keypair configured for "
        "authentication with the Monitoring API, relative to the "
        "config directory set by option --cfg-dir")
    p.add_argument(
        '--passphrase',
        default=None,
        help="Passphrase to the private GPG key used to authenticate with "
        "the Monitoring API. When undefined (default), the program prompts "
        "for the passphrase instead.")
    p.set_defaults(func=print_help)

    subsubparsers = p.add_subparsers(title='subcommands',
                                     help='Target sub-command')
    p1 = subsubparsers.add_parser(
        'info',
        description="Show current registration info",
        help="Show current registration info",
        formatter_class=ArgumentDefaultsHelpFormatter)
    p1.add_argument('--json',
                    default=False,
                    action='store_true',
                    help='Print results in JSON format')
    p1.set_defaults(func=show_info)

    p2 = subsubparsers.add_parser(
        'password',
        description="Set/reset the authentication password",
        help="Set/reset the authentication password",
        formatter_class=ArgumentDefaultsHelpFormatter)
    p2.set_defaults(func=set_password)

    return p


def print_help(args):  # pragma: no cover
    """Re-create argparse's help menu for the reporting command"""
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(title='', help='')
    parser = subparser(subparsers)
    print(parser.format_help())
