# This Python module (upnp.py) is adapted from UPnPy, Lightweight UPnP client
# library for Python, version 1.1.8 (4c3610f).
#
# MIT License
#
# Copyright (c) 2019 5kyc0d3r
#
# Source: https://github.com/5kyc0d3r/upnpy
import socket
import urllib.request
from urllib.parse import urlparse
from xml.dom import minidom
from functools import wraps
import urllib.error


class NotRetrievedError(Exception):
    """Custom exception for objects that have not been retrieved

    Custom object not retrieved exception class. Raised whenever a certain
    property for a device or service was not retrieved.

    """
    pass


class NotAvailableError(Exception):
    """Custom exception for when a certain URL could not be retrieved

    Custom element not retrieved exception class. Raised whenever a value
    needed to be accessed could not be retrieved from the URL.

    """
    pass


def parse_http_header(header, header_key):
    """Parse HTTP header value

    Parse the value of a specific header from a RAW HTTP response.

    :param header: String containing the RAW HTTP response and headers
    :type header: str
    :param header_key: The header name of which to extract a value from
    :type header_key: str
    :return: The value of the header
    :rtype: str

    """
    split_headers = header.split('\r\n')

    for entry in split_headers:
        header = entry.strip().split(':', 1)

        if header[0].strip().lower() == header_key.strip().lower():
            return ''.join(header[1::]).split()[0]


def make_http_request(url, data=None, headers=None):
    """Helper function for making HTTP requests

    Helper function for making HTTP requests using urllib.

    :param url: The URL to which a request should be made
    :type url: str
    :param data: Provide data for the request. Request method will be set to
                 POST if data is provided
    :type data: str
    :param headers: Provide headers to send with the request
    :type headers: dict
    :return: A urllib.Request.urlopen object
    :rtype: urllib.Request.urlopen

    """
    if not headers:
        headers = {}

    # If data is provided the request method will automatically be set to POST
    # by urllib
    request = urllib.request.Request(url, data=data, headers=headers)
    return urllib.request.urlopen(request)


def _device_description_required(func):
    """Decorator for checking whether the device description is available on a
    device.

    """
    @wraps(func)
    def wrapper(device, *args, **kwargs):
        if device.description is None:
            raise NotRetrievedError(
                'No device description retrieved for this device.')
        elif device.description == NotAvailableError:
            return
        return func(device, *args, **kwargs)

    return wrapper


class SSDPDevice:
    """Represents an SSDP device

    Object for representing an SSDP device.

    :param address: SSDP device address
    :type address: tuple
    :param response: Device discovery response data
    :type response: str

    """
    def __init__(self, address, response):
        self.address = address
        self.host = address[0]
        self.port = address[1]
        self.response = response
        self.description = None
        self.friendly_name = None
        self.type_ = None
        self.base_url = None

        self._get_description_request(parse_http_header(response, 'Location'))
        self._get_friendly_name_request()
        self._get_type_request()
        self._get_base_url_request()

    def get_friendly_name(self):
        """Get the friendly name for the device

        Gets the device's friendly name

        :return: Friendly name of the device
        :rtype: str

        """
        return self.friendly_name

    def _get_description_request(self, url):
        try:
            device_description = make_http_request(url).read()
            self.description = device_description
            return device_description.decode()

        except (urllib.error.HTTPError, urllib.error.URLError):
            self.description = NotAvailableError
            return None

    @_device_description_required
    def _get_friendly_name_request(self):
        root = minidom.parseString(self.description)
        device_friendly_name = root.getElementsByTagName(
            'friendlyName')[0].firstChild.nodeValue
        self.friendly_name = device_friendly_name
        return self.friendly_name

    @_device_description_required
    def _get_type_request(self):
        root = minidom.parseString(self.description)
        device_type = root.getElementsByTagName(
            'deviceType')[0].firstChild.nodeValue
        self.type_ = device_type
        return self.type_

    @_device_description_required
    def _get_base_url_request(self):
        location_header_value = parse_http_header(self.response, 'Location')
        header_url = urlparse(location_header_value)
        root = minidom.parseString(self.description)
        try:
            parsed_url = urlparse(
                root.getElementsByTagName('URLBase')[0].firstChild.nodeValue)

            if parsed_url.port is not None:
                base_url = '{}://{}'.format(parsed_url.scheme,
                                            parsed_url.netloc)
            else:
                base_url = '{}://{}:{}'.format(parsed_url.scheme,
                                               parsed_url.netloc,
                                               header_url.port)
        except (IndexError, AttributeError):
            base_url = '{}://{}'.format(header_url.scheme, header_url.netloc)

        self.base_url = base_url
        return base_url


