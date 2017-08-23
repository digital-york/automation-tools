import smtplib
import os
from email.MIMEMultipart import MIMEMultipart
from email.mime.text import MIMEText

smtp_server = 'smtp.york.ac.uk'
smtp_port = 25
error_from = 'do-not-reply@york.ac.uk'
error_to = 'rdyork-admins-group@york.ac.uk'
error_subject = 'Notification from Archivematica automation tools'

def send_email (email_from, email_to, subject, message_body):
  msg = MIMEMultipart()
  msg['From'] = email_from
  msg['To'] = email_to
  msg['Subject'] = subject
  msg.attach(MIMEText(message_body, "plain"))
  smtpObj = smtplib.SMTP(smtp_server, smtp_port)
  smtpObj.sendmail(email_from, email_to, msg.as_string())
  smtpObj.quit

def send_error_email (message_body):
  send_email(error_from, error_to, error_subject, message_body)

# given an error message, a script name and a file name, if the message is different from the file contents, email the error and write it to file
def send_error_email_once (error_message, script, error_file):
  if (error_message != ''):
    msg = "An error occurred during the Archivematica '" + script + "' cron script:\n\n"
    msg += error_message
    msg += "\nMore information might be available in the automation tools log file (currently /var/log/archivematica/automation-tools/" + script + "-output.log)"
    # check to see if this error has already been sent
    if os.path.isfile(error_file) and os.access(error_file, os.R_OK):
      with open(error_file, 'r') as content_file:
        content = content_file.read()
        if (content == msg):
          return
    # write error message to file so that we don't end up sending the same email every time this script runs
    fh = open(error_file, "w")
    fh.write(msg)
    fh.close()
    # send error message as email
    send_error_email(msg)

