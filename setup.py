from os import environ
import os.path
import datetime
import json
from loguru import logger
from dotenv.main import load_dotenv
load_dotenv()

GOOGLE_PRIVATE_KEY_ID = environ.get("GOOGLE_PRIVATE_KEY_ID")
GOOGLE_PRIVATE_KEY = environ.get("GOOGLE_PRIVATE_KEY", "").replace("\\n", "\n")

CREDENTIALS = {
    "type": "service_account",
    "project_id": "supple-portal-395117",
    "private_key_id": f"{GOOGLE_PRIVATE_KEY_ID}",
    "private_key": f"-----BEGIN PRIVATE KEY-----{GOOGLE_PRIVATE_KEY}-----END PRIVATE KEY-----\n",
    "client_email": "spot-id@supple-portal-395117.iam.gserviceaccount.com",
    "client_id": "114206747933036399061",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/spot-id%40supple-portal-395117.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
date_now = datetime.date.today()
logger.add(os.path.join(MAIN_DIR, 'logs', 'setup',
           f"setup_{date_now}.log"), rotation="1 day")


class GoogleAuthKeyEnvValuesError(OSError):
    """Raised when encountered an error while trying to receive env values for google auth file"""

    def __init__(self):
        self.message = f"Encountered an error while trying to receive env values"
        logger.error(self.message)

    def __str__(self):
        return self.message


def google_key_generate():
    if GOOGLE_PRIVATE_KEY and GOOGLE_PRIVATE_KEY_ID:
        creds = json.dumps(CREDENTIALS)

        with open("service-account-key.json", 'w') as json_file:
            json_file.write(creds)
    else:
        raise GoogleAuthKeyEnvValuesError
