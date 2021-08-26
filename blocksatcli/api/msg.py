"""API Messages"""
import hashlib
import logging
import os
import struct
import sys
import time
import zlib

from .. import defs
from .fec import Fec

logger = logging.getLogger(__name__)
# API message header:
# Octets 0 - 254   : string with the file name
# Octet 255        : bool indicating whether the message is text
# Octets 256 - 259 : CRC32 checksum
MSG_HEADER_FORMAT = '<255sxI'
MSG_HEADER_LEN = 255 + 1 + 4
data_formats = ["original", "encapsulated", "encrypted", "fec_encoded"]


class ApiMsg:
    """API Message - The content sent by the user over satellite

    This class defines the content sent over satellite, which includes the
    original data array and potentially other features. For example, it could
    be the original data encapsulated on an application-layer protocol. It
    could also be the encrypted version of the original data or the encrypted
    version of the application-layer protocol structure. Moreover, it could
    include forward error correction (FEC) for extra protection to data loss
    over the lossy satellite link.

    """
    def __init__(self, data, msg_format="original", filename=None):
        """ApiMsg Constructor

        Args:
            data       : bytes array with the data to send through an API
                         message.
            msg_format : message format corresponding to the input data array.
                         It could be the original data ("original"), the
                         encapsulated version of the original data
                         ("encapsulated"), the encrypted version ("encrypted"),
                         or the FEC-encoded format ("fec_encoded").
            filename   : Name of the file represented by the input data, when
                         the data corresponds to a file.
        """
        assert (isinstance(data, bytes))
        assert (msg_format in data_formats), "Unknown message format"

        # Data containers
        self.data = {
            'original': None,  # Original data, before encapsulation
            'encapsulated': None,  # After encapsulation
            'encrypted': None,  # After encryption
            'fec_encoded': None  # After forward error correction
        }

        # The input data fills one of the containers:
        self.data[msg_format] = data
        logger.debug("{} message has {:d} bytes".format(
            msg_format.replace("_", " ").title(), len(data)))

        # When the file name is empty, use a timestamp:
        self.filename = filename if filename is not None else \
            time.strftime("%Y%m%d%H%M%S")
        if (filename is not None):
            logger.debug("File name: {}".format(filename))

    def get_data(self, target=None):
        """Return message data

        Returns the data corresponding to the highest data container level
        available, in order of complexity (by convention, fec_encoded >
        encrypted > encapsulated > raw original format). If the target data
        container is specified, return the corresponding data directly.

        Args:
            target : Target data container (original, encapsulated, encrypted,
                     or fec_encoded).

        """
        if target is not None:
            assert (target in data_formats), "Unknown target container"
            return self.data[target]

        # Take the highest-level container
        if self.data['fec_encoded'] is not None:
            return self.data['fec_encoded']
        elif self.data['encrypted'] is not None:
            return self.data['encrypted']
        elif self.data['encapsulated'] is not None:
            return self.data['encapsulated']
        else:
            return self.data['original']

    def get_length(self, target=None):
        """Return the message length

        Returns the length corresponding to the highest data container level
        available. If the target data container is specified, return the
        corresponding data.

        Args:
            target : Target data container (original, encapsulated, encrypted,
                     or fec_encoded).

        """
        return len(self.get_data(target))

    def encapsulate(self):
        """Encapsulate the original data

        Add a header to the data including a CRC32 checksum and the file name.

        """
        orig_data = self.data["original"]
        crc32 = zlib.crc32(orig_data)
        header = struct.pack(MSG_HEADER_FORMAT, self.filename.encode(), crc32)

        self.data['encapsulated'] = header + orig_data

        logger.debug("Checksum: {:d}".format(crc32))
        logger.debug("Packed in data structure with a total of %d bytes" %
                     (len(self.data['encapsulated'])))

    def decapsulate(self):
        """Decapsulate the data structure

        Unpacks the CRC32 checksum and the file name out of the header. Then,
        validates the data integrity using the checksum.

        Returns:
            Boolean indicating whether the parsing was successful

        """
        assert (self.data['encapsulated'] is not None)
        encap_data = self.data['encapsulated']

        if (len(encap_data) < MSG_HEADER_LEN):
            logger.error("Trying to decapsulate a non-encapsulated message")
            return False

        # Parse the header
        header = struct.unpack(MSG_HEADER_FORMAT, encap_data[:MSG_HEADER_LEN])
        try:
            self.filename = header[0].rstrip(b'\0').decode()
        except UnicodeDecodeError:
            logger.error("Could not parse file name. This is likely a "
                         "non-encapsulated message.")
            return False
        in_checksum = header[1]

        # Check the integrity of the payload
        payload = encap_data[MSG_HEADER_LEN:]
        calc_checksum = zlib.crc32(payload)

        if (calc_checksum != in_checksum):
            logger.error("Checksum (%d) does not match the header value (%d)" %
                         (calc_checksum, in_checksum))
            return False
        else:
            logger.info("File: %s\tChecksum: %d\tSize: %d bytes" %
                        (self.filename, in_checksum, len(payload)))

        self.data['original'] = payload
        return True

    def encrypt(self, gpg, recipient, sign, trust):
        """Encrypt the data

        If encapsulated data is available, encrypt that. Otherwise, encrypt the
        original data.

        Args:
            gpg        : Gpg object.
            recipient  : Public key fingerprint of the desired recipient.
            sign       : GPG sign parameter: True to sign with the default key,
                         False to skip signing, or a fingerprint with the key
                         to use for signing.
            trust      : Skip key validation.


        """
        data = self.data['encapsulated'] if self.data['encapsulated'] \
            else self.data['original']

        logger.debug("Encrypt for recipient %s" % (recipient))

        if (sign and sign is not True):
            logger.debug("Sign message using key %s" % (sign))

        encrypted_obj = gpg.encrypt(data,
                                    recipient,
                                    always_trust=trust,
                                    sign=sign)
        if (not encrypted_obj.ok):
            logger.error(encrypted_obj.stderr)
            raise ValueError(encrypted_obj.status)

        self.data['encrypted'] = encrypted_obj.data
        logger.debug("Encrypted version of the data structure has %d bytes" %
                     (len(self.data['encrypted'])))

    def decrypt(self, gpg, signer_filter=None):
        """Decrypt the data

        Args:
            gpg           : Gpg object.
            signer_filter : Fingerprint of a target signer. If the message is
                            not signed by this fingerprint, drop it.

        Returns:
            True if the decryption was successful.

        """

        decrypted_data = gpg.decrypt(self.data['encrypted'])

        if (not decrypted_data.ok):
            logger.info("Size: %7d bytes\t Decryption: FAILED\t" %
                        (len(self.data['encrypted'])) +
                        "Not encrypted for us (%s)" % (decrypted_data.status))
            return False

        # Is the message digitally signed?
        if (decrypted_data.fingerprint is not None):
            signed_by = decrypted_data.fingerprint
            verified = decrypted_data.trust_level is not None
            sign_str_short = "Signed"

            if verified:
                sign_str_long = \
                    "Signed by %s (verified w/ trust level: %s)" % (
                        signed_by, decrypted_data.trust_text)
            else:
                sign_str_long = "Signed by %s (unverified)" % (signed_by)
        else:
            sign_str_short = "Unsigned"
            sign_str_long = ""
            signed_by = None
            verified = False

        logger.info("Encrypted size: %7d bytes\t Decryption: OK    \t%s" %
                    (len(self.data['encrypted']), sign_str_short))

        if (len(sign_str_long) > 0):
            logger.info(sign_str_long)

        if (signer_filter is not None):
            if (not signed_by):
                logger.warning("Dropping message - not signed")
                return False

            if (signer_filter != signed_by):
                logger.warning("Dropping message - not signed by the selected "
                               "sender")
                return False

            if (decrypted_data.trust_level < decrypted_data.TRUST_FULLY):
                logger.warning("Dropping message - signature unverified")
                return False

        logger.info("Decrypted size: %7d bytes" % (len(str(decrypted_data))))

        # We can't know whether decrypted data is encapsulated or not. So, for
        # now, put the data into both fields. If the decrypted data is
        # encapsulated, eventually "decapsulate" will be called and will
        # overwrite the "original" data container.
        self.data['original'] = decrypted_data.data
        self.data['encapsulated'] = decrypted_data.data

        return True

    def clearsign(self, gpg, sign_key):
        """Clearsign the data

        Unlike the other methods in this class, this method overwrites the
        original data container. The rationale is that, in this case, the
        actual message to be delivered to the recipient becomes the clearsigned
        one, including the signature.

        This method should be used in plaintext mode only. In contrast, in
        encryption mode, the signature should be enabled on the call to method
        "encrypt" instead.

        Args:
            gpg      : Gpg object.
            sign_key : Fingerprint to use for signing. If set to None, try with
                       the first private key on the keyring.

        """
        data = self.data['original']

        logger.debug("Sign message using key %s" % (sign_key))

        signed_obj = gpg.sign(data, sign_key)

        logger.debug("Signed version of the data structure has %d bytes" %
                     (len(signed_obj.data)))

        self.data['original'] = signed_obj.data

    def verify(self, gpg, signer):
        """Verify signed (but non-encrypted) message from target signer

        Detects whether the clearsigned plaintext messages comes from the
        specified signer. In the positive case, overwrite the "original" data
        container with the underlying data, excluding the signature. In other
        words, if the verification is succesful, remove the signature and leave
        the data only.

        Args:
            gpg    : Gpg object.
            signer : Fingerprint of a target signer.

        Returns:
            (bool) Whether the message is signed by the target signer.

        """
        assert (signer is not None)

        verif_obj = gpg.gpg.verify(self.data['original'])
        verified = verif_obj.trust_level is not None
        signed_by = verif_obj.fingerprint

        if (not signed_by):
            logger.info("Dropping message - not signed")
            return False

        if (signed_by != signer):
            logger.info("Dropping message - not signed by the selected "
                        "sender")
            return False

        if (not verified):
            logger.info("Dropping message - signature unverified")
            return False

        logger.info("Signed by {} (verified w/ trust level: {})".format(
            signed_by, verif_obj.trust_text))

        if (verif_obj.trust_level < verif_obj.TRUST_FULLY):
            logger.warning("Dropping message - signature unverified")
            return False

        # The signature has been verified. However, verif_obj does not return
        # the original data. In this case, gpg.decrypt() can be used to get the
        # original data, even though this is not strictly a decryption. In this
        # case, decrypted_data.ok returns false, but the data becomes available
        # on decrypted_data.data (although with a '\n' in the end).
        decrypted_data = gpg.decrypt(self.data['original'])
        assert (verif_obj.fingerprint == decrypted_data.fingerprint)
        assert (verif_obj.trust_level == decrypted_data.trust_level)
        assert (decrypted_data.data[-1] == ord('\n'))
        self.data['original'] = decrypted_data.data[:-1]

        return True

    def fec_encode(self, overhead=0.1):
        """Forward error correction (FEC) encoding

        Adds overhead through FEC encoding so that the message has
        redundancy. With that, the receiver can recover the original message
        even if parts of it are missing. The amount of data that can be missing
        depends on the number of overhead FEC chunks. The latter, in turn, is
        controlled by the overhead parameter.

        This function applies FEC encoding to the highest data container level
        available. Furthermore, it generates FEC chunks that completely fill
        the maximum Blocksat Packet payload. All chunks are of equal size and
        the last chunk is padded if necessary.

        Args:
            overhead : Percentage of the FEC chunks to add as overhead
                       (rounded up).

        """
        fec = Fec(overhead)
        self.data['fec_encoded'] = fec.encode(self.get_data())

    def fec_decode(self):
        """Forward error correction (FEC) decoding

        Try to decode the FEC-encoded message held in the internal container,
        which may be missing some parts of the original FEC-encoded message.

        Note:
            This function should be called only when the FEC-encoded object is
            decodable. Otherwise, it throws a RuntimeError exception. Use the
            "is_fec_decodable()" method before calling it.

        """
        assert (self.data['fec_encoded'] is not None)

        fec = Fec()
        decoded_data = fec.decode(self.data['fec_encoded'])

        # The encoded data should be decodable at this point
        if (not decoded_data):
            raise RuntimeError("Failed to decode the FEC-encoded message")

        # We can't know whether the underlying message is encrypted or
        # encapsulated. Thus, for now, put the data into all fields. These
        # fields can be overwritten by calling "decrypt()" or "decapsulate()".
        self.data['original'] = decoded_data
        self.data['encapsulated'] = decoded_data
        self.data['encrypted'] = decoded_data

    def is_fec_decodable(self):
        """Check if the FEC-encoded data is decodable

        Returns:
            (bool) Whether the FEC-encoded data is decodable.

        """
        assert (self.data['fec_encoded'] is not None)

        fec = Fec()
        res = fec.decode(self.data['fec_encoded'])
        return res is not False

    def save(self, dst_dir, target='original'):
        """Save data into a file

        Save the data of a specified container into a file. Name the file
        according to the filename attribute of this class.

        If another file with the same name and different contents already
        exists in the download directory, save the data on a new file with an
        appended number (e.g., "-2", "-3", and so on). Meanwhile, if a file
        with the same name exists and its contents are also the same as the
        incoming data, do not proceed with the saving.

        Args:
            dst_dir : Destination directory to save the file
            target  : Target bytes array to save (original, encapsulated or
                      encrypted).

        Returns:
            Path to the downloaded file. If the file already exists, return the
            path to the pre-existing file regardless.

        """
        data = self.get_data(target)
        assert (isinstance(data, bytes))

        # Save file into a specific directory
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

        # If the file already exists, check if it has the same contents as the
        # data array to be saved. Return in the positive case (no need to save
        # it again).
        dst_file = os.path.join(dst_dir, self.filename)

        if os.path.exists(dst_file):
            # sha256 hash of the existing file
            with open(dst_file, "rb") as fd:
                existing_hash = hashlib.sha256(fd.read()).hexdigest()

            # sha256 hash of the incoming data
            incoming_hash = hashlib.sha256(data).hexdigest()

            if (incoming_hash == existing_hash):
                logger.info("File {} already exists.".format(dst_file))
                return dst_file

        # At this point, if a file with the same name already exists, it can be
        # implied that it has different contents. Hence, save the incoming data
        # with the same name but an appended number.
        filename, ext = os.path.splitext(self.filename)
        i_file = 1
        while (True):
            if not os.path.exists(dst_file):
                break
            i_file += 1
            dst_file = os.path.join(dst_dir,
                                    filename + "-" + str(i_file) + ext)

        # Write file with user data
        f = open(dst_file, 'wb')
        f.write(data)
        f.close()

        logger.info("Saved at {}.".format(dst_file))
        return dst_file

    def serialize(self, target='original'):
        """Serialize data to stdout

        Args:
            target : Target bytes array to print (original, encapsulated or
                     encrypted).

        """
        data = self.get_data(target)
        assert (isinstance(data, bytes))
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()


