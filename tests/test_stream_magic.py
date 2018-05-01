""" stream_magic test suite
"""
import sys
from socket import gethostbyname
import random
import string
sys.path.append("..")
from stream_magic import discovery
from stream_magic import device


HOST = gethostbyname('cambridge')
DEVICE_OBJECT = None

def test_discover_multi():
    # test object creation
    sm_object = discovery.StreamMagic()
    assert isinstance(sm_object, discovery.StreamMagic)

    # test discovering without explicit host
    sm_devices = sm_object.discover()
    assert len(sm_devices) >= 1
    dev = sm_devices[0] # get the first data set from the list

    # simple checks for data consistency

    # IP: splitting at the dots should give us exactly 4 parts
    assert len(dev[0][0].split(".")) == 4

    # port number between 1 and 65k
    assert 0 < int(dev[0][1]) < 65536

    # server header starts with StreamMagic
    assert str(dev[1]['server']).startswith("StreamMagic")

    # location header starts with http and ends with xml
    assert str(dev[1]['location']).startswith("http")
    assert str(dev[1]['location']).lower().endswith("xml")

def test_discover_single():
    """ test discovering a user-specified host """
    global DEVICE_OBJECT
    sm_object = discovery.StreamMagic()

    # test if specifying a wrong host ip returns None
    sm_devices = sm_object.discover(host='127.255.255.255')
    assert not sm_devices

    # now try with an actual host's ip
    sm_devices = sm_object.discover(host=HOST)
    try:
        dev = sm_devices[0]
        host, port = dev[0][0:2]
        desc = dev[1]['server']
        scpdurl = dev[1]['location']
    except Exception:
        assert False

    # instantiate a StreamMagicDevice object with the data we gathered
    DEVICE_OBJECT = device.StreamMagicDevice(host, port, desc, scpdurl)
    assert isinstance(DEVICE_OBJECT, device.StreamMagicDevice)

def test_smdev_name():
    """ test assigning a random name """
    global DEVICE_OBJECT
    random_name = ''.join(random.choices(string.ascii_uppercase\
                    + string.ascii_lowercase\
                    + string.digits, k=random.randint(1,10)))
    DEVICE_OBJECT.name = random_name
    assert DEVICE_OBJECT.name == random_name

def test_get_serviceinfo():
    """ Test the services, actions and action parameters returned by the device. """
    global DEVICE_OBJECT
    dobj = DEVICE_OBJECT
    dobj._setup()
    services = dobj.get_services()

    svc_spec = 'urn:schemas-upnp-org:service:AVTransport:1'
    assert svc_spec in services

    actions = dobj.get_actions(svc_spec)
    assert 'Play' in actions

    a_params = dobj.get_action_parameters(svc_spec, 'Play')
    assert 'InstanceID' in a_params

    a_pinfo = dobj.get_parameter_info(svc_spec, 'Play', 'InstanceID')
    assert 'direction' in a_pinfo.keys()

def test_get_mute_state():
    global DEVICE_OBJECT
    dobj = DEVICE_OBJECT
    assert isinstance(dobj.get_mute_state(), bool)

def test_get_transport_state():
    global DEVICE_OBJECT
    dobj = DEVICE_OBJECT
    assert dobj.get_transport_state() in ['PLAYING', 'PAUSED', 'STOPPED']

def test_get_audio_source():
    global DEVICE_OBJECT
    dobj = DEVICE_OBJECT
    assert dobj.get_audio_source() in ['internet radio', 'media player', 'other']

def test_get_power_state():
    """ Check if get_power_state() returns 'on' """
    global DEVICE_OBJECT
    dobj = DEVICE_OBJECT
    assert dobj.get_power_state() == "on"

def test_get_current_track_info():
    global DEVICE_OBJECT
    dobj = DEVICE_OBJECT
    trinfo = dobj.get_current_track_info()
    assert set(('artist', 'trackTitle', 'albumArtURI',
                'genre', 'origTrackNo', 'album')) == set(trinfo.keys())

def test_get_preset_list():
    """ Check the preset list returned by the device. """
    global DEVICE_OBJECT
    dobj = DEVICE_OBJECT
    presets = dobj.get_preset_list()
    assert presets                  # list is not empty
    assert len(presets[0]) == 3     # list items contain 3 elements

def test_get_playback_details():
    global DEVICE_OBJECT
    dobj = DEVICE_OBJECT
    pbd = dobj.get_playback_details()
    assert set(('artist', 'format', 'state', 'stream')) == set(pbd.keys())
