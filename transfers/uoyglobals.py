import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.mime.text import MIMEText

smtp_server = 'smtp.york.ac.uk'
smtp_port = 25
error_from = 'do-not-reply@york.ac.uk'
error_to = 'fergus.a.mcglynn@york.ac.uk'
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

