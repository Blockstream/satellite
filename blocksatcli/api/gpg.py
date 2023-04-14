import getpass
import logging
import os
import stat
import sys

import gnupg

from .. import defs
from .. import util

logger = logging.getLogger(__name__)


class Gpg():

    def __init__(self, gpghome, verbose=False, interactive=False):
        """Create GnuPG instance"""
        if (not os.path.exists(gpghome)):
            os.makedirs(gpghome)
            # Make sure only the owner has permissions to read, write, and
            # execute the GPG home directory
            os.chmod(gpghome, stat.S_IRWXU)

        self.interactive = interactive
        self.gpghome = gpghome
        self.passphrase = None

        # Create GPG object and fetch the list of current private keys
        self.gpg = gnupg.GPG(verbose=verbose, gnupghome=gpghome)

    def _find_gpg_key_by_email(self, email):
        """Find GPG key with matching email address on UID"""

        # Fetch the list of current private keys
        current_priv_keys = self.gpg.list_keys(True)

        for key in current_priv_keys:
            for uid in key['uids']:
                if (email in uid):
                    return key

    def create_keys(self, name, email, comment, passphrase=None):
        """Generate GPG Keys"""

        # Check if there is already a key with this e-mail address
        matching_key = self._find_gpg_key_by_email(email)
        if (matching_key):
            logger.info("Found existing key {} with uid {}".format(
                matching_key['fingerprint'], matching_key['uids']))

            if (not self.interactive):
                logger.info("Aborting")
                return
            elif (util.ask_yes_or_no("Abort the creation of a new key?")):
                return

        # Password
        if (passphrase is None):
            self.prompt_passphrase('Please enter a passphrase to protect '
                                   'your key: ')
        else:
            self.set_passphrase(passphrase)

        if not self.passphrase:
            logger.error("Empty passphrase")
            return

        # Generate key
        key_params = self.gpg.gen_key_input(key_type="RSA",
                                            key_length=1024,
                                            name_real=name,
                                            name_comment=comment,
                                            name_email=email,
                                            passphrase=self.passphrase)
        self.gpg.gen_key(key_params)
        logger.info("Keys succesfully generated at {}".format(
            os.path.abspath(self.gpghome)))

    def prompt_passphrase(self, prompt=None):
        if (self.passphrase is not None):
            return
        if (prompt is None):
            prompt = 'Please enter a passphrase: '
        try:
            self.set_passphrase(getpass.getpass(prompt=prompt))
        except KeyboardInterrupt:
            print("\nAborting")
            sys.exit(1)

    def set_passphrase(self, passphrase):
        if (self.passphrase is not None):
            logger.warning("GPG passphrase already set. Ignoring.")
            return
        self.passphrase = passphrase

    def test_passphrase(self, fingerprint):
        """Validate the defined key passphrase

        Args:
            fingerprint (str): Fingerprint of the private key associated with
                the passphrase.

        Returns:
            bool: Whether the passphrase works for the given private key.

        """
        if self.passphrase is None:
            return False
        res = self.gpg.export_keys(
            fingerprint,
            True,  # private key
            passphrase=self.passphrase)
        success = res is not None and res != ''
        if not success:
            logger.error("Bad passphrase.")
        return success

    def get_default_public_key(self):
        """Get the default (user) public key from the keyring

        Returns:
            Dictionary with key information such as 'fingerprint', 'keyid', and
            'uids'. None if not found.

        """
        for key in self.gpg.list_keys():
            if key['fingerprint'] != defs.blocksat_pubkey:
                return key

    def get_default_priv_key(self):
        """Get the default (user) private key from the keyring

        Returns:
            Dictionary with key information such as 'fingerprint', 'keyid', and
            'uids'. None if not found.

        """
        for key in self.gpg.list_keys(True):
            return key  # return the first private key found

    def get_public_key(self, fingerprint):
        """Find a specific public key on the keyring and return the info dict

        Returns:
            Dictionary with key information such as 'fingerprint', 'keyid', and
            'uids'.

        """
        key_map = self.gpg.list_keys().key_map
        assert (fingerprint in key_map), \
            "Could not find public key {}".format(fingerprint)
        return key_map[fingerprint]

    def get_priv_key(self, fingerprint):
        """Find a specific private key on the keyring and return the info dict

        Returns:
            Dictionary with key information such as 'fingerprint', 'keyid', and
            'uids'.
        """
        key_map = self.gpg.list_keys(True).key_map
        assert (fingerprint in key_map), \
            "Could not find private key {}".format(fingerprint)
        return key_map[fingerprint]

    def encrypt(self, data, recipients, always_trust=False, sign=None):
        """Encrypt a given data array"""
        return self.gpg.encrypt(data,
                                recipients,
                                always_trust=always_trust,
                                sign=sign,
                                passphrase=self.passphrase)

    def decrypt(self, data):
        """Decrypt a given data array"""
        if (not self.interactive and self.passphrase is None):
            raise RuntimeError(
                "Passphrase must be defined in non-interactive mode")

        return self.gpg.decrypt(data, passphrase=self.passphrase)

    def sign(self, data, keyid, clearsign=True, detach=False):
        """Sign a given data array"""
        assert (not (clearsign and detach)), \
            "clearsign and detach options are mutually exclusive"

        if (not self.interactive and self.passphrase is None):
            raise RuntimeError(
                "Passphrase must be defined in non-interactive mode")

        return self.gpg.sign(data,
                             keyid=keyid,
                             clearsign=clearsign,
                             detach=detach,
                             passphrase=self.passphrase)


