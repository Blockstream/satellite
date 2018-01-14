#!/bin/bash
set -x

#check environment variables first
[ -z $FREQ ] && { echo "specify -e FREQ=1429000000"; exit 1;}
[ -z $GAIN ] && { echo "-e GAIN=40 used by default"; export GAIN=40;}

#start vnc server if start script exist
if [ -f /vncserver.sh ] && [ ! -z "$VNCPASSWORD" ]; then
  /vncserver.sh &
fi

#start actual data reception from satellite
ulimit -c unlimited
cd /opt/satellite/grc
echo "start rx"
while [ 1 ];
do
  if [ -z "$GUI" ]
  then
    # prevent stdin closing when docker-compose used
    sleep infinity | ./rx.py --freq $FREQ --gain $GAIN
  else
    DISPLAY=:1 ./rx_gui.py --freq $FREQ --gain $GAIN
  fi
  echo "rx done"
  sleep 1
done
