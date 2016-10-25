#!/bin/bash
if [ ! $1 ] ; then
  USER="pi"
fi
cd /home/$1/missed_call_mail_alert/

# backup your database
if [ -f calllist.db ]; then
   cp calllist.db calllist.db.old
fi

# make sone scripts executable
chmod +x missed_call_mail_alert.sh
chmod +x webfrontend/server.py
chmod +x analyse.py
chmod +x database.py
chmod +x pingscript.sh
date >> deploy.txt
