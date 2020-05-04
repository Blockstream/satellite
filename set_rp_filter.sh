#!/bin/bash

if [ -z "$1" ]; then
	IF="dvb1_0"
else
	IF=$1
fi

for i in /proc/sys/net/ipv4/conf/*/rp_filter; do
    echo 1 > "$i"
done
echo 0 > /proc/sys/net/ipv4/conf/all/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/$IF/rp_filter
