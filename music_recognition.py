from loguru import logger
import requests
import datetime
import subprocess
from acrcloud.recognizer import ACRCloudRecognizer
from dotenv.main import load_dotenv
from os import environ, path
import json
load_dotenv()

BUCKET_ID = 20149
MAIN_DIR = path.dirname(path.abspath(__file__))
date_now = datetime.date.today()
logger.add(path.join(MAIN_DIR, 'logs', f"music_recognition_{date_now}.log"), rotation="1 day")


class MusicError(OSError):
    """Raised when an error relating the ACRCloud API occurred"""
    logger.debug(f"Debug info: Bucket ID: {BUCKET_ID}")  # TODO (low priority): Insert relevant data to log
    pass


class MusicRecognitionError(MusicError):
    """Raised when an error occurred while recognising music using ACRCloud API"""
    logger.error("Can't recognize audio file in database")


class MusicUploadError(MusicError):
    """Raised when an error occurred while uploading music using ACRCloud API"""
    logger.error("Can't upload audio file to database")


class MusicDeleteError(MusicError):
    """Raised when an error occurred while deleting music using ACRCloud API"""
    logger.error("Can't delete audio file from database")


CONFIG = {
    'host': environ.get('ACRCLOUD_HOST', ''),
    'access_key': environ.get('ACRCLOUD_ACCESS_KEY', ''),
    'access_secret': environ.get('ACRCLOUD_ACCESS_SECRET', ''),
    'debug': False,
    'timeout': 10  # seconds
}
# BUCKET_INTERACTION_TOKEN = environ.get('ACRCLOUD_USER_INTERACTION_TOKEN', '')
BUCKET_INTERACTION_TOKEN = environ.get('TEST_ALL_TOKEN', '')


def recognize(recording_sample: str) -> bool:
    """
    Check if the recorded sample is present in the user database (the sample is cropped to the first 10 seconds)
    :param recording_sample: Path to local audio file
    :return: Is the recording in user database or not
    """
    logger.info(f"Recognising file in {recording_sample}")
    acr_recognizer = ACRCloudRecognizer(CONFIG)
    answer = json.loads(acr_recognizer.recognize_by_file(recording_sample, start_seconds=0))
    logger.info(f"Done recognising file in {recording_sample}")
    logger.debug(f"Recognition answer: {answer}")
    if answer["status"]["msg"] == 'Success':
        return True
    elif answer['status']['msg'] == 'No result':
        return False
    else:
        raise MusicRecognitionError(answer['status'])


def upload_to_db(user_full_track: str, title: str, artist: str, album: str = 'Single') -> None:
    """
    Upload an audio file to user music bucket.

    :param user_full_track: Absolute path to the user audio file
    :param title: Music Title
    :param artist: Music Artist
    :param album: Music Album
    :exception MusicUploadError: The ACRCloud API encountered an error while uploading user's audio file
    :return: None (Everything is fine)
    """
    url = f"https://api-v2.acrcloud.com/api/buckets/{BUCKET_ID}/files"

    payload = {'title': title, 'data_type': 'audio',
               "user_defined": json.dumps({"artist": artist, 'album': album})}
    files = [
        ('file', (path.split(user_full_track)[-1], open(user_full_track, 'rb'), 'audio/mpeg'))
    ]
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {BUCKET_INTERACTION_TOKEN}'
    }

    logger.info(f"Uploading file in {user_full_track}")
    response = requests.request("POST", url,
                                headers=headers,
                                data=payload,
                                files=files)
    logger.info(f"Done uploading file in {user_full_track}")
    answer = json.loads(response.text)
    if answer.get('error'):
        raise MusicUploadError(response.text)

    return


def get_files_in_db() -> dict:
    url = f"https://api-v2.acrcloud.com/api/buckets/{BUCKET_ID}/files"

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {BUCKET_INTERACTION_TOKEN}'
    }

    logger.info("Getting audio files from database...")
    response = requests.get(url, headers=headers)
    logger.info("Finished getting audio files from database")
    answer = json.loads(response.text)
    if answer.get('error'):
        raise MusicUploadError(response.text)

    return answer


def delete_from_db(file_id: int) -> None:
    """Delete audio file from user music bucket.

    :param file_id: Audio file's database ID number
    :exception MusicDeleteError: The ACRCloud API encountered an error while deleting user's audio file
    :return: None (Everything is fine)
    """

    logger.info(f"Deleting audio file '{file_id}' from database")
    return_code = subprocess.run([
        "curl", "--location", "--request", "DELETE",
        f"https://api-v2.acrcloud.com/api/buckets/{BUCKET_ID}/files/{file_id}",
        "--header", "Accept: application/json",
        "--header", f"Authorization: Bearer {BUCKET_INTERACTION_TOKEN}"
    ])
    logger.info(f"Finished deleting audio file '{file_id}' from database")
    logger.debug(f"CMD return code: {return_code}")


def get_ids_and_titles(database: dict) -> dict:
    titles_ids = dict()
    for track_num in range(len(database['data'])):
        file_title = database['data'][track_num]['title']
        file_id = database['data'][track_num]['id']
        if titles_ids.get(file_title):
            logger.warning(f"Database contains duplicate files titled '{file_title}'. Using ID: {file_id}.")

        titles_ids[file_title] = file_id

    return titles_ids


def get_id_from_title(database: dict, title: str) -> int:
    db_ids_titles = get_ids_and_titles(database)
    return int(db_ids_titles[title])
