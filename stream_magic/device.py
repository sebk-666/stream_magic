"""
DLNA Digital Media Controller implementation for Cambridge Audio
network audio players that are based on their StreamMagic platform.

This module contains the actual device repesentation and methods to retrieve
information from the device as well as control the device.
"""

# This is in parts based on Pavel Cherezov's dlnap.py
# (https://github.com/cherezov/dlnap.git)
# and largely inspired by Ferry Boender's tutorial at:
# https://www.electricmonk.nl/log/2016/07/05/exploring-upnp-with-python/

__version__ = '0.10'
__author__ = 'Sebastian Kaps (sebk-666)'

import urllib.request
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError
from xml.dom import minidom
from . import discovery

StreamMagic = discovery.StreamMagic()


class StreamMagicDevice:
    """ Representation of a DLNA Media Player (UPnP-AV renderer) device.
        Provides all the methods to control the device and retrieve
        information from it.
    """
    host = None  # host name or ip address of the device
    port = None  # host port to connect to
    description = None  # device description, e.g. value of SERVER: header
    location = None  # root scpd url from the LOCATION header
    _name = None  # friendly name of the device
    _pwrstate = None

    # dictionary containing mapping of service type to scpdUrl and ctrlUrl:
    # {'Service Type': {'scpdUrl': 'SCPD XML URL', 'ctrlUrl': 'Control URL'}}
    services = dict()

    # supported actions of a service
    actions = dict()

    def __init__(self, host, port, description, location, name='Unknown'):
        """ Initialize instance, fetch the root service control point
            description XML document and populate the objects data structures.

            host: host name or ip address and port of the device
            description: device description, e.g. SERVER header value
            location: root service control point definition url (LOCATION:)
        """
        self.host = host
        self.port = port
        self.description = description
        self.location = location
        self._name = name

        # fetch the root scpd xml document
        root_xml = self._get_scpd(location)

        # set self.urlBase from urlBase tag or,
        # if this is not specified, from the location parameter
        urlbase = root_xml.getElementsByTagName('urlBase')
        if urlbase:
            urlbase = self._xml_get_node_text(urlbase[0].rstrip('/'))
        else:
            urlbase = urlparse(location)
            urlbase = '%s://%s' % (urlbase.scheme, urlbase.netloc)

        for node in root_xml.getElementsByTagName('service'):
            service_type = self._xml_get_node_text(
                           node.getElementsByTagName('serviceType')[0])

            control_url = '%s%s' % (urlbase, self._xml_get_node_text(
                         node.getElementsByTagName('controlURL')[0]))

            scpd_url = '%s%s' % (urlbase, self._xml_get_node_text(
                      node.getElementsByTagName('SCPDURL')[0]))

            self.services.update({service_type: {'scpdUrl': scpd_url,
                                                 'ctrlUrl': control_url}})
        self._pwrstate = self.get_power_state()

    @property
    def name(self):
        """ Return the name of the device """
        return self._name

    @name.setter
    def name(self, new_name):
        """ set a friendly name for the device """
        self._name = new_name

    def _get_scpd(self, scpdurl=None):
        """ Download the SCPD XML file from the device and
            return it as a minidom object.
        """
        try:
            scpdurl = scpdurl or self.location
            with urllib.request.urlopen(scpdurl) as response:
                return minidom.parseString(response.read())
        except (HTTPError, URLError) as ex:
            print("Something went wrong fetching the SCPD XML file from %s"
                  % self.host, ex)
        return None