class SSDPHeader:
    def __init__(self, **headers):
        """
        Example M-SEARCH header:
        ------------------------------------------------------------------------
        M-SEARCH * HTTP/1.1          SSDP method for search requests
        HOST: 239.255.255.250:1900   SSDP multicast address and port (REQUIRED)
        MAN: "ssdp:discover"         HTTP Extension Framework scope (REQUIRED)
        MX: 2                        Maximum wait time in seconds (REQUIRED)
        ST: upnp:rootdevice          Search target (REQUIRED)
        ------------------------------------------------------------------------
        """
        self.headers = {}
        self.set_headers(**headers)

        self._available_methods = ['M-SEARCH']

        self.method = None
        self.host = self.headers.get('HOST')
        self.man = self.headers.get('MAN')
        self.mx = self.headers.get('MX')
        self.st = self.headers.get('ST')

    def _check_method_required_params(self):
        if self.method == 'M-SEARCH':
            # M-SEARCH required parameters: HOST, MAN, MX, ST
            if None in [self.host, self.man, self.mx, self.st]:
                raise ValueError(
                    'M-SEARCH method requires HOST, MAN, MX and ST headers '
                    'to be set.')

    def set_method(self, method):
        method = method.upper()
        if method in self._available_methods:
            self.method = method.upper()
        else:
            raise ValueError('Method must be either' +
                             ' or '.join(self._available_methods))

    def set_header(self, name, value):
        self.headers[name.upper()] = value

    def set_headers(self, **headers):
        for key, value in headers.items():
            self.set_header(key.upper(), value)


class SSDPRequest(SSDPHeader):
    """Create and perform an SSDP request

    :param method: SSDP request method [M-SEARCH]

    """
    def __init__(self,
                 ssdp_mcast_addr='239.255.255.250',
                 ssdp_port=1900,
                 src_port=None,
                 **headers):
        super().__init__(**headers)

        self.SSDP_MCAST_ADDR = ssdp_mcast_addr
        self.SSDP_PORT = ssdp_port

        self.set_header('HOST', "{}:{}".format(self.SSDP_MCAST_ADDR,
                                               self.SSDP_PORT))

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        if (src_port is not None):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('', src_port))

    def __del__(self):
        self.socket.close()

    def m_search(self, discover_delay=2, st='ssdp:all', **headers):
        """Perform an M-SEARCH SSDP request

        Send an SSDP M-SEARCH request for finding UPnP devices on the network.

        :param discover_delay: Device discovery delay in seconds
        :type discover_delay: int
        :param st: Specify device Search Target
        :type st: str
        :param headers: Specify M-SEARCH specific headers
        :type headers: str
        :return: List of device that replied
        :rtype: list

        """
        self.set_method('M-SEARCH')

        self.set_header('MAN', '"ssdp:discover"')
        self.set_header('MX', discover_delay)
        self.set_header('ST', st)
        self.set_headers(**headers)

        self.socket.settimeout(discover_delay)

        devices = self._send_request(self._get_raw_request())

        for device in devices:
            yield device

    def _get_raw_request(self):
        """Get raw request data to send to server"""

        final_request_data = ''

        if self.method is not None:
            ssdp_start_line = '{} * HTTP/1.1'.format(self.method)
        else:
            ssdp_start_line = 'HTTP/1.1 200 OK'

        final_request_data += '{}\r\n'.format(ssdp_start_line)

        for header, value in self.headers.items():
            final_request_data += '{}: {}\r\n'.format(header, value)

        final_request_data += '\r\n'

        return final_request_data

    def _send_request(self, message):
        self.socket.sendto(message.encode(),
                           (self.SSDP_MCAST_ADDR, self.SSDP_PORT))

        devices = []

        try:
            while True:

                # UDP packet data limit is 65507 imposed by IPv4
                # https://en.wikipedia.org/wiki/User_Datagram_Protocol#Packet_structure

                response, addr = self.socket.recvfrom(65507)
                device = SSDPDevice(addr, response.decode())
                devices.append(device)
        except socket.timeout:
            pass

        return devices


class UPnP:
    """UPnP object

    A UPnP object used for device discovery

    """
    def __init__(self, src_port=None):
        self.ssdp = SSDPRequest(src_port=src_port)
        self.discovered_devices = []

    def discover(self, delay=2, **headers):
        """Find UPnP devices on the network

        Find available UPnP devices on the network by sending an M-SEARCH
        request.

        :param delay: Discovery delay, amount of time in seconds to wait for a
                      reply from devices
        :type delay: int
        :param headers: Optional headers for the request
        :return: List of discovered devices
        :rtype: list

        """

        discovered_devices = []
        for device in self.ssdp.m_search(discover_delay=delay,
                                         st='upnp:rootdevice',
                                         **headers):
            discovered_devices.append(device)

        self.discovered_devices = discovered_devices
        return self.discovered_devices