def generate(data,
             filename=None,
             plaintext=True,
             encapsulate=False,
             sign=False,
             fec=False,
             gpg=None,
             recipient=None,
             trust=False,
             sign_key=None,
             fec_overhead=0.1):
    """Generate an API message

    Args:
        data         : Message data (bytes)
        filename     : Underlying file name if the message consists of a file.
        plaintext    : Boolean indicating plaintext mode.
        encapsulate  : Boolean indicating whether to encapsulate the data.
        sign         : Boolean indicating whether the message should be signed.
        fec          : Boolean indicating whether to enable FEC encoding.
        gpg          : Gpg object.
        recipient    : Public key fingerprint of the desired recipient.
        trust        : Skip key validation on encryption (trust the recipient).
        sign_key     : Fingerprint to use for signing.
        fec_overhead : Target FEC overhead.

    Returns:
        Message as an ApiMsg object.

    """
    if ((not plaintext or sign) and gpg is None):
        raise ValueError("Gpg object is required for encryption or signing")

    msg = ApiMsg(data, filename=filename)

    # If transmitting a plaintext message, it could still be clearsigned.
    if (plaintext and sign):
        if (sign_key):
            # Make sure the key exists
            gpg.get_priv_key(sign_key)
            sign_key = sign_key
        else:
            sign_key = gpg.get_default_priv_key()["fingerprint"]

        msg.clearsign(gpg, sign_key)

    # Pack data into structure (header + data), if enabled
    if (encapsulate):
        msg.encapsulate()

    # Encrypt, unless configured otherwise
    if (not plaintext):
        # Default to the first public key in the keyring if the recipient is
        # not defined.
        if (recipient is None):
            recipient = gpg.get_default_public_key()["fingerprint"]
            assert(recipient != defs.blocksat_pubkey), \
                "Defaul public key is not the user's public key"
        else:
            # Make sure the key exists
            gpg.get_public_key(recipient)
            recipient = recipient

        # Digital signature. If configured to sign the message without a
        # specified key, use the default key.
        if (sign):
            if (sign_key):
                # Make sure the key exists
                gpg.get_priv_key(sign_key)
                sign_cfg = sign_key
            else:
                sign_cfg = gpg.get_default_priv_key()["fingerprint"]
        else:
            sign_cfg = False

        msg.encrypt(gpg, recipient, sign_cfg, trust)

    # Forward error correction encoding
    if (fec):
        msg.fec_encode(fec_overhead)

    return msg


