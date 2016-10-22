#!/bin/bash

cd ~/missed_call_mail_alert/calllist

# backup your database
cp calllist.db calllist.db.old

# make sone scripts executable
chmod +x missed_call_mail_alert.sh
chmod +x webfrontend/server.py
chmod +x analyse.py
chmod +x database.py
chmod +x pingscript.sh
