import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

load_dotenv('e:/css - Copy/.env')

print('SMTP_HOST:', os.getenv('SMTP_HOST'))
print('SMTP_PORT:', os.getenv('SMTP_PORT'))
print('SMTP_USERNAME:', os.getenv('SMTP_USERNAME'))

try:
    msg = MIMEText('Test email content')
    msg['Subject'] = 'Test ElitePrep'
    msg['From'] = f"{os.getenv('SMTP_FROM_NAME')} <{os.getenv('SMTP_FROM_EMAIL')}>"
    msg['To'] = 'test@example.com' # dummy

    server = smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT', 587)))
    server.set_debuglevel(1)
    if os.getenv('SMTP_USE_TLS', 'true').lower() == 'true':
        server.starttls()
    
    server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
    print('Login successful!')
    server.quit()
except Exception as e:
    print(f'Failed to send email: {e}')
