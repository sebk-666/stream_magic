#!/bin/sh
rsync -e ssh -auz ~/Documents/Code/Python/cambridgeaudio/cambridgeaudio/cambridgeaudio.py root@dantana.sebastian-kaps.de:/home/seb/.homeassistant/custom_components/media_player/
rsync -e ssh -auz ~/Documents/Code/Python/cambridgeaudio/cambridgeaudio/dmc.py root@dantana.sebastian-kaps.de:/home/seb/.homeassistant/python/
