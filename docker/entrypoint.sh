#!/bin/bash
set -e

#check environment variables first
[ -z $FREQ ] && { echo "specify -e FREQ=1429000000"; exit 1;}
[ -z $GAIN ] && { echo "-e GAIN=40 used by default"; export GAIN=40;}

#start vnc server if start script exist
if [ -f /vncserver.sh ]; then
  /vncserver.sh &
fi

#start actual data reception from satellite
cd /opt/satellite/grc
if [ -z "$GUI" ]
then
  ./rx.py  --freq $FREQ --gain $GAIN
else
  DISPLAY=:1 ./rx_gui.py --freq $FREQ --gain $GAIN
fi
