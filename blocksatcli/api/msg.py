"""API Messages"""
import sys, os, logging, time, struct, zlib
from math import ceil, floor
import zfec
from . import pkt


logger            = logging.getLogger(__name__)
# API message header:
# Octets 0 - 254   : string with the file name
# Octet 255        : bool indicating whether the message is text
# Octets 256 - 259 : CRC32 checksum
MSG_HEADER_FORMAT = '<255sxI'
MSG_HEADER_LEN    = 255 + 1 + 4
data_formats      = ["original", "encapsulated", "encrypted", "fec_encoded"]
# FEC chunk header:
# Octet 0      : Chunk id
# Octets 1 - 4 : Message length
FEC_HEADER_FORMAT = '!BI'
FEC_HEADER_LEN    = 5
# Each FEC chunk goes in a single Blocksat Packet along with metadata
FEC_CHUNK_SIZE    = pkt.MAX_PAYLOAD - FEC_HEADER_LEN


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
        # Check if the data fits into 256 chunks with the chosen overhead
        data              = self.get_data()
        n_chunks          = ceil(len(data) / FEC_CHUNK_SIZE)
        n_overhead_chunks = ceil(overhead * n_chunks)
        n_fec_chunks      = n_chunks + n_overhead_chunks
        logger.debug("FEC Encoder: Original Chunks: {} / "
                     "Overhead Chunks: {}".format(n_chunks, n_overhead_chunks))
        if (n_fec_chunks >= 256):
            max_size = floor(256/(1 + overhead)) * FEC_CHUNK_SIZE
            raise ValueError("Message size is too large - max size with {} "
                             "FEC overhead is {:.2f} kB".format(
                                 overhead, max_size/(2**10)))

        # Split the original data (from the highest container level) into chunks
        chunks   = []
        for i_frag in range(n_chunks):
            # Byte range of the next chunk:
            s_byte = i_frag * FEC_CHUNK_SIZE # starting byte
            e_byte = (i_frag + 1) * FEC_CHUNK_SIZE # ending byte
            chunk  = data[s_byte:e_byte]

            # The last chunk may need zero-padding
            if (i_frag + 1 == n_chunks and len(chunk) < FEC_CHUNK_SIZE):
                chunk += bytes(FEC_CHUNK_SIZE - len(chunk))

            assert(len(chunk) == FEC_CHUNK_SIZE)
            chunks.append(chunk)

        # Generate the corresponding FEC chunks
        encoder    = zfec.Encoder(n_chunks, n_fec_chunks)
        fec_chunks = encoder.encode(chunks)

        # Form the payload to be transmitted on each Blocksat Packet. Each
        # payload contains the FEC chunk and metadata. The metadata includes the
        # chunk id and the original message length, which the receiver needs.
        payloads = []
        for i_chunk, chunk in enumerate(fec_chunks):
            metadata = struct.pack(FEC_HEADER_FORMAT, i_chunk, len(data))
            payloads.append(metadata + chunk)

        # Concatenate all payloads to form a single "API message". Later on, the
        # satellite transmitter splits this message into packets. The FEC chunks
        # are sized so that each packet derived in this process will carry
        # precisely a single FEC chunk.
        message = b""
        for payload in payloads:
            message += payload

        self.data['fec_encoded'] = message

    def fec_decode(self):
        """Forward error correction (FEC) decoding

        Try to decode the FEC-encoded message held in the internal container,
        which may be missing some parts of the original FEC-encoded message.

        Note:
            This function should be called only when the FEC-encoded object is
            decodable. Otherwise, it throws a RuntimeError exception. Use the
            "is_fec_decodable()" method before calling it.

        """
        encoded_data = self.data['fec_encoded']
        assert(encoded_data is not None)

        # The encoded data must contain an integer number of max-sized payloads,
        # although it may not contain the full FEC-encoded object (given that
        # some parts of it may have been lost)
        assert(len(encoded_data) % pkt.MAX_PAYLOAD == 0)

        # Process each payload and create a map of FEC chunks
        n_payloads = len(encoded_data) // pkt.MAX_PAYLOAD
        chunk_map  = {}
        msg_len    = None
        for i_payload in range(n_payloads):
            # Byte range of the next payload:
            s_byte  = i_payload * pkt.MAX_PAYLOAD # starting byte
            e_byte  = (i_payload + 1) * pkt.MAX_PAYLOAD # ending byte
            payload = encoded_data[s_byte:e_byte]

            # Unpack the metadata from the FEC header
            metadata = struct.unpack(FEC_HEADER_FORMAT,
                                     payload[:FEC_HEADER_LEN])
            chunk_id = metadata[0]

            # All payloads should bring the same message length
            if (msg_len is not None):
                assert(metadata[1] == msg_len)
            else:
                msg_len = metadata[1]

            # Save the FEC chunk
            chunk_map[chunk_id] = payload[FEC_HEADER_LEN:]

        logger.debug("FEC Decoder: Processed chunks: {}".format(n_payloads))

        # Number of FEC chunks required to decode the original message:
        n_chunks  = ceil(msg_len / FEC_CHUNK_SIZE)

        if (n_chunks > len(chunk_map)):
            raise RuntimeError("Insufficient number of FEC chunks")

        # FEC decoding
        decoder        = zfec.Decoder(n_chunks, 256)
        # NOTE: The hard-coded "256" represents the maximum number of chunks
        # that can be generated. The receiver does not know how many chunks the
        # sender really generated. Nevertheless, it does not need to know, as
        # long as it receives at least n_chunks (any combination of
        # n_chunks). The explanation for this requirement is that the FEC scheme
        # is a maximum distance separable (MDS) erasure code.
        chunks         = list(chunk_map.values())[:n_chunks]
        chunk_ids      = list(chunk_map.keys())[:n_chunks]
        decoded_chunks = decoder.decode(chunks, chunk_ids)

        # Concatenate the original (decoded) chunks to form the original message
        decoded_data = b""
        for chunk in decoded_chunks:
            assert(len(chunk) == FEC_CHUNK_SIZE)
            decoded_data += chunk

        # Remove any zero-padding that may have been applied to the last chunk
        decoded_data = decoded_data[:msg_len]

        # We can't know whether the underlying message is encrypted or
        # encapsulated. Thus, for now, put the data into all fields. These
        # fields can be overwritten by calling "decrypt()" or "decapsulate()".
        self.data['original']     = decoded_data
        self.data['encapsulated'] = decoded_data
        self.data['encrypted']    = decoded_data

    def is_fec_decodable(self):
        """Check if the FEC-encoded data is decodable

        Assume that it is decodable when it contains enough FEC chunks.

        Returns:
            (bool) Whether the FEC-encoded data is decodable.

        """
        encoded_data = self.data['fec_encoded']
        assert(encoded_data is not None)

        # A properly FEC-encoded object contains an integer number of max-sized
        # payloads. However, this function could be processing any type of data,
        # not necessarily FEC-encoded. Infer that the object is not decodable if
        # this formatting condition fails.
        if (len(encoded_data) % pkt.MAX_PAYLOAD != 0):
            logger.debug("Not a properly formatted FEC-encoded object")
            return False

        # Get the original message length and check that it is set consistently
        # among all payloads. Organize also the set of unique chunk ids within
        # the internal FEC-encoded data.
        n_payloads = len(encoded_data) // pkt.MAX_PAYLOAD
        chunk_ids  = set()
        msg_len    = None
        for i_payload in range(n_payloads):
            # Byte range of the next FEC header
            s_byte     = i_payload * pkt.MAX_PAYLOAD # starting byte
            e_byte     = s_byte + FEC_HEADER_LEN # ending byte
            fec_header = encoded_data[s_byte:e_byte]

            # Unpack the metadata from the FEC header
            metadata = struct.unpack(FEC_HEADER_FORMAT, fec_header)

            # Add to set of unique chunk ids
            chunk_ids.add(metadata[0])

            # If the message length is not consistent, assume this object is not
            # decodable. It could still be another type of data (not
            # FEC-encoded).
            if (msg_len is not None and metadata[1] != msg_len):
                logger.debug("Inconsistent message length on FEC chunks - "
                             "likely not FEC-encoded")
                return False
            else:
                msg_len = metadata[1]

        # Number of FEC chunks required to decode the original message:
        n_chunks = ceil(msg_len / FEC_CHUNK_SIZE)

        # Is it decodable?
        decodable = len(chunk_ids) >= n_chunks
        logger.debug("FEC object decodable: {}".format(decodable))

        return decodable

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

