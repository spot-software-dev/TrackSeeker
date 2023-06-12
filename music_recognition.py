from loguru import logger
from datetime import datetime
import datetime
from acrcloud.recognizer import ACRCloudRecognizer
from dotenv.main import load_dotenv
from os import environ, path
import json
load_dotenv()

MAIN_DIR = path.dirname(path.abspath(__file__))
date_now = datetime.date.today()
logger.add(path.join(MAIN_DIR, 'logs', f"music_recognition_{date_now}.log"), rotation="1 day")


class MusicRecognitionError(Exception):
    """Raised when an error occurred while recognising music using ACRCloud API"""
    pass


CONFIG = {
    'host': environ.get('ACRCLOUD_HOST', ''),
    'access_key': environ.get('ACRCLOUD_ACCESS_KEY', ''),
    'access_secret': environ.get('ACRCLOUD_ACCESS_SECRET', ''),
    'debug': False,
    'timeout': 10  # seconds
}


def recognize(recording_sample: str) -> bool:
    """
    Check if the recorded sample is present in the user database (the sample is cropped to the first 10 seconds)
    :param recording_sample: Path to local audio file
    :return: Is the recording in user database or not
    """
    logger.info(f"Recognising file in {recording_sample}")
    acr_recognizer = ACRCloudRecognizer(CONFIG)
    answer = json.loads(acr_recognizer.recognize_by_file(recording_sample, start_seconds=0))
    logger.debug(f"Recognition answer: {answer}")
    if answer["status"]["msg"] == 'Success':
        return True
    elif answer['status']['msg'] == 'No result':
        return False
    else:
        raise MusicRecognitionError(answer['status'])


def upload_to_db(user_full_track):
    raise NotImplementedError
