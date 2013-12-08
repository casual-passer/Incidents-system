# -*- coding: utf-8 -*-
import smtplib
from email.mime.text import MIMEText
from datetime import date, timedelta

def send_email(subject, body, msg_to, msg_from = u''):
    msg = MIMEText(body.encode('utf-8'), "text/html", "utf-8")
    msg['Subject'] = subject
    msg['From'] = msg_from
    msg['To'] = msg_to
    s = smtplib.SMTP('10.133.20.3') # CHANGEME
    s.sendmail(msg_from, msg_to, msg.as_string())
    s.quit()

def today():
    return date.today()

def tomorrow():
    return date.today() + timedelta(days=1)