# ------ Helper Functions ------

    # this was taken from
    # https://www.electricmonk.nl/log/2016/07/05/exploring-upnp-with-python/
    def _xml_get_node_text(self, node):
        """ Return text contents of an XML node. """
        text = []
        for childNode in node.childNodes:
            if childNode.nodeType == node.TEXT_NODE:
                text.append(childNode.data)
        return ''.join(text)

    def _get_response_tag_value(self, response, tag):
        """ Return a tag's value extracted from an XML response by the device.
        """
        values = minidom.parseString(response).getElementsByTagName(tag)
        if values:
            return values[0].firstChild.nodeValue
        return 'n/a'

    def _print_services(self):
        """ Print the services that are registered for a device and the
            corresponding service control point definition (scpd) and
            control URLs.
         """
        for service in self.services:
            print("Service Type: ", service)
            print(" `-> Control Url:", self.services[service]['ctrlUrl'])
            print(" `-> SCPD Url:", self.services[service]['scpdUrl'])
            print("." * 100)

    def _get_service_data(self, service_type):
        """ If it exists, return the scpd url and control url for the
            specified service type and None otherwise.

            Parameter:
            service_type: service type string,
                        e.g. urn:schemas-upnp-org:service:AVTransport:1
        """
        if service_type in self.services:
            return {'ctrlUrl': self.services[service_type]['ctrlUrl'],
                    'scpdUrl': self.services[service_type]['scpdUrl']}
        return None

    def _send_cmd(self, action, instanceId=0,
                  service_type=StreamMagic.URN_AVTransport,
                  omitInstanceId=False, **kwargs):
        """ Execute an action (as specified in the SCPD XML) on the device.

            action: action to perform
            service_type: service type specifier,
                e.g. urn:schema-upnp-org:...); defaults to *:AVTransport:1

            Additional keyword parameters will be processed as parameters
            to the specified action and added to the SOAP request as XML
            tags accordingly.
        """

        # <InstanceID> apparently needs to be the first parameter tag
        #  but it needs to be omitted completely for certain action calls
        if omitInstanceId is True:
            params = ''
        else:
            params = '<{0}>{1}</{0}>\n'.format('InstanceID', instanceId)

        # build XML tags from the remaining kwargs
        for key in kwargs:
            params += '<{0}>{1}</{0}>\n'.format(key, kwargs[key])

        # template for the SOAP request body
        soapBody = '<?xml version="1.0" encoding="utf-8"?>\n' \
                   '<s:Envelope xmlns:s="{3}" s:encodingStyle="{0}">\n' \
                   '<s:Body>\n' \
                   '<u:{2} xmlns:u="{1}">\n' \
                   '{4}' \
                   '</u:{2}>\n' \
                   '</s:Body>\n' \
                   '</s:Envelope>\n'.format(StreamMagic.SOAP_ENCODING,
                                            service_type, action,
                                            StreamMagic.SOAP_ENVELOPE,
                                            params)

        # template for the SOAP request headers
        headers = {'SOAPACTION': u'"%s"' % (service_type + '#' + action),
                   'Host': u'%s:%s' % (self.host, self.port),
                   'Content-Type': 'text/xml; charset="utf-8"',
                   'Accept': '*/*',
                   'Content-Length': len(soapBody)}

        ctrlUrl = self._get_service_data(service_type)['ctrlUrl']

        request = urllib.request.Request(ctrlUrl, str.encode(soapBody),
                                         headers)
        try:
            response = urllib.request.urlopen(request, timeout=2)
            return response.read()
        except URLError:
            return None

    def _update_actions(self):
        """ Fill the self.actions class attribute with the services and
            associated actions retrieved from the SCPD XML documents.
        """
        for service in self.services:
            scpd_url = self.services[service]['scpdUrl']
            xml = self._get_scpd(scpd_url)

            for node in xml.getElementsByTagName('action'):
                action = self._xml_get_node_text(
                         node.getElementsByTagName('name')[0])

                for arg in node.getElementsByTagName('argument'):
                    argument = self._xml_get_node_text(
                               arg.getElementsByTagName('name')[0])

                    direction = self._xml_get_node_text(
                                arg.getElementsByTagName('direction')[0])

                    rsv = self._xml_get_node_text(
                          arg.getElementsByTagName('relatedStateVariable')[0])

                    if service not in self.actions.keys():
                        self.actions[service] = dict()

                    if action not in self.actions[service].keys():
                        self.actions[service][action] = dict()

                    self.actions[service][action][argument] = \
                        {
                            'direction': direction,
                            'relatedStateVariable': rsv,
                            'dataType': None
                        }

    def _get_position_info(self):
        """ Returns a DIDL document with meta data of the currently played
            track / track position.
        """
        response = self._send_cmd('GetPositionInfo')
        track_data = self._get_response_tag_value(response, 'TrackMetaData')
        return track_data

    def _get_protocol_info(self):
        """ Return a list of audio formats the device supports.
            List elements e.g. look like: http-get:*:audio/flac:*
        """

        svc_type = 'urn:schemas-upnp-org:service:ConnectionManager:1'
        response = self._send_cmd('GetProtocolInfo',
                                  omitInstanceId=True,
                                  service_type=svc_type)

        response = self._get_response_tag_value(response, 'Sink')
        return response.split(',')
# ------ End of Helper Functions ------

