import logging, os, getpass
import gnupg
from .. import util


logger = logging.getLogger(__name__)


class Gpg():
    def __init__(self, gpghome, verbose=False, interactive=False):
        """Create GnuPG instance"""
        if (not os.path.exists(gpghome)):
            os.mkdir(gpghome)

        self.interactive = interactive
        self.gpghome     = gpghome
        self.passphrase  = None

        # Create GPG object and fetch the list of current private keys
        self.gpg     = gnupg.GPG(verbose = verbose, gnupghome = gpghome)

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
                matching_key['fingerprint'],
                matching_key['uids']
            ))

            if (not self.interactive):
                logger.info("Aborting")
                return
            elif(util._ask_yes_or_no("Abort the creation of a new key?")):
                return

        # Password
        if (passphrase is None):
            passphrase = getpass.getpass(prompt='Please enter the passphrase to '
                                         'protect your new key: ')

        # Generate key
        key_params = self.gpg.gen_key_input(
            key_type = "RSA",
            key_length = 1024,
            name_real = name,
            name_comment = comment,
            name_email = email,
            passphrase = passphrase
        )
        key        = self.gpg.gen_key(key_params)

        # Export
        public_key  = self.gpg.export_keys(key.fingerprint)
        private_key = self.gpg.export_keys(key.fingerprint, True,
                                           passphrase = passphrase)

        logger.info("Keys succesfully generated at {}".format(
            os.path.abspath(self.gpghome)))

    def set_passphrase(self, passphrase):
        self.passphrase = passphrase

    def get_default_public_key(self):
        """Get the fingerprint of the first public key on the keyring"""
        return self.gpg.list_keys()[0]

    def get_default_priv_key(self):
        """Get the fingerprint of the first private key on the keyring"""
        return self.gpg.list_keys(True)[0]

    def get_public_key(self, fingerprint):
        """Find a specific public key on the keyring"""
        key_map = self.gpg.list_keys().key_map
        assert(fingerprint in key_map), \
            "Could not find public key {}".format(fingerprint)
        return key_map[fingerprint]

    def get_priv_key(self, fingerprint):
        """Find a specific private key on the keyring"""
        key_map = self.gpg.list_keys(True).key_map
        assert(fingerprint in key_map), \
            "Could not find private key {}".format(fingerprint)
        return key_map[fingerprint]

    def encrypt(self, data, recipients, always_trust=False, sign=None):
        """Encrypt a given data array"""
        return self.gpg.encrypt(
            data,
            recipients,
            always_trust = always_trust,
            sign = sign,
            passphrase = self.passphrase
        )

    def decrypt(self, data):
        """Decrypt a given data array"""
        if (not self.interactive and self.passphrase is None):
            raise RuntimeError(
                "Passphrase must be defined in non-interactive mode")

        return self.gpg.decrypt(data, passphrase = self.passphrase)

    def sign(self, data, keyid, clearsign=True):
        """Sign a given data array"""
        return self.gpg.sign(
            data,
            keyid = keyid,
            clearsign = clearsign,
            passphrase = self.passphrase
        )