def is_gpg_keyring_set(gnupghome):
    """Check if the keyring is already configured

    It is configured when:
    - It has at least one private key
    - It has at least two public keys
    - One of the public keys is the blocksat pubkey

    """
    if not os.path.exists(gnupghome):
        return False

    gpg = Gpg(gnupghome)

    if (len(gpg.gpg.list_keys(True)) == 0):  # no private key
        return False

    if (len(gpg.gpg.list_keys()) < 2):  # no two public keys
        return False

    if (len(gpg.gpg.list_keys(
            keys=defs.blocksat_pubkey)) == 0):  # blocksat key
        return False

    return True


def import_bs_pubkey(gpg):
    """Import Blockstream's public key from the package directory

    Args:
        gpg (Gpg): Gpg object.

    Raises:
        RuntimeError: If the GPG keyring is not properly configured before
        calling this function.
    """
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    key_path = os.path.join(pkg_dir, 'gpg', defs.blocksat_pubkey + ".gpg")

    with open(key_path) as fd:
        key_data = fd.read()

    import_result = gpg.gpg.import_keys(key_data)

    if (len(import_result.fingerprints) == 0):
        logger.warning("Failed to import key {}".format(defs.blocksat_pubkey))
        return

    logger.info("Imported key {}".format(import_result.fingerprints[0]))

    gpg.gpg.trust_keys(defs.blocksat_pubkey, 'TRUST_ULTIMATE')


def config_keyring(gpg, log_if_configured=False):
    """Configure the local keyring

    Create a keypair and import Blockstream's public key

    Args:
        gpg : Gpg object
        log_if_configured : Print log message if keyring is already configured

    """
    assert (isinstance(gpg, Gpg))
    if is_gpg_keyring_set(gpg.gpghome):
        if (log_if_configured):
            logger.info("Keyring already configured")
        return

    # Generate new keypair
    logger.info("Generating a GPG keypair to encrypt and decrypt API messages")
    name = util.string_input("User name represented by the key")
    email = util.string_input("E-mail address")
    comment = util.string_input("Comment to attach to the user ID",
                                optional=True)
    gpg.create_keys(name, email, comment)

    # Import Blockstream's public key
    import_bs_pubkey(gpg)

    if (not is_gpg_keyring_set(gpg.gpghome)):
        raise RuntimeError("GPG keyring configuration failed")