# Service Control Point Definition related methods

    def get_services(self, init=False):
        """ Return the list of service types the device supports from
            the self.actions attribute.

            init:  Set to True, to call self._update_actions() once to
                    initialize self.actions if it is still empty.
        """
        initialized = False

        if init:
            self._update_actions()
            initialized = True

        return self.actions.keys()\
            if self.actions.keys()\
            else self.get_services(init=not initialized)

    def get_actions(self, service_type):
        """ Return a list of actions defined by the specified service type.
        """
        return self.actions[service_type].keys()

    def get_action_parameters(self, service_type, action):
        """ Return the parameters for the given action that is defined by the
            specified service type.
        """
        return self.actions[service_type][action].keys()

    def get_parameter_info(self, service_type, action, parameter):
        """ Returns information about the specified parameter for
            a service type's action.
        """
        return self.actions[service_type][action][parameter]

# Transport Controls related methods

    def get_mute_state(self):
        """ Return the boolean state of the muting function of the device. """

        svc_type = 'urn:schemas-upnp-org:service:RenderingControl:1'
        response = self._send_cmd('GetMute', service_type=svc_type,
                                  Channel='Master')
        state = self._get_response_tag_value(response, 'CurrentMute')
        # The xml response contains either 0 (not muted) or 1 (muted).
        # Turn that into a boolean and return it.
        state = bool(int(state))
        return state

    def volume_mute(self, state=True):
        """ Mute (default) or unmute the device. """
        svc_type = 'urn:schemas-upnp-org:service:RenderingControl:1'
        # param order is important: Channel= before DesiredMute=
        response = self._send_cmd('SetMute', service_type=svc_type,
                                  Channel='Master', DesiredMute=int(state))
        return response

    def get_volume_control(self):
        """ Return True if the device supports volume control (pre-amp mode),
            and False otherwise.
        """
        svc_type = 'urn:UuVol-com:service:UuVolControl:5'
        response = self._send_cmd('GetVolumeControl', service_type=svc_type,
                                  omitInstanceId=True)
        return bool(int(self._get_response_tag_value(response, 'Enabled')))

    def get_volume(self):
        """ Return the current volume setting. """
        svc_type = 'urn:schemas-upnp-org:service:RenderingControl:1'
        response = self._send_cmd('GetVolume', service_type=svc_type,
                                  Channel='Master')
        volume = self._get_response_tag_value(response, 'CurrentVolume')
        return volume

    def get_volume_max(self):
        """ Return the maximum volume setting. """
        svc_type = 'urn:schemas-upnp-org:service:RenderingControl:1'
        response = self._send_cmd('GetVolumeMax', service_type=svc_type)
        return self._get_response_tag_value(response, 'CurrentVolumeMax')

    def set_volume(self, volume):
        """ Set the volume to the specified value.
            There's no check regarding the validity of the specified value.
        """
        svc_type = 'urn:schemas-upnp-org:service:RenderingControl:1'
        self._send_cmd('SetVolume', service_type=svc_type, Channel='Master',
                       DesiredVolume=volume)
        return None

    def get_transport_state(self):
        """ Return the transport state: PLAYING, STOPPED or PAUSED_PLAYBACK """
        response = self._send_cmd('GetTransportInfo')
        state = self._get_response_tag_value(response, 'CurrentTransportState')
        return state

    def trnsprt_pause(self):
        """ Pause playback. """
        response = self._send_cmd('Pause')
        return response

    def trnsprt_play(self):
        """ Start playback.  """
        # The 'Play' command returns a SOAP error when issued while the
        # device is already play back some file. So make sure to catch that.
        # Additionally, playing a stopped internet radio source results in a
        # SOAP error.
        # So implementing "play" by simulating a key press instead.
        if self.get_transport_state() != 'PLAYING':
            return self.trnsprt_play_pause()
        return None

    def trnsprt_play_pause(self):
        """ Toggle play/pause by simulating a key press. """
        svc_type = 'urn:UuVol-com:service:UuVolSimpleRemote:1'
        response = self._send_cmd('KeyPressed', Key='PLAY_PAUSE',
                                  Duration='SHORT', service_type=svc_type,
                                  omitInstanceId=True)
        return response

    def trnsprt_next(self):
        """ Skip to next track. """
        # this returns a SOAP error
        # response = self._send_cmd('Next')
        # return response
        svc_type = 'urn:UuVol-com:service:UuVolSimpleRemote:1'
        response = self._send_cmd('KeyPressed', Key='SKIP_NEXT',
                                  Duration='SHORT', service_type=svc_type,
                                  omitInstanceId=True)
        return response

    def trnsprt_prev(self, press_twice=False):
        """ Jump to the beginning of the current track.
            Supply press_twice=True argument to actually jump to
            the previous track.
        """
        # this returns a SOAP error
        # response = self._send_cmd('Previous')
        # return response
        svc_type = 'urn:UuVol-com:service:UuVolSimpleRemote:1'
        response = self._send_cmd('KeyPressed', Key='SKIP_PREVIOUS',
                                  Duration='SHORT', service_type=svc_type,
                                  omitInstanceId=True)
        if press_twice:
            self.trnsprt_prev()
        return response

    def trnsprt_stop(self):
        """ Stop playback """
        response = self._send_cmd('Stop')
        return response