def decode(data,
           plaintext=True,
           decapsulate=False,
           fec=False,
           sender=None,
           gpg=None):
    """Decode an incoming API message

    Args:
        data        : Message data (bytes)
        plaintext   : Boolean indicating plaintext mode.
        decapsulate : Boolean indicating whether to encapsulate the data.
        fec         : Boolean indicating whether to try FEC decoding first.
        sender      : Fingerprint of a sender who must have signed the message.
        gpg         : Gpg object.

    Returns:
        ApiMsg if the message is succesfully decoded, None otherwise.

    """
    if ((not plaintext or sender) and gpg is None):
        raise ValueError("Gpg object is required for decryption/verification")

    if (fec):
        msg = ApiMsg(data, msg_format="fec_encoded")
        msg.fec_decode()
        data = msg.data['original']
        del msg  # after extracting the data, re-create a new ApiMsg below

    if (plaintext):
        if (decapsulate):
            # Encapsulated format, but no encryption
            msg = ApiMsg(data, msg_format="encapsulated")

            # Try to decapsulate it
            if (not msg.decapsulate()):
                return
        else:
            # Assume that the message is not encapsulated. This mode is
            # useful, e.g., for compatibility with transmissions triggered
            # from the browser at: https://blockstream.com/satellite-queue/.
            msg = ApiMsg(data, msg_format="original")

        # If filtering clearsigned messages, verify
        if (sender and not msg.verify(gpg, sender)):
            return

        logger.info("Message Size: {:d} bytes\tSaving in plaintext".format(
            msg.get_length(target='original')))

    else:
        # Cast data into ApiMsg object in encrypted form
        msg = ApiMsg(data, msg_format="encrypted")

        # Try to decrypt the data:
        if (not msg.decrypt(gpg, sender)):
            return

        # Try to decapsulate the application-layer structure if assuming it
        # is present (i.e., with "save-raw=False")
        if (decapsulate and not msg.decapsulate()):
            return

    return msg
