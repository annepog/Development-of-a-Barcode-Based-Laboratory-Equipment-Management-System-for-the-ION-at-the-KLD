# test_email.py
from email_config import SENDER_EMAIL, SENDER_PASSWORD, SMTP_SERVER, SMTP_PORT
import smtplib
from email.mime.text import MIMEText

def test_email():
    try:
        msg = MIMEText("This is a test email from LEMS")
        msg['Subject'] = 'LEMS Email Test'
        msg['From'] = SENDER_EMAIL
        msg['To'] = 'acogarces@kld.edu.ph' 
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(" Email sent successfully!")
        return True
    except Exception as e:
        print(f" Email failed: {e}")
        return False

if __name__ == "__main__":
    test_email()