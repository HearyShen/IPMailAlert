# coding: utf-8
# Author: jyshen
# Contact: jiayun.shen@foxmail.com
import json
import socket
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument("-C",
                    "--config",
                    default='config.json',
                    type=str,
                    help='file path for config JSON file.')


class LocalHost:
    '''
    class LocalHost for instantiating and getting host's name and IP.
    '''
    def __init__(self, record_path='record.json'):
        # get hostname
        self.hostname = socket.gethostname()
        # get host ip
        self.ip = socket.gethostbyname(self.hostname)
        # get current timestamp
        self.time = time.time()

        try:
            with open(record_path, 'r') as record_file:
                records = json.load(record_file)
                self.last_hostname = records['hostname']
                self.last_ip = records['ip']
                self.last_time = records['time']
        except IOError:
            print(f'Initial execution at {self.hostname} ({self.ip})')
            # init as None for initial execution
            self.last_hostname = None
            self.last_ip = None
            self.last_time = None
        finally:
            # always write the lastest record
            with open(record_path, 'w') as record_file:
                records = dict()
                records['hostname'] = self.hostname
                records['ip'] = self.ip
                records['time'] = self.time
                json.dump(records, record_file)

    def getIP(self):
        return self.ip

    def getHostName(self):
        return self.hostname

    def getTime(self):
        return self.time

    def getLastIP(self):
        return self.last_ip

    def getLastHostName(self):
        return self.last_hostname

    def getLastTime(self):
        return self.last_time

    def isIPChanged(self):
        return not (self.ip == self.last_ip)

    def __str__(self):
        localtime = time.asctime(time.localtime(self.time))
        return f'{self.hostname}\t{self.ip}\t{localtime}'


class SmtpAlert:
    '''
    class SmtpAlert for sending alert mail via SMTP protocol
    '''
    def __init__(self, config_path='config.json'):
        try:
            with open(config_path, mode='r') as config_file:
                configs = json.load(config_file)
                # read in SMTP configs
                self.smtp_host = configs['smtp']['host']
                self.smtp_port = int(configs['smtp']['port'])
                self.smtp_username = configs['smtp']['username']
                self.smtp_password = configs['smtp']['password']
                # read in mail configs
                self.mail_sender = configs['mail']['sender']
                self.mail_receivers = configs['mail']['receivers']
        except BaseException as e:
            print(
                "Error in reading SmtpAlert's config.json! Please check the config file."
            )
            print(e)

    def sendIpAlert(self, localHost):
        '''
        send alert for IP change
        '''
        # third-party SMTP service
        host = self.smtp_host  # smtp server
        port = self.smtp_port  # smtp port (SMTP-over-SSL default port: 465)
        username = self.smtp_username  # username
        password = self.smtp_password  # password

        sender = self.mail_sender
        receivers = self.mail_receivers

        hostname = localHost.getHostName()
        ip = localHost.getIP()
        last_hostname = localHost.getLastHostName()
        last_ip = localHost.getLastIP()
        last_time = localHost.getLastTime()

        title = f'<h2>The IP address has changed</h2>'
        current_status = f'<p>The IP address of your host <strong>{hostname}</strong> is <strong>{ip}</strong> now.</p>'
        if last_hostname is not None and last_ip is not None and last_time is not None:
            last_status = f'<p>The expired IP address of <strong>{last_hostname}</strong> was <strong>{last_ip}</strong>, recorded at <strong>{time.asctime(time.localtime(last_time))}</strong>.</p>'
        else:
            last_status = 'This is the initial mail.'
        ending = '<br />\
                  <hr />\
                  <br />\
                  Powered by <a href="https://github.com/HearyShen/IPMailAlert" target="_blank">IPMailAlert</a>'
        
        content = title + current_status + last_status + ending
        message = MIMEText(content, 'html', 'utf-8')
        message['From'] = Header(f"{hostname}", 'utf-8')
        message['To'] = Header("Admin", 'utf-8')
        message['Subject'] = Header('New IP Alert', 'utf-8')

        try:
            smtpObj = smtplib.SMTP_SSL()
            smtpObj.connect(host, port)
            smtpObj.login(username, password)
            smtpObj.sendmail(sender, receivers, message.as_string())
            print(f"An alert mail has been sent to {receivers}.")
        except smtplib.SMTPException as e:
            print(
                "Error in sending mail! Please check your config and network.")
            print(e)
        finally:
            smtpObj.close()


if __name__ == "__main__":
    args = parser.parse_args()

    localHost = LocalHost()
    print(localHost)

    if localHost.isIPChanged():
        print('The IP is changed.')
        smtpAlert = SmtpAlert(args.config)
        smtpAlert.sendIpAlert(localHost)
    else:
        print('The IP is not changed.')
