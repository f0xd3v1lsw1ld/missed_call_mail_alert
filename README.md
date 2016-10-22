# missed call mail alert

TODO: add description

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

For this project you need to install the following applications:
```
sudo apt-get update
sudo apt-get install curl
```
As runtime environment you need python in version 2.7. On the most linux desktop versions python is already installed. If not read the documentation of your liunx version how to install python.

This project was developed and tested with the raspberry pi, so this description depends on it. If you use an other board, pc etc. as server, please do the steps described for the raspberry pi with your custom server.

### Installing

To install this project you need to do the following steps.

The process of installing depends on the machine, where you will do this. This could be your desktop pc (HOST), which is not the raspberry pi or directly on the RPI. Therefor I tag the step with HOST and/or RPI depending where this should be done.

1. [HOST] [PI] Clone the repository in your home directory
   ```
   cd ~
   git clone https://github.com/f0xd3v1lsw1ld/missed_call_mail_alert.git
   ```
2. [HOST] [PI] Configuration
   - **mailbox.ini**
     inside this file you should configure your t-online account and the mail account from which the e-mail notification will be send. Furthermore you should define a comma separated list of e-mail addresses who should receive the notification
      - imap_username = your t-online mail address
      - imap_password = yout t-online login
      - smtp* = your account settings from which the e-mail notification will be send
      - to =  a comma separated list of e-mail addresses who should receive the notification
   - **missed_call_mail_alert.sh**
     This is the main script. Here you should define the IP address of your speedport and the login username and password for the website of your speedport
3. [HOST] Deployment
   If you start on your desktop you must deploy your project to your raspberry pi. For this step a working ssh account to your raspberry pi is necessary. Otherwise you can use ftp to copy all files to your rpi.
   For the deployment I prepared a script which you should run. As arguments the scripts requires your ssh login and the raspberry pi IP address. Otherwise you can define this inside the script.
   ```
   #usage: deploy.sh <IP> <username> <pssword>
   ./scripts/deploy.sh 192.168.1.100 pi raspberry
   ```
4. [RPI] First test
   open a ssh connection to your raspberry pi and go into your working copy
   ```
   $ ssh user@pi_ip
   $ cd ~/missed_call_mail_alert

   # now you should test all with running
   $ ./missed_call_mail_alert.sh
   ```
5. [RPI] setup
   **raspbmc**
   If you running raspbmc on you raspberry pi, you must activate cron jobs at first
    - Per default running cron jobs is deactivated in Raspbmc and there are two ways to activate them.
    - In the Raspbmc GUI under Programs -> Raspbmc Settings -> System Configuration -> Service Management -> Cronjob Scheduler
    - Via SSH/FTP by modifying sys.service.cron value to true the settings file under /home/<your_username>/.xbmc/userdata/addon_data/script.raspbmc.settings/settings.xml

   **setup cronjob**
   The script should be configured in that way that it connects to your speedport each 5 minutes to check if you have a new missed call.
   ```
  $ crontab -e
    */5 * * * * /home/pi/missed_call_mail_alert.sh>>/dev/null
   ```
   Now you should wait the first five minutes and the check working with
   ```
   $tail -n 20 /var/log/syslog
   May 10 23:05:01 raspbmc CRON[5413]: (pi) CMD (/home/pi/missed_call_mail_alert/missed_call_mail_alert.sh>>/dev/null)
  ```

## Built With

* at moment there are no externals used

## Usage

As add on to the mail alert this project contains a webfrontend to access the database of your missed calls.
With the frontend you can create some statistic and add a name to each number of your incomming list of calls.

To use the webfrontend you must run the follwing scripts:

**webfrontend/server.py**
A simple webserver for the webpage
**analyse.py**
A python script to access the database and to communicate with the webpage via a websocket connection

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## History

2014 Start of development and private Usage
2016 first public release

## Authors

* **f0xd3v1lsw1ld** - *Initial work* - [missed_call_mail_alert](https://github.com/f0xd3v1lsw1ld/missed_call_mail_alert.git)

## Credists

* I've read a lot of web pages which I didn't know anymore to develop this project, so thanks to everyone who share his project with the community.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
