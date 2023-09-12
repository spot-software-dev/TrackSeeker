from os import environ
import json
from dotenv.main import load_dotenv
load_dotenv()

CLIENT_ID = environ.get("CLIENT_ID")
PROJECT_ID = environ.get("PROJECT_ID")
CLIENT_SECRET = environ.get("CLIENT_SECRET")

CREDENTIALS = {
        "installed": {
            "client_id": f"{CLIENT_ID}.apps.googleusercontent.com",
            "project_id": f"supple-portal-{PROJECT_ID}", "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": f"{CLIENT_SECRET}", "redirect_uris": ["http://localhost"]}
    }
creds = json.dumps(CREDENTIALS)

with open("credentials.json", 'w') as json_file:
    json_file.write(creds)
