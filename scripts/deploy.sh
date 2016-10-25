#!/bin/bash
#usage: deploy.sh <IP> <username> <pssword>
if [ ! $1 ] && [ ! $2 ] && [ ! $3 ]; then
  PI_IP="192.168.1.100"
  USER="pi"
  PASSWORD="raspberry"
else
  PI_IP=$1
  USER=$2
  PASSWORD=$3
fi
echo "deploy to your server with: "
echo "   server IP: "$PI_IP
echo "   username: "$USER
echo "   password: "$PASSWORD

sshpass -p $PASSWORD rsync -av --exclude *.db --exclude ".*" --exclude "./*" ../ $USER@$PI_IP:/home/$USER/missed_call_mail_alert && sshpass -p $PASSWORD ssh $USER@$PI_IP "cd /home/$USER/missed_call_mail_alert/scripts && ./after_deploy.sh $USER"
