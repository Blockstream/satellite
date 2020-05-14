import unittest, os, shutil, gnupg
from .gpg import Gpg


class TestGpg(unittest.TestCase):
    def setUp(self):
        self.gpghome = "/tmp/.gnupg-test"

    def tearDown(self):
        shutil.rmtree(self.gpghome, ignore_errors=True)

    def test_key_creation(self):
        """Test creation of GPG keys"""
        name       = "Test"
        email      = "test@test.com"
        comment    = "comment"
        gpghome    = "/tmp/.gnupg-test"
        passphrase = "test"
        gpg = Gpg(gpghome)
        gpg.create_keys(name, email, comment, passphrase)
        assert(os.path.exists(gpghome))

        # Check public key
        expected_uid = name + " (" + comment + ") <" + email + ">"
        created_uid  = gpg.get_default_public_key()['uids'][0]
        self.assertEqual(created_uid, expected_uid)

        # Check private key
        expected_uid = name + " (" + comment + ") <" + email + ">"
        created_uid  = gpg.get_default_priv_key()['uids'][0]
        self.assertEqual(created_uid, expected_uid)

    def test_duplicate_key(self):
        """Test creation of duplicate GPG keys"""
        name       = "Test"
        email      = "test@test.com"
        comment    = "comment"
        gpghome    = "/tmp/.gnupg-test"
        passphrase = "test"
        gpg = Gpg(gpghome)

        # Create keys for the first time
        gpg.create_keys(name, email, comment, passphrase)
        assert(os.path.exists(gpghome))

        # Try to create again
        gpg.create_keys(name, email, comment, passphrase)
        self.assertEqual(len(gpg.gpg.list_keys()), 1)

    def test_encrypt_decrypt(self):
        """Test encryption and decryption"""
        name       = "Test"
        email      = "test@test.com"
        comment    = "comment"
        gpghome    = "/tmp/.gnupg-test"
        passphrase = "test"
        gpg = Gpg(gpghome)

        # Create keys for the first time
        gpg.create_keys(name, email, comment, passphrase)
        assert(os.path.exists(gpghome))

        # Original message
        data  = bytes([0,1,2,3])

        # Encrypt to self
        recipient = gpg.get_default_public_key()['fingerprint']
        enc_data  = gpg.encrypt(data, recipient).data

        # Decryption requires the passphrase, otherwise it throws exception
        with self.assertRaises(RuntimeError):
            gpg.decrypt(enc_data)

        # Provide the passphrase and decrypt
        gpg.set_passphrase(passphrase)
        dec_data = gpg.decrypt(enc_data).data

        # Check
        self.assertEqual(data, dec_data)


