"""Receiver monitoring API"""
import json
import logging
import os
import queue
import threading
import time

import requests

from . import util
from . import defs
from . import config
from .cache import Cache
from .api import api
from .api.pkt import ApiChannel
from .api.gpg import Gpg
from .api.listen import ApiListener

logger = logging.getLogger(__name__)
base_url = "https://satellite.blockstream.space/monitoring"
account_endpoint = os.path.join(base_url, 'accounts')
metric_endpoint = os.path.join(base_url, "metrics")


def _register_explainer():
    os.system('clear')
    util._print_header("Receiver Monitoring")

    util.fill_print("Option --report enables periodic reporting of receiver \
    performance metrics to Blockstream's monitoring server. This information \
    is sent over the internet and is used to help us improve the satellite \
    communications service.")

    util.prompt_for_enter()
    util._print_sub_header("Reported Metrics")

    util.fill_print("The reported metrics vary according to the receiver type "
                    "and consist of a subset of the following:")
    print("  - Demodulator lock status.")
    print("  - Signal level.")
    print("  - Signal-to-noise ratio (SNR).")
    print("  - Bit error ratio (BER).")
    print("  - Signal quality (%).")
    print("  - Packet error count.")

    util.prompt_for_enter()
    util._print_sub_header("Registration Procedure")

    util.fill_print(
        "An initial registration procedure is necessary to confirm \
    you are running a functional satellite receiver. Our server will send you \
    a verification code over satellite and will wait for reception \
    confirmation. This application, in turn, will wait for the \
    verification code and, upon successful reception, will \
    confirm it to the server (over the internet).")

    util.prompt_for_enter()
    util._print_sub_header("Collected Information")

    util.fill_print("For registration, we require the following information:")

    print("  1) Your location (city, country, and state, if applicable).")
    print("  2) Your public GPG key, created and used by the Satellite API "
          "apps.\n")

    util.fill_print("The location information is essential for us to improve \
    the service worldwide. Meanwhile, the public key is used for the initial \
    registration procedure and, subsequently, to authenticate your receiver \
    status reports. Refer to further information at:")

    print(defs.user_guide_url + "doc/monitoring.html\n")

    util.fill_print("Note that any identification information held by the \
    public key will be included in the data sent to Blockstream. For \
    instance, the username, e-mail address, and the optional comment \
    attached to the public key on its creation.")

    util.fill_print("Additionally, the CLI will automatically send some \
    hardware information during the registration step. More specifically, it \
    will communicate the adopted receiver, antenna, and LNB model. No other \
    personal data is required nor collected.")

    util.fill_print(
        "If you have never used the Satellite API before, you will \
    be prompted to create a new GPG keypair next. Otherwise, you will be \
    prompted for your GPG passphrase and location.")

    util.prompt_for_enter()


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
    def __init__(self, cfg, cfg_dir, gnupghome, passphrase=None):
        self.cfg = cfg
        self.cfg_dir = cfg_dir
        self.gpg = Gpg(os.path.join(cfg_dir, gnupghome))

        if (passphrase is not None):
            self.gpg.set_passphrase(passphrase)

        # Check if this receiver setup is already registered
        self.user_info = config.read_cfg_file(cfg, cfg_dir)
        self.registered = 'monitoring' in self.user_info and \
            self.user_info['monitoring']['registered']

        # Register with the Monitoring API if necessary
        self.rx_lock_event = threading.Event()
        if (not self.registered):
            self._register()
        else:
            self._setup_registered()

    def _setup_registered(self):
        """Setup for a receiver that is already registered

        If already registered, confirm that the registered GPG key is available
        in the keyring and prompt for the GPG private key passphrase required
        to sign report data

        """
        fingerprint = self.user_info['monitoring']['fingerprint']
        matching_keys = self.gpg.gpg.list_keys(True, keys=fingerprint)
        if (len(matching_keys) == 0):
            logger.error("Could not find key {} in the local "
                         "keyring.".format(fingerprint))
            try_again = util._ask_yes_or_no(
                "Reset the Monitoring API credentials and try registering "
                "with a new key?",
                default="n")
            if (try_again):
                self._delete_credentials()
                self._register()
            else:
                raise RuntimeError("Monitoring configuration failed")

            # Return regardless. If the key is not available, don't bother
            # about the password.
            return
        self.gpg.prompt_passphrase('Please enter your GPG passphrase to '
                                   'sign receiver reports: ')

    def _delete_credentials(self):
        """Remove the registration info from the local config file"""
        self.user_info.pop('monitoring')
        config.write_cfg_file(self.cfg, self.cfg_dir, self.user_info)
        self.registered = False

    def _save_credentials(self, uuid, fingerprint):
        """Record the successful registration locally on the JSON config"""
        self.user_info['monitoring'] = {
            'registered': True,
            'uuid': uuid,
            'fingerprint': fingerprint
        }
        config.write_cfg_file(self.cfg, self.cfg_dir, self.user_info)
        self.registered = True

    def _register(self):
        """Run the registration procedure

        The procedure is divided in two steps:

        1) Interaction with the user;
        2) Interaction with the API.

        This method implements step 1, where it sets up a GPG keyring, collects
        the user address, and prepares the request parameters for registering
        with the monitoring API. In the end, it dispatches step 2 on a thread.

        Note step 2 has to run on a thread because it needs the receiver lock
        first. By running on a thread, the main (parent) thread can proceed to
        initializing the receiver.

        """
        self.registration_running = True
        self.registration_failure = False

        # Save some state on the local cache
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
            util.fill_print("Please inform your GPG passphrase to decode the "
                            "encrypted verification code sent over satellite")
            self.gpg.prompt_passphrase("GPG passphrase: ")

        os.system('clear')

        # Get the user's location
        util.fill_print(
            "Please inform you city, state (if applicable), and country:")
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
            confirmed = util._ask_yes_or_no("\"{}\"?".format(address))

        os.system('clear')

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
                              args=(fingerprint, pubkey, address, satellite,
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
                logger.info("Ready to report Rx metrics to the monitoring "
                            "server")
                self._save_credentials(uuid, fingerprint)
                break

        if (attempts == 0):
            logger.error("Maximum number of registration attempts " "reached")
            logger.error("Please check if your receiver is running properly "
                         "and restart the application to try again")
            failure = True

        self.registration_running = False
        self.registration_failure = failure

        # Stop the API listener
        listen_loop.stop()
        listen_thread.join()

    def sign_report(self, data):
        """Sign a dictionary of metrics to be reported to the monitoring API

        First, add the monitored receiver's UUID to the dictionary of
        metrics. Then, use the default local GPG privkey to generate a detached
        signature corresponding to the JSON-dumped version of the dictionary
        (including the UUID). Lastly, append the detached signature. The
        resulting dictionary (including both the UUID and the signature) is
        ready to be sent to the API.

        Args:
            data : Dictionary with receiver data to be reported

        """
        assert (self.registered)
        data['uuid'] = self.user_info['monitoring']['uuid']
        fingerprint = self.user_info['monitoring']['fingerprint']
        data['signature'] = str(
            self.gpg.sign(json.dumps(data),
                          fingerprint,
                          clearsign=False,
                          detach=True))
        if (data['signature'] == ''):
            logger.error('GPG signature failed')
