#!/bin/bash
OMNETDEST="$HOME/Documenti/Code/Omnet/omnetpp-6.0pre11"
QUEUENETDEST="$OMNETDEST/samples/queuenet/"
MAPDEST="$OMNETDEST/images/maps/fog.png"
GAHOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
MAP="data.png"
OMNETRES="$GAHOME/omnetpp_resources"
# run GA algorithm
./ga.py
# copy files
cp $OMNETRES/* $QUEUENETDEST
cp *.ini *.ned $QUEUENETDEST
cp $MAP $MAPDEST