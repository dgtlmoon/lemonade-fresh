
import smtplib
# if in docker, bind it this way
# https://stackoverflow.com/questions/31324981/how-to-access-host-port-from-docker-container
import os


def send_email(to="", subject="", message_body=""):
    sender = 'Changedetection.io fresh instance <contact@lemonade.changedetection.io>'

    message = """From: {}
Subject: {}

{}    
    """.format(sender, subject, message_body)

    # 1025 is the mailhog dev interface debugger
    smtpObj = smtplib.SMTP(os.getenv("SMTP_SERVER", 'localhost:1025'))

    try:
        smtpObj.sendmail(sender, [to,"contact@lemonade.changedetection.io"], message)

    except smtplib.SMTPException:
        print ("uhoh, couldn't send email")
        return False