import math
import os
import random
import shutil
import string
import unittest
from . import msg, pkt, fec
from .gpg import Gpg


class TestApi(unittest.TestCase):
    def test_encapsulation(self):
        """Test custom application-layer encapsulation/decapsulation"""
        # Original message
        data = bytes([0, 1, 2, 3])

        # ApiMsg on the Tx end (starting from the original data)
        tx_msg = msg.ApiMsg(data)

        # The original data container should be set. The others should be
        # empty.
        assert (tx_msg.data["original"] is not None)
        assert (tx_msg.data["encapsulated"] is None)
        assert (tx_msg.data["encrypted"] is None)

        # Once the data is encapsulated, it is augmented with a header
        expected_len = len(data) + msg.MSG_HEADER_LEN

        # Before the explicit call to the encapsulation function, the data
        # should remain in its original form. Check:
        self.assertTrue(len(tx_msg.get_data()) < expected_len)

        # Encapsulate on user-defined protocol
        tx_msg.encapsulate()

        # Now the encapsulated data container should be non-null too.
        assert (tx_msg.data["original"] is not None)
        assert (tx_msg.data["encapsulated"] is not None)
        assert (tx_msg.data["encrypted"] is None)

        # Get the encapsulated data
        encap_data = tx_msg.get_data()

        # Check that get_data returns the encapsulated data
        self.assertEqual(encap_data, tx_msg.data["encapsulated"])

        # Check that the header was added
        self.assertEqual(len(encap_data), expected_len)

        # ApiMsg on the Rx end (starting from the encapsulated data)
        rx_msg = msg.ApiMsg(encap_data, msg_format="encapsulated")

        # The Rx message starts with only the encapsulated container filled.
        # The other containers are empty.
        assert (rx_msg.data["original"] is None)
        assert (rx_msg.data["encapsulated"] is not None)
        assert (rx_msg.data["encrypted"] is None)

        # Decapsulate (returns True on success)
        self.assertTrue(rx_msg.decapsulate())

        # Now the original data container should be non-null too.
        assert (tx_msg.data["original"] is not None)
        assert (tx_msg.data["encapsulated"] is not None)
        assert (tx_msg.data["encrypted"] is None)

        # Under the hood, decapsulation will check integrity and parse the file
        # name.
        self.assertEqual(tx_msg.filename, rx_msg.filename)

    def test_decapsulation_of_non_encapsulated_data(self):
        """Try to decapsulate a non-encapsulated data object"""
        data = bytes([0, 1, 2, 3])
        rx_msg = msg.ApiMsg(data, msg_format="encapsulated")

        # The decapsulation should fail
        self.assertFalse(rx_msg.decapsulate())

    def test_msg_len(self):
        """Test encapsulated/encrypted lengths"""
        # Original message
        data = bytes([0, 1, 2, 3])

        # ApiMsg on the Tx end (starting from the original data)
        tx_msg = msg.ApiMsg(data)

        # Check that the data length returns the original message length
        self.assertEqual(tx_msg.get_length(), len(data))

        # Encapsulate
        tx_msg.encapsulate()

        # Check that the data length returns the encapsulated message length
        self.assertEqual(tx_msg.get_length(), len(data) + msg.MSG_HEADER_LEN)

    def _setup_gpg(self):
        """Setup a test gpg directory"""
        # Setup test gpg directory
        name = "Test"
        email = "test@test.com"
        comment = "comment"
        gpghome = "/tmp/.gnupg-test"
        passphrase = "test"
        gpg = Gpg(gpghome)
        gpg.create_keys(name, email, comment, passphrase)
        return gpg

    def _teardown_gpg(self):
        """Teardown test gpg directory"""
        gpghome = "/tmp/.gnupg-test"
        # Delete test gpg directory
        shutil.rmtree(gpghome, ignore_errors=True)

    def test_encryption(self):
        """Test encryption/decryption of API message"""
        data = bytes([0, 1, 2, 3])
        gpg = self._setup_gpg()

        # Message recipient:
        recipient = gpg.get_default_public_key()["fingerprint"]

        # Transmit message
        tx_msg = msg.ApiMsg(data)

        # The original data container should be set. The others should be
        # empty.
        assert (tx_msg.data["original"] is not None)
        assert (tx_msg.data["encapsulated"] is None)
        assert (tx_msg.data["encrypted"] is None)

        # Encrypt message
        tx_msg.encrypt(gpg, recipient, sign=False, trust=False)

        # Now the encrypted data container should be non-null too.
        assert (tx_msg.data["original"] is not None)
        assert (tx_msg.data["encapsulated"] is None)
        assert (tx_msg.data["encrypted"] is not None)

        cipher_data = tx_msg.get_data()

        # ApiMsg on the Rx end (starting from the encrypted data)
        rx_msg = msg.ApiMsg(cipher_data, msg_format="encrypted")

        # The Rx message starts with only the encrypted container filled. The
        # other containers are empty.
        assert (rx_msg.data["original"] is None)
        assert (rx_msg.data["encapsulated"] is None)
        assert (rx_msg.data["encrypted"] is not None)

        # Decrypt
        self.assertTrue(rx_msg.decrypt(gpg))

        # Now the original data container should be non-null too. Also, because
        # the decryption logic can't detect whether the data is encapsulated,
        # it fills both the original and encapsulated data containers.
        assert (rx_msg.data["original"] is not None)
        assert (rx_msg.data["encapsulated"] is not None)
        assert (rx_msg.data["encrypted"] is not None)

        # Check that the decrypted data matches the original
        self.assertEqual(rx_msg.data['original'], data)

        self._teardown_gpg()

    def test_decryption_of_unencrypted_data(self):
        """Try to decrypt a non-encrypt data object"""
        data = bytes([0, 1, 2, 3])
        gpg = self._setup_gpg()

        # ApiMsg on the Rx end (starting from the supposedly encrypted data,
        # which is actually the non-encrypted data)
        rx_msg = msg.ApiMsg(data, msg_format="encrypted")

        # Decrypt should fail
        self.assertFalse(rx_msg.decrypt(gpg))

        self._teardown_gpg()

    def test_decryption_of_signed_data(self):
        """Test decryption of a signed message with a signer filter"""
        data = bytes([0, 1, 2, 3])
        gpg = self._setup_gpg()

        # Create a second keypair
        gpg.create_keys("Test2", "test2@test.com", "", "test")

        # Define the signer and recipient as two distinct keys
        recipient = gpg.gpg.list_keys(True)[0]["fingerprint"]
        signer = gpg.gpg.list_keys(True)[1]["fingerprint"]
        assert (recipient != signer)

        # Transmit message
        tx_msg = msg.ApiMsg(data)

        # Unsigned encrypted message
        tx_msg.encrypt(gpg, recipient, sign=False, trust=False)
        rx_msg1 = msg.ApiMsg(tx_msg.get_data(), msg_format="encrypted")

        # Encrypted message signed by the actual signer of interest
        tx_msg.encrypt(gpg, recipient, sign=signer, trust=False)
        rx_msg2 = msg.ApiMsg(tx_msg.get_data(), msg_format="encrypted")

        # Encrypted message signed by another key (the recipient key)
        tx_msg.encrypt(gpg, recipient, sign=recipient, trust=False)
        rx_msg3 = msg.ApiMsg(tx_msg.get_data(), msg_format="encrypted")

        # Decryption without a sign filter should work in all cases
        self.assertTrue(rx_msg1.decrypt(gpg))
        self.assertTrue(rx_msg2.decrypt(gpg))
        self.assertTrue(rx_msg3.decrypt(gpg))

        # Decryption with a signer filter should only work for the message
        # signed by the actual signer of interest (rx_msg2)
        self.assertFalse(rx_msg1.decrypt(gpg, signer))
        self.assertTrue(rx_msg2.decrypt(gpg, signer))
        self.assertFalse(rx_msg3.decrypt(gpg, signer))

        self._teardown_gpg()

    def test_encapsulation_and_encryption(self):
        """Test encapsulation+encryption, then decryption+decapsulation"""
        data = bytes([0, 1, 2, 3])
        gpg = self._setup_gpg()

        # Message recipient:
        recipient = gpg.get_default_public_key()["fingerprint"]

        # Define original message, encapsulate, and encrypt
        tx_msg = msg.ApiMsg(data)
        tx_msg.encapsulate()
        tx_msg.encrypt(gpg, recipient, sign=False, trust=False)

        # All data containers should be non-null at this point.
        assert (tx_msg.data["original"] is not None)
        assert (tx_msg.data["encapsulated"] is not None)
        assert (tx_msg.data["encrypted"] is not None)

        # ApiMsg on the Rx end (starting from the encrypted data)
        rx_msg = msg.ApiMsg(tx_msg.get_data(), msg_format="encrypted")

        # Decrypt and decapsulate
        self.assertTrue(rx_msg.decrypt(gpg))
        self.assertTrue(rx_msg.decapsulate())

        # Again, all data containers should be non-null at this point.
        assert (rx_msg.data["original"] is not None)
        assert (rx_msg.data["encapsulated"] is not None)
        assert (rx_msg.data["encrypted"] is not None)

        # Check that the decrypted data matches the original
        self.assertEqual(rx_msg.data['original'], data)

        self._teardown_gpg()

    def test_clearsign_verification(self):
        """Test signing and verification of plaintext message"""
        data = bytes([0, 1, 2, 3])
        gpg = self._setup_gpg()

        # Create a second keypair
        gpg.create_keys("Test2", "test2@test.com", "", "test")

        # Define the signer and recipient as two distinct keys
        recipient = gpg.gpg.list_keys(True)[0]["fingerprint"]
        signer = gpg.gpg.list_keys(True)[1]["fingerprint"]
        assert (recipient != signer)

        # Original unsigned message
        tx_msg = msg.ApiMsg(data)
        rx_msg1 = msg.ApiMsg(tx_msg.get_data())

        # Clearsigned message
        tx_msg.clearsign(gpg, signer)
        rx_msg2 = msg.ApiMsg(tx_msg.get_data())

        # Clearsigned message signed by another key (the recipient key)
        tx_msg.clearsign(gpg, recipient)
        rx_msg3 = msg.ApiMsg(tx_msg.get_data())

        # The verification should filter the message signed by the actual
        # signer of interest (rx_msg2)
        self.assertFalse(rx_msg1.verify(gpg, signer))
        self.assertTrue(rx_msg2.verify(gpg, signer))
        self.assertFalse(rx_msg3.verify(gpg, signer))

        # The verifiction step should remove the signature and leave the
        # original data only
        self.assertEqual(rx_msg2.data['original'], data)

        self._teardown_gpg()

    def test_fec_encoding_decoding(self):
        """Test FEC encoding and decoding"""
        fec_overhead = 0.1

        # Random data
        n_bytes = 100000
        data = ''.join(
            random.choice(string.ascii_letters + string.digits)
            for _ in range(n_bytes)).encode()

        # Define the original message, encapsulate it, and apply FEC encoding
        tx_msg = msg.ApiMsg(data)
        tx_msg.encapsulate()
        tx_msg.fec_encode(fec_overhead)

        # Number of original and FEC overhead chunks
        n_chunks = math.ceil(len(data) / fec.CHUNK_SIZE)
        n_overhead_chunks = math.ceil(fec_overhead * n_chunks)

        # ApiMsg on the Rx end (starting from the full FEC-encoded data)
        rx_msg = msg.ApiMsg(tx_msg.get_data(), msg_format="fec_encoded")
        rx_msg.fec_decode()
        rx_msg.decapsulate()

        # Check that the decoded data matches the original
        self.assertEqual(rx_msg.data['original'], data)

        # Drop a number of chunks corresponding to the overhead chunks (the
        # maximum number that can be dropped). Then, try to decode:
        n_drop = n_overhead_chunks
        rx_msg2 = msg.ApiMsg(tx_msg.get_data()[:-(n_drop * pkt.MAX_PAYLOAD)],
                             msg_format="fec_encoded")
        rx_msg2.fec_decode()
        rx_msg2.decapsulate()

        # The decoding should still work
        self.assertTrue(rx_msg2.is_fec_decodable())
        self.assertEqual(rx_msg2.data['original'], data)

        # Drop more chunks than the decoder can tolerate
        n_drop = n_overhead_chunks + 1
        rx_msg3 = msg.ApiMsg(tx_msg.get_data()[:-(n_drop * pkt.MAX_PAYLOAD)],
                             msg_format="fec_encoded")

        # Now the decoding should fail
        self.assertFalse(rx_msg3.is_fec_decodable())
        with self.assertRaises(RuntimeError):
            rx_msg3.fec_decode()

    def test_save(self):
        """Test saving of API msg data"""
        dst_dir = "/tmp/test-api-downloads/"
        data = bytes([0, 1, 2, 3])

        # Instantiate ApiMsg object and save the data to file
        api_msg = msg.ApiMsg(data)
        api_msg.save(dst_dir)

        # Check the generated file
        dst_file = os.path.join(dst_dir, api_msg.filename)
        with open(dst_file) as fd:
            rd_data = fd.read()
        self.assertEqual(data, rd_data.encode())

        # Try saving again
        api_msg.save(dst_dir)
        dst_file2 = os.path.join(dst_dir, api_msg.filename + "-2")

        # It should not create another file, given that the existing file has
        # the same contents
        self.assertFalse(os.path.exists(dst_file2))

        # Try one more time, now with different contents
        api_msg.data['original'] = bytes([4, 5, 6, 7])
        api_msg.save(dst_dir)

        # Now it should create another file. There is a file with the same name
        # already, but the contents do not match.
        self.assertTrue(os.path.exists(dst_file2))

        # Clean up
        os.remove(dst_file)
        os.remove(dst_file2)

    def test_msg_generator_decoder_wrappers(self):
        """Test the message generation and decoding wrappers"""
        data = bytes([0, 1, 2, 3])
        fec_overhead = 0.5

        # Set up GPG keyring with two keypairs
        gpg = self._setup_gpg()
        gpg.create_keys("Test2", "test2@test.com", "", "test")
        recipient = gpg.gpg.list_keys(True)[0]["fingerprint"]
        signer = gpg.gpg.list_keys(True)[1]["fingerprint"]
        assert (recipient != signer)

        # The generator/decoder wrappers assume a plaintext and
        # non-encapsulated message by default
        msg1 = msg.ApiMsg(data)
        msg2 = msg.generate(data)
        self.assertEqual(msg1.get_data(), msg2.get_data())
        dec_msg = msg.decode(msg2.get_data())
        self.assertEqual(dec_msg.data['original'], data)

        # Plaintext encapsulated message
        msg1.encapsulate()
        msg2 = msg.generate(data, encapsulate=True)
        self.assertEqual(msg1.get_data(), msg2.get_data())
        dec_msg = msg.decode(msg2.get_data(), decapsulate=True)
        self.assertEqual(dec_msg.data['original'], data)

        # Plaintext encapsulated message with FEC encoding
        msg1.fec_encode(fec_overhead)
        msg2 = msg.generate(data,
                            encapsulate=True,
                            fec=True,
                            fec_overhead=fec_overhead)
        # NOTE: the FEC-encoded data is not necessarily repeatable. Check the
        # length only.
        self.assertEqual(msg1.get_length(), msg2.get_length())
        dec_msg = msg.decode(msg2.get_data(), decapsulate=True, fec=True)
        self.assertEqual(dec_msg.data['original'], data)

        # GPG object is required if signing/verifying or encrypting/decrypting
        with self.assertRaises(ValueError):
            msg.generate(data, plaintext=False)
        with self.assertRaises(ValueError):
            msg.generate(data, sign=True)
        with self.assertRaises(ValueError):
            msg.decode(data, plaintext=False)
        with self.assertRaises(ValueError):
            msg.decode(data, sender=signer)

        # Encrypted non-encapsulated message
        tx_msg = msg.generate(data, gpg=gpg, plaintext=False)
        rx_msg = msg.decode(tx_msg.get_data(), gpg=gpg, plaintext=False)
        self.assertEqual(rx_msg.data['original'], data)

        # Encrypted encapsulated message
        tx_msg = msg.generate(data, gpg=gpg, plaintext=False, encapsulate=True)
        rx_msg = msg.decode(tx_msg.get_data(),
                            gpg=gpg,
                            plaintext=False,
                            decapsulate=True)
        self.assertEqual(rx_msg.data['original'], data)

        # Encrypted + encapsulated + FEC-encoded message
        tx_msg = msg.generate(data,
                              gpg=gpg,
                              plaintext=False,
                              encapsulate=True,
                              fec=True,
                              fec_overhead=fec_overhead)
        rx_msg = msg.decode(tx_msg.get_data(),
                            gpg=gpg,
                            plaintext=False,
                            decapsulate=True,
                            fec=True)
        self.assertEqual(rx_msg.data['original'], data)

        # Encrypted + signed + encapsulated + FEC-encoded message
        # NOTE: decryption should only work if the sender filter matches
        tx_msg = msg.generate(data,
                              gpg=gpg,
                              plaintext=False,
                              encapsulate=True,
                              sign=True,
                              sign_key=signer,
                              fec=True,
                              fec_overhead=fec_overhead)
        rx_msg1 = msg.decode(tx_msg.get_data(),
                             gpg=gpg,
                             plaintext=False,
                             decapsulate=True,
                             fec=True,
                             sender=recipient)
        self.assertIsNone(rx_msg1)
        rx_msg2 = msg.decode(tx_msg.get_data(),
                             gpg=gpg,
                             plaintext=False,
                             decapsulate=True,
                             fec=True,
                             sender=signer)
        self.assertEqual(rx_msg2.data['original'], data)

        # Clearsigned message
        tx_msg = msg.generate(data, gpg=gpg, sign=True, sign_key=signer)
        rx_msg1 = msg.decode(tx_msg.get_data())
        self.assertNotEqual(rx_msg1.data['original'], data)
        rx_msg2 = msg.decode(tx_msg.get_data(), gpg=gpg, sender=signer)
        self.assertEqual(rx_msg2.data['original'], data)

        # Clearsigned + encapsulated message
        tx_msg = msg.generate(data,
                              encapsulate=True,
                              gpg=gpg,
                              sign=True,
                              sign_key=signer)
        rx_msg1 = msg.decode(tx_msg.get_data())
        self.assertNotEqual(rx_msg1.data['original'], data)
        rx_msg2 = msg.decode(tx_msg.get_data(), gpg=gpg, sender=signer)
        self.assertIsNone(
            rx_msg2)  # verification fails and decode returns None
        rx_msg3 = msg.decode(tx_msg.get_data(),
                             decapsulate=True,
                             gpg=gpg,
                             sender=signer)
        self.assertEqual(rx_msg3.data['original'], data)
