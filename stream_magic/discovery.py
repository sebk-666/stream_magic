"""
DLNA Digital Media Controller implementation for Cambridge Audio
network audio players that are based on their StreamMagic platform.

This module contains the methods to discover a StreamMagic device
on the local network using IP multicast.
"""

# This is in parts based on Pavel Cherezov's dlnap.py
# (https://github.com/cherezov/dlnap.git)
# and largely inspired by Ferry Boender's tutorial at:
# https://www.electricmonk.nl/log/2016/07/05/exploring-upnp-with-python/

__version__ = '0.10'
__author__ = 'Sebastian Kaps (sebk-666)'

import socket


class StreamMagic:
    """ This is the basic StreamMagic class.
        It provides the means to discover compatible devices on the
        network (via IP multicast) and retrieve the necessary data
        needed to instantiate a StreamMagicPDevice object.
    """

    SSDP_GROUP = ("239.255.255.250", 1900)
    URN_AVTransport = "urn:schemas-upnp-org:service:AVTransport:1"
    URN_RenderingControl = "urn:schemas-upnp-org:service:RenderingControl:1"
    SSDP_ALL = "ssdp:all"
    SOAP_ENCODING = "http://schemas.xmlsoap.org/soap/encoding/"
    SOAP_ENVELOPE = "http://schemas.xmlsoap.org/soap/envelope/"

    devices = None

    def __init__(self):
        """ Initialize instance. """
        self.devices = []

    def _send_udp(self, msg):
        """ Send the specified message to the SSDP multicast group. """
        sock = socket.socket(socket.AF_INET,
                             socket.SOCK_DGRAM,
                             socket.IPPROTO_UDP)
        sock.settimeout(2)
        sock.sendto(msg, StreamMagic.SSDP_GROUP)

        replies = []

        try:
            while True:
                data, addr = sock.recvfrom(65507)
                replies.append((addr, data))
        except socket.timeout:
            pass
        return replies

    def discover(self, host=None):
        """ Send out an UDP discover message to the SSDP multicast group
            and return a list of StreamMagic devices that replied to it.

            Optional parameters:
            host='IP_addr': if specified, only include the host with the
                            specified ip address in the returned list.

            Returns a list object: [ (addr, data ), ... ] with:

            addr: (str, int) tupel with the ip address and
                    port number of the host, e.g. ('192.168.10.250', 1900)

            data: {'HEADER': 'value'} dict containing the headers
                    of the reply and their values
        """

        # Message template
        msg = \
            b'M-SEARCH * HTTP/1.1\r\n' \
            b'HOST:239.255.255.250:1900\r\n' \
            b'ST:upnp:rootdevice\r\n' \
            b'MX:2\r\n' \
            b'MAN:"ssdp:discover"\r\n' \
            b'\r\n'

        discovered_devices = []

        for (addr, data) in self._send_udp(msg):
            # Turn the response into a dict of header names and their value.
            headers = [elem.split(": ")
                       for elem in data.decode("utf-8").splitlines()[1:]]

            data = dict()

            for header in headers:
                # If we find a header without an assiciated value,
                # e.g. "EXT: ", assign an empty string instead.
                # Also: lowercase the header names
                if len(header) > 1:
                    (key, val) = str(header[0]).lower(), header[1]
                else:
                    (key, val) = (str(header[0]).lower(), '')
                data.update({key: val})

            # If the device is not a StreamMagic device, discard it.
            # If a host parameter was specified, only add the matching host
            if host:
                if addr[0] == host:
                    if (data['server'].startswith("StreamMagic")):
                        self.devices.append((addr, data))
            else:
                if addr not in [dev[0] for dev in discovered_devices]:
                    if (data['server'].startswith("StreamMagic")):
                        self.devices.append((addr, data))
        if self.devices:
            return self.devices
        return None
