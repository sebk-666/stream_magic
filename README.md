## Note: This is still a very early a work in progress version. Things will change.

# Python Package to Support Cambridge Audio Network Audio Players (Stream Magic)

This is a simple package to provide basic support for Cambridge Audio's Network Audio Players.
It currently has only been tested with the Azur 851N model, but should be compatible with other models too.
As all functions are based on the UPnP-AV (DLNA) standard, there's a good possibility that other DLNA audio players will work as well.
Though they might differ in some details, breaking stuff.

# How to use

There are two modules:

* `stream_magic.discovery` and
* `stream_magic.device`

## The `discovery` module

The `stream_magic.discovery` module's only function is to send out an IP multicast message to discover UPnP devices on the local network.
It defines a `StreamMagic` class which has only one method, `discover()`.
The `discover()` method returns a list of devices (and associated data) that were found.

Each returned list item uses the following data structure:

`[(addr, data), ...]` with

 * `addr`: a`(str, int)` tuple with the IP address and the port of a discovered device.
 * `data`: a `{header: value}` dictionary containg the device's response headers (in lower case) and their values (e.g. `location:`, `server:`)

You can add an `host=<ip address>` argument to the `discover()` method, to only return the device with the specified IP address.

The data gathered from this can be used to instantiate a `StreamMagicDevice` object.

Example usage:

```python
from stream_magic import discovery

# ip address of a known device
my_player = '192.168.12.34'

# instantiate a StreamMagic object
sm = discovery.StreamMagic()

# get a list of all UPnP devices on the local network
devices = sm.discover()

# specify an ip address to limit the list of returned devices:
# devices = sm.discover(host=my_player)


for dev in devices:
    host, port = dev[0][0:2]
    description = dev[1]['server']
    scpdurl = dev[1]['location']    # URL of the root Service Control Point Definition XML document
    print ('Found device:')
    print ('Host: %s, Port: %d, Description: %s, SCPD URL: %s' %\
            host, port, description, scpdurl)
```


## The `device` module
The `stream_magic.device` module defines a `StreamMagicDevice` class that represents a specific Stream Magic device on the local network.
A `StreamMagicDevice` object exposes a variety of methods to control the device's playback as well as retrieve information about the current state.

Continuing the above example code, you would instantiate a `StreamMagicDevice` like this:

```python

# (assuming we already ran the discovery to retrieve the necessary information)

from stream_magic import device

# create `StreamMagicDevice` object
mydevice = device.StreamMagicDevice(host, port, description, scpdurl, name="Azur851N")
```

### Methods
Complete description of the public methods exposed by a `StreamMagicDevice` object.


#### `_setup()`
This one is likely to change in the near future.
The `_setup()` method currently needs to be called once per device to populate the device object's internal data structures that hold the services offered by the device and the corresponding specifications and access data.


#### `get_services()`

Returns a list of service specifiers for services offered by the device. These would typically include:

* `urn:schemas-upnp-org:service:RenderingControl:1`
* `urn:schemas-upnp-org:service:ConnectionManager:1`
* `urn:schemas-upnp-org:service:AVTransport:1`
* etc.


#### `get_actions(service_type)`

Returns a list of actions that the specified service type (see above) supports.
Examples include `Play`, `Stop` for the `AVTransport` service or `GetMute`, `SetVolume` for the `RenderingControl` service.


#### `get_action_parameters(service_type, action)`

Returns a list of parameters for the specified service_type-action. These are basically the arguments an action requires and/or supports.


#### `get_parameter_info(service_type, action, parameter)`

Returns information about the parameter's arguments, such as the expected data type.


#### `get_mute_state()`

Returns `True` if the device is currently muted and `False` if it is not.


#### `get_transport_state()`

Returns `PLAYING`, `PAUSED` or `STOPPED` depending on the current operation of the device.


#### `trnsprt_pause()`
Pause playback.


#### `trnsprt_play()`
Start playing.


#### `trnsprt_next()` / `trnsprt_prev()`
Skip playback to the next / previous track.


#### `trnsprt_stop()`
Stop playback.


#### `get_audio_source()`
Returns either `media player`or `internet radio`, depending of the currently playing media.


#### `get_power_state()`
Returns either `ON` or `OFF`. When the device is configured for Eco-Standby, it's not receiving network packets and thus will only reply with `ON` when it's powered on.


#### `get_current_track_info()`
When the device is operating in `media player` mode (i.e. playing back files from a local server or storage device`), returns a dict with track information like artist, title, genre and also an URI pointing to the album cover image.


#### `get_preset_list()`
Returns a list containing the number and description of the device's Internet radio presets.


#### `get_current_preset()`
Returns the number and name of the currently playing preset (if any) and `None` otherwise.


#### `play_preset(number)`
Plays the preset with the specified number. Valid numbers can be retrieved with the `get_preset_list()` method.


#### `get_playback_details()`
When playing an Internet radio stream, this will return the information for the stream itself as well as the currently playing song.




