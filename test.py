#!/usr/bin/env python3

import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'cambridgeaudio'))

player='192.168.10.36'
#player=None
from stream_magic import discovery
from stream_magic import device

smbase = discovery.StreamMagic()
sm_device = smbase.discover(host=player)

#device = dmc.DMC.discover(host=player)

def printservices():
    for svc in mydev.get_services():
        print("\nActions for service", svc)
        for act in mydev.get_actions(svc):
            print("- ", act)
            for p in mydev.get_action_parameters(svc, act):
                pinfo = mydev.get_parameter_info(svc, act, p)
                print ("---- {} ({}) ".format(p,list(pinfo.values())))


for dev in sm_device:
    host = dev[0][0]
    port = dev[0][1]
    desc = dev[1]['SERVER']
    scpdurl = dev[1]['LOCATION']
    mydev = device.StreamMagicDevice(host, port, desc, scpdurl, name="CA851N")
    mydev._setup()
    mydev.name = "Azur 851N"
    print(mydev.get_power_state())
    #print(mydev.getMute())
 #   print(mydev.getPowerState())
 #   print(mydev.getTransportState())
 #   print(mydev.getAudioSource())
 #   print(mydev.getCurrentTrackInfo())

 ## Navigator testing
 #   print("Registering Navigator")
 #   n = mydev._registerNavigator()
 #   print(n)
 #   print("Did it work? ", mydev._isRegisteredNavigator(n))
 #   print("Releasing Navigator", mydev._releaseNavigator(n))
 #   print("Did it work? ", mydev._isRegisteredNavigator(n))

    print(mydev.dev_check())
    info = mydev.get_playback_details()
    print("Artist: %s" % info['artist'])



    #mydev._printServices()

 #   printservices()


#    print(mydev.pause())
#    sleep(2)
#    print(mydev.play())