# Methods to retrieve various information from the device.

    def get_audio_source(self):
        """ Return the currently selected audio source in lowercase
            (i.e. "internet radio", "media player" or "other")
            The device returns "other" if it is used as DAC.
        """
        svc_type = 'urn:UuVol-com:service:UuVolControl:5'
        response = self._send_cmd('GetAudioSource', service_type=svc_type)
        src = self._get_response_tag_value(response, 'RetAudioSourceValue')
        return src.lower()

    def get_power_state(self):
        """ Returns the power state of the device ('on', 'off' or 'idle'). """
        svc_type = 'urn:UuVol-com:service:UuVolControl:5'
        response = self._send_cmd('GetPowerState', service_type=svc_type)
        if response:
            pwstate = self._get_response_tag_value(response,
                                                   'RetPowerStateValue')
            return str(pwstate).lower()
        return None

    def get_current_track_info(self):
        """ When the audio source is "media player":
            Return a dict with meta data (artist, title, ...) for
            the currently playing track.

            When the audio source is "Internet radio" use
            get_playback_details() instead to get this information.
        """
        data = dict()
        if self.get_audio_source() == "media player":
            track_data = self._get_position_info()
            f = self._get_response_tag_value    # function alias
            data['artist'] = f(track_data, 'upnp:artist')
            data['trackTitle'] = f(track_data, 'dc:title')
            data['albumArtURI'] = f(track_data, 'upnp:albumArtURI')
            data['genre'] = f(track_data, 'upnp:genre')
            data['origTrackNo'] = f(track_data, 'upnp:originalTrackNumber')
            data['album'] = f(track_data, 'upnp:album')
        else:
            # set all fields to NOT_IMPLEMENTED to at least return some
            # syntactically correct information
            for key in ['artist', 'trackTitle', 'albumArtURI', 'genre',
                        'origTrackNo', 'album']:
                data[key] = 'NOT_IMPLEMENTED'
        return data

