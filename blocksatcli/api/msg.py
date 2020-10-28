"""API Messages"""
import sys, os, logging, time, struct, zlib
from math import ceil, floor
import zfec
from . import pkt
from .fec import Fec


logger            = logging.getLogger(__name__)
# API message header:
# Octets 0 - 254   : string with the file name
# Octet 255        : bool indicating whether the message is text
# Octets 256 - 259 : CRC32 checksum
MSG_HEADER_FORMAT = '<255sxI'
MSG_HEADER_LEN    = 255 + 1 + 4
data_formats      = ["original", "encapsulated", "encrypted", "fec_encoded"]


class ApiMsg:
    """API Message - The content sent by the user over satellite

    This class defines the content sent over satellite, which includes the
    original data array and potentially other features. For example, it could be
    the original data encapsulated on an application-layer protocol. It could
    also be the encrypted version of the original data or the encrypted version
    of the application-layer protocol structure. Moreover, it could include
    forward error correction (FEC) for extra protection to data loss over the
    lossy satellite link.

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
        assert(isinstance(data, bytes))
        assert(msg_format in data_formats), "Unknown message format"

        # Data containers
        self.data = {
            'original'     : None, # Original data, before encapsulation
            'encapsulated' : None, # After encapsulation
            'encrypted'    : None, # After encryption
            'fec_encoded'  : None  # After forward error correction
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
            assert(target in data_formats), "Unknown target container"
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
        crc32     = zlib.crc32(orig_data)
        header    = struct.pack(MSG_HEADER_FORMAT, self.filename.encode(),
                                crc32)

        self.data['encapsulated'] = header + orig_data

        logger.debug("Checksum: {:d}".format(crc32))
        logger.debug("Packed in data structure with a total of %d bytes" %(
            len(self.data['encapsulated'])))

    def decapsulate(self):
        """Decapsulate the data structure

        Unpacks the CRC32 checksum and the file name out of the header. Then,
        validates the data integrity using the checksum.

        Returns:
            Boolean indicating whether the parsing was successful

        """
        assert(self.data['encapsulated'] is not None)
        encap_data = self.data['encapsulated']

        if (len(encap_data) < MSG_HEADER_LEN):
            logger.error("Trying to decapsulate a non-encapsulated message")
            return False

        # Parse the header
        header        = struct.unpack(MSG_HEADER_FORMAT,
                                      encap_data[:MSG_HEADER_LEN])
        try:
            self.filename = header[0].rstrip(b'\0').decode()
        except UnicodeDecodeError:
            logger.error("Could not parse file name. This is likely a "
                         "non-encapsulated message.")
            return False
        in_checksum = header[1]

        # Check the integrity of the payload
        payload       = encap_data[MSG_HEADER_LEN:]
        calc_checksum = zlib.crc32(payload)

        if (calc_checksum != in_checksum):
            logger.error("Checksum (%d) does not match the header value (%d)" %(
                calc_checksum, in_checksum
            ))
            return False
        else:
            logger.info("File: %s\tChecksum: %d\tSize: %d bytes" %(
                self.filename, in_checksum, len(payload)))

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

        logger.debug("Encrypt for recipient %s" %(recipient))

        if (sign and sign != True):
            logger.debug("Sign message using key %s" %(sign))

        encrypted_obj = gpg.encrypt(data, recipient, always_trust = trust,
                                    sign = sign)
        if (not encrypted_obj.ok):
            logger.error(encrypted_obj.stderr)
            raise ValueError(encrypted_obj.status)

        self.data['encrypted'] = encrypted_obj.data
        logger.debug("Encrypted version of the data structure has %d bytes" %(
            len(self.data['encrypted'])))

    def decrypt(self, gpg):
        """Decrypt the data

        Args:
            gpg : Gpg object.

        Returns:
            True if the decryption was successful.

        """

        decrypted_data = gpg.decrypt(self.data['encrypted'])

        if (not decrypted_data.ok):
            logger.info(
                "Size: %7d bytes\t Decryption: FAILED\t" %(
                    len(self.data['encrypted'])) +
                "Not encrypted for us (%s)" %(decrypted_data.status)
            )
            return False

        # Is the message digitally signed?
        if (decrypted_data.fingerprint is not None):
            signed_by = decrypted_data.fingerprint

            # Was the signature verified?
            if decrypted_data.trust_level is not None:
                sign_str = "Signed by %s (verified w/ trust level: %s)" %(
                    signed_by, decrypted_data.trust_text
                )
            else:
                sign_str = "Signed by %s (unverified)" %(signed_by)

            unsign_str = ""
        else:
            unsign_str = "Not signed"
            sign_str = ""

        logger.info("Encrypted size: %7d bytes\t Decryption: OK    \t%s" %(
            len(self.data['encrypted']), unsign_str))
        if (len(sign_str) > 0):
            logger.info(sign_str)
        logger.info("Decrypted size: %7d bytes" %(len(str(decrypted_data))))

        # We can't know whether decrypted data is encapsulated or not. So, for
        # now, put the data into both fields. If the decrypted data is
        # encapsulated, eventually "decapsulate" will be called and will
        # overwrite the "original" data container.
        self.data['original']     = decrypted_data.data
        self.data['encapsulated'] = decrypted_data.data

        return True

    def fec_encode(self, overhead=0.1):
        """Forward error correction (FEC) encoding

        Adds overhead through FEC encoding so that the message has
        redundancy. With that, the receiver can recover the original message
        even if parts of it are missing. The amount of data that can be missing
        depends on the number of overhead FEC chunks. The latter, in turn, is
        controlled by the overhead parameter.

        This function applies FEC encoding to the highest data container level
        available. Furthermore, it generates FEC chunks that completely fill the
        maximum Blocksat Packet payload. All chunks are of equal size and the
        last chunk is padded if necessary.

        Args:
            overhead : Percentage of FEC chunks to add as overhead (rounded up).

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
        assert(self.data['fec_encoded'] is not None)

        fec = Fec()
        decoded_data = fec.decode(self.data['fec_encoded'])

        # The encoded data should be decodable at this point
        if (not decoded_data):
            raise RuntimeError("Failed to decode the FEC-encoded message")

        # We can't know whether the underlying message is encrypted or
        # encapsulated. Thus, for now, put the data into all fields. These
        # fields can be overwritten by calling "decrypt()" or "decapsulate()".
        self.data['original']     = decoded_data
        self.data['encapsulated'] = decoded_data
        self.data['encrypted']    = decoded_data

    def is_fec_decodable(self):
        """Check if the FEC-encoded data is decodable

        Returns:
            (bool) Whether the FEC-encoded data is decodable.

        """
        assert(self.data['fec_encoded'] is not None)

        fec = Fec()
        res = fec.decode(self.data['fec_encoded'])
        return res != False

    def save(self, dst_dir, target='original'):
        """Save data into a file

        Save given sequence of octets into a file with given name.

        Args:
            dst_dir : Destination directory to save the file
            target  : Target bytes array to save (original, encapsulated or
                      encrypted).

        Returns:
            Path to the downloaded file.

        """
        data = self.get_data(target)
        assert(isinstance(data, bytes))

        # Save file into a specific directory
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

        # If the file already exists, append number
        dst_file      = os.path.join(dst_dir, self.filename)
        filename, ext = os.path.splitext(self.filename)
        i_file        = 1
        while (True):
            if not os.path.exists(dst_file):
                break
            i_file  += 1
            dst_file = os.path.join(dst_dir, filename + "-" + str(i_file) + ext)

        # Write file with user data
        f = open(dst_file, 'wb')
        f.write(data)
        f.close()

        logger.info("Saved in %s." %(dst_file))
        return dst_file

    def serialize(self, target='original'):
        """Serialize data to stdout

        Args:
            target : Target bytes array to print (original, encapsulated or
                     encrypted).

        """
        data = self.get_data(target)
        assert(isinstance(data, bytes))
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()

