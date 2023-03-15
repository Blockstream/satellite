import os
from unittest.mock import patch

from ..defs import blocksat_pubkey
from .gpg import Gpg, config_keyring
from ..test_helpers import TestEnv


class TestGpg(TestEnv):

    def test_key_creation(self):
        """Test creation of GPG keys"""
        name = "Test"
        email = "test@test.com"
        comment = "comment"
        passphrase = "test"
        gpg = Gpg(self.gpghome)
        gpg.create_keys(name, email, comment, passphrase)
        assert (os.path.exists(self.gpghome))

        # Check public key
        expected_uid = name + " (" + comment + ") <" + email + ">"
        created_uid = gpg.get_default_public_key()['uids'][0]
        self.assertEqual(created_uid, expected_uid)

        # Check private key
        expected_uid = name + " (" + comment + ") <" + email + ">"
        created_uid = gpg.get_default_priv_key()['uids'][0]
        self.assertEqual(created_uid, expected_uid)

        # The passphrase should be saved internally
        self.assertIsNotNone(gpg.passphrase)

    @patch('getpass.getpass')
    @patch('builtins.input')
    def test_keyring_config(self, mock_user_input, mock_getpass):
        """Test keyring configuration"""
        name = "Test"
        email = "test@test.com"
        comment = "comment"
        passphrase = "test"
        mock_user_input.side_effect = [name, email, comment]
        mock_getpass.return_value = passphrase

        gpg = Gpg(self.gpghome)

        # Before keyring config, the default keypair is empty
        self.assertIsNone(gpg.get_default_public_key())
        self.assertIsNone(gpg.get_default_priv_key())

        config_keyring(gpg)

        # Check public key
        expected_uid = name + " (" + comment + ") <" + email + ">"
        created_uid = gpg.get_default_public_key()['uids'][0]
        self.assertEqual(created_uid, expected_uid)

        # Check private key
        expected_uid = name + " (" + comment + ") <" + email + ">"
        created_uid = gpg.get_default_priv_key()['uids'][0]
        self.assertEqual(created_uid, expected_uid)

    @patch('getpass.getpass')
    @patch('builtins.input')
    def test_keyring_config_empty_passphrase(self, mock_user_input,
                                             mock_getpass):
        """Test keyring configuration"""
        name = "Test"
        email = "test@test.com"
        comment = "comment"
        passphrase = ""
        mock_user_input.side_effect = [name, email, comment]
        mock_getpass.return_value = passphrase

        gpg = Gpg(self.gpghome)

        # Before keyring config, the default keypair is empty
        self.assertIsNone(gpg.get_default_public_key())
        self.assertIsNone(gpg.get_default_priv_key())

        with self.assertRaises(RuntimeError):
            config_keyring(gpg)

        # The user keypair is not created if an empty passphrase is provided,
        # so the default keypair continues to be empty
        self.assertIsNone(gpg.get_default_public_key())
        self.assertIsNone(gpg.get_default_priv_key())

        # But the blocksat pubkey should have been imported
        self.assertIsNotNone(gpg.get_public_key(blocksat_pubkey))

    def test_duplicate_key(self):
        """Test creation of duplicate GPG keys"""
        name = "Test"
        email = "test@test.com"
        comment = "comment"
        passphrase = "test"
        gpg = Gpg(self.gpghome)

        # Create keys for the first time
        gpg.create_keys(name, email, comment, passphrase)
        assert (os.path.exists(self.gpghome))

        # Try to create again
        gpg.create_keys(name, email, comment, passphrase)
        self.assertEqual(len(gpg.gpg.list_keys()), 1)

    def test_encrypt_decrypt(self):
        """Test encryption and decryption"""
        name = "Test"
        email = "test@test.com"
        comment = "comment"
        passphrase = "test"
        gpg = Gpg(self.gpghome)

        # Create keys for the first time
        gpg.create_keys(name, email, comment, passphrase)
        assert (os.path.exists(self.gpghome))

        # Original message
        data = bytes([0, 1, 2, 3])

        # Encrypt to self
        recipient = gpg.get_default_public_key()['fingerprint']
        enc_data = gpg.encrypt(data, recipient).data

        # Decryption requires the passphrase, otherwise it throws an exception
        gpg.passphrase = None  # delete the passphrase set on key creation
        with self.assertRaises(RuntimeError):
            gpg.decrypt(enc_data)

        # Provide the passphrase and decrypt
        gpg.set_passphrase(passphrase)
        dec_data = gpg.decrypt(enc_data).data

        # Check
        self.assertEqual(data, dec_data)

    def test_passphrase_validation(self):
        name = "Test"
        email = "test@test.com"
        comment = "comment"
        passphrase = "test"
        gpg = Gpg(self.gpghome)
        gpg.create_keys(name, email, comment, passphrase)

        fingerprint = gpg.get_default_priv_key()['fingerprint']
        self.assertTrue(gpg.test_passphrase(fingerprint))

        gpg.passphrase = 'wrong-passphrase'
        self.assertFalse(gpg.test_passphrase(fingerprint))

        gpg.passphrase = None
        self.assertFalse(gpg.test_passphrase(fingerprint))
