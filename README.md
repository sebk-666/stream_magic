# Python Package to Support Cambridge Audio Network Audio Players (Stream Magic)

This is a simple package to provide basic support for Cambridge Audio's Network Audio Players.
It currently has only been tested with the Azur 851N model, but should be compatible with other models too.

As all functions are based on the UPnP-AV (DLNA) standard, there's a good possibility that other DLNA audio players will work as well - however, some code changes will be required as the _discovery.discover()_ method only lists StreamMagic devices.

This is still a work in progress, so things might change.

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

#### `volume_mute(state=True)`

Mutes or unmutes the device, depending on the optional _state_ (boolean) parameter.
If omitted, _state_ defaults to _True_, which turns the mute function on.
Setting it to _False_ unmutes the device.

Note: This has no effect, if the device is not configured as pre-amplifier.

#### `get_volume_control()`

Returns _True_ if the device volume can be controlled (i.e. in pre-amp mode) and _False_ otherwise.

####  `get_volume()`

Returns the current volume level as an integer between 0..30 (for my device).

#### `get_volume_max()`

Returns the maximum volume level the device supports (which is 30 for my device).

#### `set_volume(volume)`

Set the device volume to the specified volume.
This does not do any checks for the validity of the supplied value.
In case an invalid value is supplied, the command is ignored.

#### `get_transport_state()`

Returns `PLAYING`, `PAUSED_PLAYBACK`, `STOPPED` or `TRANSITIONING` depending on the current operation of the device.
The `TRANSITIONING` state might occur during the connection establishment phase when starting playback of an internet radio source, for example.

#### `trnsprt_pause()`
Pause playback.

#### `trnsprt_play()`
Start playing.

#### `trnsprt_play_pause()`
Toggles the device operation between `Play` and `Pause`.

#### `trnsprt_next()` / `trnsprt_prev()`
Skip playback to the next / previous track.

#### `trnsprt_stop()`
Stops playback.

#### `trnsprt_seek(seek_target)`
Jumps to the position within a track specified by _seek\_target_, a string representing a time, e.g. `'0:02:34'`.

#### `get_repeat() / set_repeat(True|False)`
When the _repeat_ function is active, the playlist will be restarted at the beginning after finishing the last track.
The method `get_repeat()` will return _True_ if the _repeat_ function is currently active and _False_ if playback is set to stop after finishing the playlist.

With `set_repeat(True)` the _repeat_ function is enabled while `set_repeat(False)` turns it off.

#### `get_shuffle() / set_shuffle(True|False)`
The _shuffle_ function randomizes the playlist order when it is active.

The method `get_shuffle()` will return _True_ if the _shuffle_ function is currently active and _False_ if playback happens in the original order.

With `set_shuffle(True)` the _repeat_ function can be turned on while `set_shuffle(False)` disables it.

#### `get_audio_source()`
Returns either `media player`, `internet radio` or `other` depending of the currently playing media.

#### `get_power_state()`
Returns either `ON`, `OFF` or `IDLE`. 

When the device is configured for _ECO_ standby mode, it will not receive or answer any network packets when powered off. The device will respond with `OFF` only in the short time between issuing the power off command and the device actually turning off.

When the device is configured for _network standby_ mode, it will respond with `IDLE` when it is turned off.

#### `power_on()`
Will turn on the device, if in _network standby_ mode.

#### `power_off(power_state='OFF')`
With the optional _power\_state_ parameter set to 'OFF' (the default), turns the device completely off. If _power\_state_ is set to `IDLE`, switches to _network standby_ mode.

Note: This ignores the standby setting that is configured in the device menu.
If the device is configured for _ECO standby_ through the device menu, `power_off(power_state='IDLE')` will still only switch it in to _network standby_ mode and vice versa.

#### `get_current_track_info()`
When the device is operating in `media player` mode (i.e. playing back files from a local server or storage device`), returns a dict with track information like artist, title, genre and also an URI pointing to the album cover image, e.g.:

```python
{
  'artist': 'Calexico', 
  'trackTitle': 'Splitter', 
  'albumArtURI': 'https://example.com/640x640.jpg', 
  'genre': 'n/a', 
  'origTrackNo': '2', 
  'album': 'Algiers', 
  'currentPos': '0:00:47', 
  'trackLength': '0:03:30'
}
```

#### `get_preset_list()`
Returns a list containing the number and description of the device's Internet radio presets, e.g.:

```python
[[1, 'Preset One', False], [2, 'Preset Two', True], [3, 'Preset Three', False]]
```
The third element in each of the sub-lists is set to _True_ when this preset is currently playing and _False_ otherwise.

#### `get_current_preset()`
Returns the number and name of the currently playing preset (if any) as a dictionary and `None` otherwise, e.g.:

```python
{'num': 1, 'name': 'Preset One'}
```

#### `play_preset(number)`
Plays the preset with the specified number. Valid numbers can be retrieved with the `get_preset_list()` method.


#### `get_playback_details()`
When playing an Internet radio stream, this will return a dictionary containing information for the stream itself as well as the currently playing song, e.g.:

```python
{'state': 'Playing',
 'format': {'codec': 'MP3',
            'sample-rate': '44100',
            'vbr': '0',
            'bit-rate': '320000',
            'bit-depth': '16'},
 'artist': 'Derek And The Dominos - Layla',
 'stream': 'Psychomed: Rock & Blues'}
}
```




