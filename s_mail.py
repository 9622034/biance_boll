#! /usr/bin/python
# -*- codeing = utf-8 -*-
# @Time : 2021-09-11 11:28
# @Author : yjh
# @File : mail.py
# @Software : PyCharm

import smtplib
from email.mime.text import MIMEText
from email.header import Header

auth_passport = 'iaioolviysocbfgh'


sender = '939678968@qq.com'
receiver = '939678968@qq.com'
subject = '交易情况'

def send_mail(receive_txt):
    server = smtplib.SMTP()
    server.connect('smtp.qq.com')
    server.login('939678968@qq.com', auth_passport)

    message = MIMEText(receive_txt,'plain','utf-8')
    message['Subject'] = Header(subject,'utf-8')
    server.sendmail(sender,receiver,message.as_string())

    server.quit()