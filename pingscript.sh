#!/bin/sh

# -q quiet
# -c nb of pings to perform

if [ ! $1]; then
echo "ERROR: Missing server ip"
echo "usage: ./pingscript.sh <IP>"
exit
fi


ping -q -c5 $1> /dev/null

if [ $? -eq 0 ]
then
	echo "ok"
	date +%D_%H:%M:%S
else
	echo "NOK"
	date +%D_%H:%M:%S
	reboot
fi
