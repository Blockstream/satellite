"""FEC Encoding/decoding"""
import logging
import random
import struct
from math import ceil, floor

import zfec

from . import pkt

logger = logging.getLogger(__name__)
# FEC packet header:
# Octet 0      : Object id
# Octet 1      : Number of FEC objects
# Octet 2      : Chunk id
# Octets 3 - 6 : Object length
# Octet 7      : Reserved
HEADER_FORMAT = '!BBBIx'
HEADER_LEN = 8
# Each FEC packet (chunk + metadata) should fit a single Blocksat Packet
PKT_SIZE = pkt.MAX_PAYLOAD
CHUNK_SIZE = PKT_SIZE - HEADER_LEN
MAX_FEC_CHUNKS = 256  # per FEC object
MAX_OVERHEAD = MAX_FEC_CHUNKS - 1  # see notes in Fec.encode()


class Fec:
    """Forward error correction (FEC) encoding/decoding

    This class processes *FEC packets*, i.e., the structures containing a FEC
    chunk and the associated metadata. The adopted FEC scheme is limited to 256
    chunks. Furthermore, we limit chunk sizes based on the maximum BlocksatPkt
    payload, so that one FEC packet goes in exactly one IP packet (with no
    IP-level fragmentation). Given that the maximum BlocksatPkt payload to fit
    the 1500-byte Ethernet MTU is of 1464 bytes, the FEC packets may use up to
    (256 * 1464) = 366 kBytes. This capacity is not enough to fit all messages
    of interest, potentially up to 1 MB.

    To solve the problem, the adopted scheme can encode the input message using
    multiple FEC objects. Each object encompasses up to 256 FEC chunks. Then,
    on the decoding end, the message is reconstructed once all FEC objects are
    successfully decoded.

    The scheme is as follows:

    - An *input message* is encoded through multiple *FEC objects*;
    - Each *FEC object* contains up to 256 *FEC chunks*.
    - Each *FEC chunk* goes within a single *FEC packet*. Hence, each *FEC
      object* yields up to 256 *FEC packets*.
    - The *FEC packet* encapsulates the *FEC chunk* and the following metadata:
        - FEC object id: identifies the FEC object corresponding to the chunk
          contained by the packet.
        - Number of FEC objects: informs receivers how many objects are used to
          carry the underlying message.
        - Chunk id: identifies the chunk within the given FEC object, from 0 to
          255 (inclusive).
        - Object length: the length (in bytes) corresponding to the part of the
          message carried by the current FEC object. The original message
          length is the sum of the object lengths from all FEC objects.

    The decoder first collects enough FEC chunks from all FEC objects
    pertaining to the same message. Subsequently, it can decode each FEC object
    independently and recover the original message.

    Note that the FEC packet does not carry an identification of the message.
    Hence, the FEC packet alone is not capable of identifying the packets
    pertaining to the same message. This identification is instead provided by
    the BlocksatPkt structure (see pkt.py).

    """
    def __init__(self, overhead=0.1):
        """Constructor

        Args:
            overhead : Percentage of the FEC chunks to add as overhead
                       (rounded up).
        """
        self.overhead = overhead

    def _encode_obj(self, data):
        """Encode a single FEC object

        Args:
            data : Data to encode (bytes array)

        Note:
            Unlike method encode(), this method must take a data object that
            fits within 256 chunks with overhead so that it fits into a single
            FEC object. Furthermore, while encode() returns FEC packets,
            this method returns FEC chunks.

        Returns:
            List of FEC-encoded chunks.

        """
        assert (isinstance(data, bytes))

        n_chunks = ceil(len(data) / CHUNK_SIZE)
        n_overhead_chunks = ceil(self.overhead * n_chunks)
        n_fec_chunks = n_chunks + n_overhead_chunks

        assert (n_fec_chunks <= MAX_FEC_CHUNKS)
        logger.debug("Original Chunks: {} / "
                     "Overhead Chunks: {} / "
                     "Total: {}".format(n_chunks, n_overhead_chunks,
                                        n_fec_chunks))

        # Split the given data array into chunks
        chunks = []
        for i_chunk in range(n_chunks):
            # Byte range of the next chunk:
            s_byte = i_chunk * CHUNK_SIZE  # starting byte
            e_byte = (i_chunk + 1) * CHUNK_SIZE  # ending byte
            chunk = data[s_byte:e_byte]

            # The last chunk may need zero-padding
            if (i_chunk + 1 == n_chunks and len(chunk) < CHUNK_SIZE):
                chunk += bytes(CHUNK_SIZE - len(chunk))

            assert (len(chunk) == CHUNK_SIZE)
            chunks.append(chunk)

        # Generate the corresponding FEC chunks
        encoder = zfec.Encoder(n_chunks, n_fec_chunks)
        return encoder.encode(chunks)

    def encode(self, data):
        """Encode message into FEC packets encompassing multiple FEC objects

        Generate the FEC packets (chunk + metadata) for the given message. If
        the message exceeds the capacity of one FEC object (up to 256 chunks),
        generate multiple FEC objects.

        Args:
            data : Data to encode (bytes array)

        Returns:
            Bytes array with all FEC packets serially (concatenated).

        """
        assert (isinstance(data, bytes))

        # The FEC object should contain up to 256 chunks, including the
        # original (systematic) and the overhead chunks. The original data
        # object (to be encoded) should occupy up to "256/(1 + overhead)"
        # chunks, whereas the overhead chunks should occupy "(overhead *
        # 256)/(1 + overhead)" chunks. Also, the overhead cannot be greater
        # than 255, otherwise the original data has zero chunks per object.
        assert(self.overhead <= MAX_OVERHEAD), \
            "FEC overhead exceeds the maximum of {}".format(MAX_OVERHEAD)

        max_obj_size = floor(MAX_FEC_CHUNKS / (1 + self.overhead)) * CHUNK_SIZE
        n_fec_objects = ceil(len(data) / max_obj_size)

        logger.debug("Message Size: {} / FEC Objects: {}".format(
            len(data), n_fec_objects))

        # Generate the FEC packets from (potentially) multiple FEC objects
        fec_pkts = []
        for i_obj in range(n_fec_objects):
            s_byte = i_obj * max_obj_size  # starting byte
            e_byte = (i_obj + 1) * max_obj_size  # ending byte
            fec_object = data[s_byte:e_byte]

            logger.debug("FEC Object: {}".format(i_obj))

            fec_chunks = self._encode_obj(fec_object)

            # FEC packets
            for i_chunk, chunk in enumerate(fec_chunks):
                metadata = struct.pack(HEADER_FORMAT, i_obj, n_fec_objects,
                                       i_chunk, len(fec_object))
                fec_pkts.append(metadata + chunk)

        # Concatenate all FEC packets to form a single encoded data
        # array. Concatenate them in random order so that the chunks from the
        # same object are not sent consecutively. This strategy is useful to
        # avoid error bursts.
        encoded_data = bytearray()
        random.shuffle(fec_pkts)
        for fec_pkt in fec_pkts:
            encoded_data += fec_pkt

        assert (len(encoded_data) % PKT_SIZE == 0)

        return bytes(encoded_data)

    def _decode_obj(self, obj_len, chunks, chunk_ids):
        """Decode a single FEC object

        Args:
            obj_len   : Length of the original object encoded by the FEC
                        object.
            chunks    : List of FEC chunks.
            chunk_ids : List of ids associated with the list of FEC chunks.

        Note:
            Unlike method decode(), this method processes a single encoded FEC
            object.

        Returns:
            (bytearray) with the decoded (original) data object.

        """
        # The original (uncoded) object must fit within the maximum number of
        # FEC chunks. Most of the time `obj_len` will be less than the
        # maximum. It only hits the maximum if the FEC overhead is set to zero.
        assert (obj_len <= (MAX_FEC_CHUNKS * CHUNK_SIZE))

        # Number of FEC chunks required to decode the original message:
        n_chunks = ceil(obj_len / CHUNK_SIZE)

        # FEC decoder
        decoder = zfec.Decoder(n_chunks, MAX_FEC_CHUNKS)
        # NOTE: The hard-coded "MAX_FEC_CHUNKS" represents the maximum number
        # of chunks that can be generated. The receiver does not know how many
        # chunks the sender really generated. Nevertheless, it does not need to
        # know, as long as it receives at least n_chunks (any combination of
        # n_chunks). The explanation for this requirement is that the FEC
        # scheme is a maximum distance separable (MDS) erasure code.

        # Decode using the minimum required number of FEC chunks
        decoded_chunks = decoder.decode(chunks[:n_chunks],
                                        chunk_ids[:n_chunks])

        # Concatenate the decoded chunks to form the original object
        decoded_obj = bytearray()
        for chunk in decoded_chunks:
            assert (len(chunk) == CHUNK_SIZE)
            decoded_obj += chunk

        # Remove any zero-padding that may have been applied to the last chunk:
        return decoded_obj[:obj_len]

    def _is_decodable(self, data):
        """Check if the FEC-encoded data is decodable

        Args:
            data : FEC-encoded data, a bytes array with multiple FEC packets
                   serially.

        Note: This is a faster processing tailored specifically to validate the
            given FEC-encoded data. Unlike method decode(), it does not make
            any expensive memory copying. The rationale is that the data will
            not be ready to be decoded most of the time. Hence, it is better to
            check if decodable separately than to try and decode it in one go.

        """

        # The encoded data must contain an integer number of FEC packets,
        # although it may not contain the full FEC-encoded object(s), given
        # that some parts of it may have been lost.
        if (len(data) % PKT_SIZE != 0):
            logger.debug("Not a properly formatted FEC-encoded object")
            return False

        # Process each packet and create a map of FEC objects and chunks
        n_fec_pkts = len(data) // PKT_SIZE
        fec_map = {}
        n_fec_objects = None
        for i_fec_pkt in range(n_fec_pkts):
            # Byte range of the next header (don't process the payload here):
            s_byte = i_fec_pkt * PKT_SIZE  # starting byte
            e_byte = s_byte + HEADER_LEN  # ending byte

            # Unpack the metadata from the FEC header
            metadata = struct.unpack(HEADER_FORMAT, data[s_byte:e_byte])
            obj_id = metadata[0]
            chunk_id = metadata[2]
            obj_len = metadata[3]

            # Check if the chunk id is valid
            if (chunk_id >= MAX_FEC_CHUNKS):
                logger.debug("Invalid chunk id - likely not FEC-encoded")
                return False

            # All packets of a FEC object should bring the same message length
            if (obj_id not in fec_map):
                fec_map[obj_id] = {'len': obj_len, 'n_chunks': 0}
                # NOTE: keep the count of chunks here (not the actual chunks).
            elif (obj_len != fec_map[obj_id]['len']):
                logger.debug("Inconsistent message length on FEC packets - "
                             "likely not FEC-encoded")
                return False

            # All FEC packets should bring the same metadata information
            # regarding the number of FEC objects
            if (n_fec_objects is None):
                n_fec_objects = metadata[1]
            elif (n_fec_objects != metadata[1]):
                logger.debug("Inconsistent number of FEC objects - "
                             "likely not FEC-encoded")
                return False

            # Increment the count of FEC chunks
            fec_map[obj_id]['n_chunks'] += 1

        # The decoder needs all the FEC objects
        if (n_fec_objects > len(fec_map)):
            logger.debug("Insufficient number of FEC objects")
            return False

        # All FEC objects should contain enough FEC chunks
        ready = n_fec_objects * [False]
        for i_obj in range(n_fec_objects):
            n_chunks = ceil(fec_map[i_obj]['len'] / CHUNK_SIZE)
            ready[i_obj] = fec_map[i_obj]['n_chunks'] >= n_chunks

        if (not all(ready)):
            logger.debug("Insufficient number of FEC chunks")
            return False

        logger.debug("Object decodable")

        return True

    def decode(self, data):
        """Decode a sequence of FEC packets spanning multiple FEC objects

        Args:
            data : FEC-encoded data, a bytes array with multiple FEC packets
                   serially.

        Returns:
            False if decoding fails. Otherwise, a bytes array with the decoded
            data (i.e., the original message).

        """

        # Check if the given FEC-encoded can decoded before anything to avoid
        # the more expensive message decoding that follows.
        if (not self._is_decodable(data)):
            return False

        # Process each packet and create a map of FEC objects and chunks
        n_fec_pkts = len(data) // PKT_SIZE
        fec_map = {}
        n_fec_objects = None
        for i_fec_pkt in range(n_fec_pkts):
            # Byte range of the next FEC packet:
            s_byte = i_fec_pkt * PKT_SIZE  # starting byte
            e_byte = (i_fec_pkt + 1) * PKT_SIZE  # ending byte
            fec_pkt = data[s_byte:e_byte]

            # Unpack the metadata from the FEC header
            obj_id, n_fec_objects, chunk_id, obj_len = struct.unpack(
                HEADER_FORMAT, fec_pkt[:HEADER_LEN])

            # Save the FEC object length and the FEC chunk
            if (obj_id not in fec_map):
                fec_map[obj_id] = {'len': obj_len, 'chunks': {}}

            fec_map[obj_id]['chunks'][chunk_id] = fec_pkt[HEADER_LEN:]

        logger.debug("Processed chunks: {} / Processed objects: {}".format(
            n_fec_pkts, len(fec_map)))

        # Decode multiple objects and concatenate the decoded data
        decoded_data = bytearray()
        for i_obj in range(n_fec_objects):
            decoded_data += self._decode_obj(
                fec_map[i_obj]['len'], list(fec_map[i_obj]['chunks'].values()),
                list(fec_map[i_obj]['chunks'].keys()))

        return bytes(decoded_data)
