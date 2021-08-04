#!/bin/bash
DESTDIR="$HOME/Documenti/Code/Omnet/omnetpp-6.0pre11/samples/queuenet/"
MAPDEST="$HOME/Documenti/Code/Omnet/omnetpp-6.0pre11/images/maps/fog.png"
GAHOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
MAP="data.png"
OMNETRES="$GAHOME/omnetpp_resources"
# run GA algorithm
./ga.py
# copy files
cp $OMNETRES/* $DESTDIR
cp *.ini *.ned $DESTDIR
cp $MAP $MAPDEST