#!/bin/sh 
temp=`for i in {1..6}; do printf "%0.2X:" $[ $RANDOM % 0x100 ]; done `;
mac=`echo $temp | cut -c 1-17`;
sudo ifconfig $1 down;
sudo ifconfig $1 hw ether $mac;
