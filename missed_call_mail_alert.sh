#! /bin/sh

USERNAME="username"
PASSWORD="password"
SPEEDPORT_IP="192.168.2.1"

INSTALL_PATH="/home/pi/missed_call_mail_alert"

cd $INSTALL_PATH


#login into speedport
/usr/bin/curl -c cookies.txt -d "Username=$USERNAME&Password=$PASSWORD" --user-agent "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:25.0) Gecko/20100101 Firefox/25.0" -k https://speedport.ip/index/login.cgi

#receive the calllist and parse them with python
/usr/bin/curl -b cookies.txt --user-agent "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:25.0) Gecko/20100101 Firefox/25.0" -k https://speedport.ip/auth/hcti_status_telanrl.php? | grep "new Array"|cut -c 30-|sed "s'\/''g"|sed "s/(//g"|sed "s/)//g"|sed "s/;//g"|sed "s/\"//g" > out.file
#logout from speedport
/usr/bin/curl -b cookies.txt --user-agent "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:25.0) Gecko/20100101 Firefox/25.0" --data "Content-Type: application/x-www-form-urlencoded Content-Type: application/x-www-form-urlencoded" https://speedport.ip/auth/logout.cgi?RequestFile=/pub/top_beenden.php -k
#remove tmp file
#rm -f cookies.txt

/usr/bin/python database.py >>/dev/null

rm -f out.file

if [ ! -d logs ]; then
 mkdir logs
fi

./pingscript.sh $SPEEDPORT_IP >logs/pingstat.log
