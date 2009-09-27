#!/usr/bin/env python
# -*- coding: utf-8 -*-

import simplejson
import struct
import zlib

from galaktia.protocol.model import Datagram, Message
from Crypto.Cipher import AES

class Codec(object):
    """ Encodes and decodes objects """

    def encode(self, decoded):
        raise NotImplementedError

    def decode(self, encoded):
        raise NotImplementedError

class SerializationCodec(Codec):
    """ Serializes and unserializes objects into a string representation.
        Objects can be compound as far as they consist of simple built-in
        types such as dict, list, tuple, str, unicode, int, float, etc. """

    def encode(self, decoded):
        return simplejson.dumps(decoded, separators=(',', ':'))

    def decode(self, encoded):
        return simplejson.loads(encoded)

class CompressionCodec(Codec):
    """ Compresses and decompresses strings via zlib """

    def encode(self, decoded):

        try:
            return decoded.encode('zlib')
        except zlib.error:
            raise ValueError(decoded)

    def decode(self, encoded):

        try:
            return encoded.decode('zlib')
        except zlib.error:
            raise ValueError(encoded)

class EncryptionCodec(Codec):
    """ Encrypts and decrypts strings with AES method """

    def encode(self, decoded):
        """
        :parameters:
            decoded : tuple(str, str)
                Decrypted data and encryption key

        :returns:
            tuple(str, str) with encrypted data and encryption key
        """

        message = self._prepare_message(decoded[0])
        encoded = AES.new(decoded[1], 2).encrypt(message)

        return (encoded, decoded[1])

    def decode(self, encoded):
        """
        :parameters:
            encoded : tuple(str, str)
                Encrypted data and encryption key

        :returns:
            tuple(str, str) with decrypted data and encryption key
        """

        message = self._prepare_message(encoded[0])
        decoded = AES.new(encoded[1], 2).decrypt(message)

        return (decoded, encoded[1])

    def _prepare_message(self, message):
        """
        :parameters:
            message : str
                Message to be prepared for de/encryption

        :returns:
            str with the prepared message
        """

        message_len = len(message)
        offset = message_len % 16
        if offset != 0:
            message_len += ( 16 - offset )

        return message.ljust(message_len)

class IdentifierPackerCodec(Codec):
    """ Packs an identifier (int) and data (str) into a str and viceversa """

    _struct = struct.Struct('!l')

    def encode(self, decoded):
        """
        :parameters:
            decoded : tuple(int, str)
                Tuple with identifier (int) and data(str)

        :returns:
            str packing identifier (int) and data (str)
        """
        return self._struct.pack(decoded[0]) + decoded[1]

    def decode(self, encoded):
        """
        :parameters:
            encoded : str
                String packing identifier (int) and data (str)

        :returns:
            tuple(int, str) with packing identifier and data
        """
        size = self._struct.size
        return (self._struct.unpack(encoded[:size])[0], encoded[size:])

class MultipleCodec(Codec):
    """ Applies multiple codecs iteratively """

    def __init__(self, codecs):
        self.codecs = tuple(codecs)

    def encode(self, decoded):
        for codec in codecs: # Functional programmers prefer foldr
            decoded = codec.encode(decoded)
        return decoded

    def decode(self, encoded):
        for codec in reversed(codecs): # Functional programmers prefer foldl
            encoded = codec.decode(encoded)
        return encoded

    # It would be so cool to concatenate a set of codecs using
    # MultipleCodec in order to implement an RPG game network protocol...
    # Unfortunately, there is coupling between the codecs we need,
    # so this elegant class turned out as impractical as a philosopher
    # playing football: http://www.youtube.com/watch?v=92vV3QGagck

class ProtocolCodec(MultipleCodec):
    """ Codec that converts Datagram to Message and viceversa.
        Designed for a multi-layer protocol that includes message
        serialization, encryption, session id packing and compression. """

    PUBLIC_KEY = 'g4L4kT14 rUlZ!'

    _serializer = SerializationCodec()
    _encipherer = EncryptionCodec()
    _packer = IdentifierPackerCodec()
    _compressor = CompressionCodec()

    def __init__(self, session_dao):
        self.session_dao = session_dao

    def encode(self, decoded):
        session = decoded.session
        # TODO: case: session.id == 0 (no encryption, etc.)
        key = session.secret_key if session.id else self.PUBLIC_KEY
                # or maybe: key = session.secret_key or self.PUBLIC_KEY
        serialized = self._serializer.encode(decoded)
        encrypted, key = self._encipherer.encode((serialized, key))
        packed = self._packer.encode((session.id, encrypted))
        compressed = self._compressor.encode(packed)
        host, port = session.host, session.port
        retval = Datagram(compressed, host=host, port=port)
        return retval

    def decode(self, encoded):
        packed = self._compressor.decode(encoded.data)
        session_id, encrypted = self._packer.decode(packed)
        if session_id == 0:
            host, port = encoded.host, encoded.port
            session = self.session_dao.create(host=host, port=port)
            serialized = encrypted # no encryption when session_id == 0
            data = self._serializer.decode(serialized)
            session.character_id = 0
            session.secret_key = self.PUBLIC_KEY
                    # TODO: bind character_id, secret_key, etc.
                    # by copying user data such as character and password
                    # (user_dao or character_dao needed)
        else:
            session = self.session_dao.get(session_id)
            key = session.secret_key
            serialized, key = self._encipherer.decode((encrypted, key))
            data = self._serializer.decode(serialized)
        retval = Message(session=session, **data)
        return retval