# Functions related to using a Navigator ID
# note: all those return only SOAP errors it an InstanceID is specified

    def _navigator_register(self):
        """ Register a navigator_id at the device and return the value. """
        svc_type = 'urn:UuVol-com:service:UuVolControl:5'
        response = self._send_cmd('RegisterNavigator', service_type=svc_type)
        navigator_id = self._get_response_tag_value(response, 'RetNavigatorId')
        return navigator_id

    def _navigator_release(self, navigator_id):
        """ Release (=invalidate) the specified navigator_id. """
        svc_type = 'urn:UuVol-com:service:UuVolControl:5'
        self._send_cmd('ReleaseNavigator',
                       NavigatorId=navigator_id,
                       omitInstanceId=True,
                       service_type=svc_type)

    def _navigator_is_registered(self, navigator_id):
        """ Check if the specified navigator_id is registered at the device.
        """
        svc_type = 'urn:UuVol-com:service:UuVolControl:5'
        response = self._send_cmd('IsRegisteredNavigatorId',
                                  NavigatorId=navigator_id,
                                  omitInstanceId=True,
                                  service_type=svc_type)
        return bool(self._get_response_tag_value(response, 'IsRegistered'))

    def _set_av_transport_uri(self, uri):
        """ Set current playback URI (media file, playlist, etc) """
        response = self._send_cmd('SetAVTransportURI',
                                  CurrentURI=uri, CurrentURIMetaData='')
        return self._get_response_tag_value(response, 'IsRegistered')

    def _get_number_of_presets(self):
        """ query the number of supported presets from the device """
        svc_type = 'urn:UuVol-com:service:UuVolControl:5'
        response = self._send_cmd('GetNumberOfPresets', service_type=svc_type)
        return self._get_response_tag_value(response,
                                            'RetNumberOfPresetsValue')

    def get_preset_list(self):
        """ Get the list of internet radio station presets

            Format is a list of lists, each containing tree elements:
            1. the preset number
            2. the station id
            3. True/False depending on if the station is currently playing
        """
        svc_type = 'urn:UuVol-com:service:UuVolControl:5'
        response = self._send_cmd('GetPresetList',
                                  Start='1',
                                  End=self._get_number_of_presets(),
                                  omitInstanceId=True,
                                  service_type=svc_type)
        presetListXML = self._get_response_tag_value(response,
                                                     'RetPresetListXML')
        presets = minidom.parseString(presetListXML)\
                         .getElementsByTagName('preset')
        presetList = []

        for p in presets:
            name = p.getElementsByTagName('title')[0].firstChild.nodeValue
            attrs = dict(p.attributes.items())
            presetNo = attrs['id']
            isPlaying = ('isPlaying' in attrs.keys())
            presetList.append([presetNo, name, isPlaying])
        return presetList

    def get_current_preset(self):
        """ Return the id and name for the current preset - or None if n/a. """
        for preset in self.get_preset_list():
            if preset[2]:
                num, name = preset[0:2]
                return {'num': num, 'name': name}
        return None

    def play_preset(self, num):
        """ Start playing the preset with the specified id """
        svc_type = 'urn:UuVol-com:service:UuVolControl:5'
        self._send_cmd('PlayPreset', NewPresetNumberValue=num,
                       omitInstanceId=True, service_type=svc_type)
        return None

    def get_playback_details(self):
        """ Return a dict with details for the currently playing Stream"""
        # if the device is not 'on', don't try to retrieve any data
        if self._pwrstate != 'on':
            return None

        # return a dict with empty string values when device is
        # still transitioning to the PLAYING state
        if self.get_transport_state() == 'TRANSITIONING':
            return {'state': '', 'format': '', 'artist': '', 'stream': ''}

        # alternative: actively wait until the state changes.
        # which can be about 5-6 seconds.
        # while self.get_transport_state() == 'TRANSITIONING':
        #     sleep(0.5)

        # register navigator id, get the playback info...
        nid = self._navigator_register()
        svc_type = 'urn:UuVol-com:service:UuVolControl:5'
        response = self._send_cmd('GetPlaybackDetails', NavigatorId=nid,
                                  omitInstanceId=True, service_type=svc_type)
        pb_details = self._get_response_tag_value(response, 'RetPlaybackXML')
        # ...and release the navigator again
        if self._navigator_is_registered(nid):
            self._navigator_release(nid)

        try:
            pbd = minidom.parseString(pb_details)\
                        .getElementsByTagName('playback-details')[0]

            state = pbd.getElementsByTagName('state')[0]\
                       .firstChild.nodeValue

            fmt = dict(pbd.getElementsByTagName('format')[0]
                          .attributes.items())

            artist = pbd.getElementsByTagName('artist')[0]\
                        .firstChild.nodeValue

            stream = pbd.getElementsByTagName('stream')[0]\
                        .getElementsByTagName('title')[0]\
                        .firstChild.nodeValue
        except IndexError:
            pass

        # example response:
        # {'state': 'Playing',
        #   'format': {'codec': 'MP3',
        #   'sample-rate': '44100',
        #   'vbr': '0',
        #   'bit-rate': '320000',
        #   'bit-depth': '16'},
        # 'artist': 'Derek And The Dominos - Layla',
        # 'stream': 'Psychomed: Rock & Blues'}
        data = {'state': state, 'format': fmt,
                'artist': artist, 'stream': stream}
        return data

# Misc methods

    def power_on(self):
        """ Power on the device.
            Only works if device is set to Network standby mode (not ECO).
        """
        svc_type = 'urn:UuVol-com:service:UuVolControl:5'
        response = self._send_cmd('SetPowerState', NewPowerStateValue='ON',
                                  service_type=svc_type, omitInstanceId=True)
        self._pwrstate = 'on'
        return response

    def power_off(self, power_state='OFF'):
        """ Power off the device. """
        if power_state not in ['OFF', 'IDLE']:
            return None
        svc_type = 'urn:UuVol-com:service:UuVolControl:5'
        response = self._send_cmd('SetPowerState',
                                  NewPowerStateValue=power_state,
                                  service_type=svc_type, omitInstanceId=True)
        self._pwrstate = power_state.lower()
        return response
