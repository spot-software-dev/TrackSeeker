import os
from dotenv.main import load_dotenv
load_dotenv()


class Config:
    # Flask Mail Configuration
    MAIL_SERVER = os.environ.get('EMAIL_HOST')  
    MAIL_PORT = int(os.environ.get('EMAIL_PORT'))  
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('EMAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('EMAIL_ADDRESS')  

    # CORS Configuration
    CORS_HEADERS = 'Content-Type'