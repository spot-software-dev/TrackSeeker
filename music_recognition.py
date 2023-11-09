from loguru import logger
import requests
import datetime
import subprocess
from dotenv.main import load_dotenv
import os
from io import BytesIO
import json
from werkzeug.utils import secure_filename

load_dotenv()

BUCKET_ID = os.environ.get('BUCKET_ID', '')
CONTAINER_ID = os.environ.get('CONTAINER_ID', '')
MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
date_now = datetime.date.today()
logger.add(os.path.join(MAIN_DIR, 'logs', 'music_recognition', f"music_recognition_{date_now}.log"), rotation="1 day")

CONTAINERS_RESULTS_LIMIT = 10000000
BUCKET_FILES_PER_REQUEST = 80


class MusicError(OSError):
    """Raised when an error relating the ACRCloud API occurred"""
    def __init__(self):
        self.message = f"Debug info: Bucket ID: {BUCKET_ID}"
        logger.debug(self.message)  # TODO (low priority): Insert relevant data to log

    def __str__(self):
        return self.message


class MusicRecognitionError(MusicError):
    """Raised when an error occurred while recognising music using ACRCloud API"""
    def __init__(self, error):
        self.message = f"Can't recognize audio file in database. Status: {error}"
        logger.error(self.message)

    def __str__(self):
        return self.message


class MusicUploadError(MusicError):
    """Raised when an error occurred while uploading music using ACRCloud API"""
    def __init__(self, error):
        self.message = f"Can't upload audio file to database {error}"
        logger.error(self.message)

    def __str__(self):
        return self.message


class MusicDeleteError(MusicError):
    """Raised when an error occurred while deleting music using ACRCloud API"""
    def __init__(self, error):
        self.message = f"Can't delete audio file from database {error}"
        logger.error(self.message)

    def __str__(self):
        return self.message


class MusicDuplicationError(MusicError):
    """Raised when trying to upload a track that already exists to the database using ACRCloud API."""
    def __init__(self):
        self.message = f"Failed to upload song, it already exists in the database."
        logger.error(self.message)

    def __str__(self):
        return self.message


class MusicFileDoesNotExist(MusicDeleteError):
    """Raised when the title entered for deletion does not exist in the database"""
    def __init__(self, error):
        self.message = f"File does not exist in the database {error}"
        logger.error(self.message)

    def __str__(self):
        return self.message


CONFIG = {
    'host': os.environ.get('ACRCLOUD_HOST', ''),
    'access_key': os.environ.get('ACRCLOUD_ACCESS_KEY', ''),
    'access_secret': os.environ.get('ACRCLOUD_ACCESS_SECRET', ''),
    'debug': False,
    'timeout': 10  # seconds
}
# BUCKET_INTERACTION_TOKEN = environ.get('ACRCLOUD_USER_INTERACTION_TOKEN', '')
BUCKET_INTERACTION_TOKEN = os.environ.get('TEST_ALL_TOKEN', '')


# noinspection PyUnresolvedReferences
def _upload_to_db(audio_file: BytesIO, title: str, artist: str, album: str = 'Single') -> None:
    """
    Upload an audio file to user music bucket.

    :param audio_file: user audio file
    :param title: Music Title
    :param artist: Music Artist
    :param album: Music Album
    :exception MusicUploadError: The ACRCloud API encountered an error while uploading user's audio file
    :return: None (Everything is fine)
    """
    url = f"https://api-v2.acrcloud.com/api/buckets/{BUCKET_ID}/files"

    payload = {'title': title or os.path.splitext(secure_filename(audio_file.filename))[0],
               'data_type': 'audio',
               "user_defined": json.dumps({"artist": artist, 'album': album})}
    files = [
        ('file', (secure_filename(audio_file.filename), audio_file, 'audio/mpeg'))
    ]
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {BUCKET_INTERACTION_TOKEN}'
    }

    logger.info(f"Uploading file")
    try:
        response = requests.post(url, headers=headers, data=payload, files=files)
        logger.info(f"Done uploading file")
        
        answer = response.json()
        if answer.get('error'):
            raise MusicUploadError(answer['error'])
    
    except requests.RequestException as e:
        raise MusicUploadError(str(e))

    return


def upload_to_db_protected(audio_file: BytesIO, title: str, artist: str, album: str = 'Single') -> None:
    """
    Upload an audio file to user music bucket.

    :param audio_file: user audio file
    :param title: Music Title
    :param artist: Music Artist
    :param album: Music Album
    :exception MusicUploadError: The ACRCloud API encountered an error while uploading user's audio file
    :return: None (Everything is fine)
    """
    logger.info("Before uploading")
    db = get_files_in_db()
    files_metadata = get_musical_metadata(db)
    if title in files_metadata:
        if artist in files_metadata[title]['artist']:
            raise MusicDuplicationError()

    _upload_to_db(audio_file, title, artist, album)


def get_files_in_db() -> list:

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {BUCKET_INTERACTION_TOKEN}'
    }

    page_number = 0
    results = []
    while True:
        url = f"https://api-v2.acrcloud.com/api/buckets/{BUCKET_ID}/files?page={page_number}&per_page={BUCKET_FILES_PER_REQUEST}"

        logger.info("Getting audio files from database...")
        response = requests.get(url, headers=headers)
        answer = json.loads(response.text)
        if answer.get('error'):
            raise MusicUploadError(response.text)

        results += answer['data']

        if answer['meta']['current_page'] == answer['meta']['last_page']:
            break

        page_number += 1

        logger.info(f"Finished getting audio files from database. Got {answer['meta']['total']}")

    return results


def delete_id_from_db(file_id: int) -> None:
    """Delete audio file from user music bucket using the track ID.

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


def delete_from_db(title: str) -> None:
    """
    Delete audio file from user music bucket using the track Title.

    :param title: Track's title in database
    :exception MusicDeleteError: The ACRCloud API encountered an error while deleting user's audio file
    :return: None (Everything is fine)
    """
    db = get_files_in_db()
    files_in_db = get_musical_metadata(db)
    if title in list(files_in_db):
        file_id = get_id_from_title(db, title)
        delete_id_from_db(file_id)
    else:
        raise MusicFileDoesNotExist(f"Entered file title: {title}")


def delete_id_from_db_protected_for_web(file_id: int) -> None:
    """
    Delete audio file from user music bucket using the track Title.

    :param file_id: Track's ID in database
    :exception MusicDeleteError: The ACRCloud API encountered an error while deleting user's audio file
    :return: None (Everything is fine)
    """
    db = get_files_in_db()
    files_metadata = get_musical_metadata(db)
    if file_id in list(map(lambda metadata: metadata['id'], files_metadata.values())):
        delete_id_from_db(int(file_id))
    else:
        raise MusicFileDoesNotExist(f"{'files_in_db': files_in_db, 'entered_title': title}")


def get_musical_metadata(database: list) -> dict:
    """
    Get the musical metadata of all tracks in database: title, album, artist, ACRCloud database ID
    {song_title: {'id': id, 'artist': artist, 'album': album}, song_title_2: {'id': id, ...}, ...}
    """
    titles_ids = dict()
    for track_num in range(len(database)):
        file_title = database[track_num]['title']
        file_id = database[track_num]['id']
        file_artist = database[track_num]['user_defined']['artist']
        file_album = database[track_num]['user_defined']['album']

        titles_ids[file_title] = {
            'id': file_id,
            'artist': file_artist,
            'album': file_album
        }

    return titles_ids


def get_id_from_title(database: list, title: str) -> int:
    db_ids_titles = get_musical_metadata(database)
    return int(db_ids_titles[title]['id'])


def get_human_readable_db() -> list:
    """
    Get a list of all tracks in the database in a human-readable form (flattened json):
    [{'title': title, 'album': album, 'artist': artist, 'id': ACRCloud database ID}, {'title': title_2, ...}, ...]
    """
    db = get_files_in_db()
    musical_metadata = get_musical_metadata(db)
    readable_db = []
    for title in musical_metadata:
        readable_db.append(
            {'title': title, 'album': musical_metadata[title]['album'],
             'artist': musical_metadata[title]['artist'], 'id': musical_metadata[title]['id']}
        )

    return readable_db


def add_to_container_recognizer(link: str) -> dict:
    """
    Add file to the container recognizer.
    """

    url = f"https://api-v2.acrcloud.com/api/fs-containers/{CONTAINER_ID}/files"

    payload = {
        'data_type': 'platforms',
        'url': link
    }

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {BUCKET_INTERACTION_TOKEN}',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        logger.success(f"Uploaded {link} to container ID {CONTAINER_ID}")
        return response.json()
    else:
        logger.error(f"Upload to container failed with status code:\n{response.status_code}")
        raise MusicRecognitionError(response.text)


def list_container_files_and_results() -> list:
    """
    Get all files in ACRCloud container and their recognition results
    """
    url = f"https://api-v2.acrcloud.com/api/fs-containers/{CONTAINER_ID}/files?page=1&per_page={CONTAINERS_RESULTS_LIMIT}&with_result=1"

    payload = {}
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {BUCKET_INTERACTION_TOKEN}'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        data = response.json()
        logger.info(f"Finished getting all {len(data['data'])} files in container ID {CONTAINER_ID}")
    else:
        logger.error(f"Getting files from container failed with status code:\n{response.status_code}")
        raise MusicRecognitionError(response.text)

    results = []
    for recognition in data['data']:
        recognition_data = {
            'drive_url': recognition['url'],
            'acrcloud_id': recognition['id'],
            'name': recognition['name']
        }
        if recognition['results']:
            metadata = recognition['results']['custom_files'][0]['result']
            relevant_metadata = {
                'title': metadata['title'],
                'artist': metadata['artist'],
                'album': metadata['album']
            }
            recognition_data['results'] = relevant_metadata
        else:
            recognition_data['results'] = dict()

        results.append(recognition_data)

    return results


def delete_from_container_recognizer(file_acrcloud_id: str):
    """
    Delete file from ACRCloud container recognizer
    :param file_acrcloud_id: ACRCloud file ID
    """

    url = f"https://api-v2.acrcloud.com/api/fs-containers/{CONTAINER_ID}/files/{file_acrcloud_id}"

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {BUCKET_INTERACTION_TOKEN}'
    }

    try:
        requests.request("DELETE", url, headers=headers)
        logger.success(f"Deleted ACRCloud file ID {file_acrcloud_id} from container ID {CONTAINER_ID}")
    except requests.RequestException as e:
        raise MusicDeleteError(str(e))


def rescan_all_files():
    """Rescan stories in ACRCloud container according to tracks in the database"""
    acrcloud_files_ids = [file['acrcloud_id'] for file in list_container_files_and_results()]

    chunk_size = 100
    number_of_chunks = len(acrcloud_files_ids) // chunk_size
    for current_chunk_num in range(number_of_chunks + 1):  # plus 1 for the final chunk
        logger.debug(f"Making ACRCloud rescan chunk num {current_chunk_num} out of {number_of_chunks}.")
        acrcloud_files_ids_chunk = ",".join(
            acrcloud_files_ids[current_chunk_num * chunk_size: (current_chunk_num + 1) * chunk_size]
        )
        url = f"https://api-v2.acrcloud.com/api/fs-containers/{CONTAINER_ID}/files/{acrcloud_files_ids_chunk}/rescan"

        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {BUCKET_INTERACTION_TOKEN}'
        }

        try:
            response = requests.request("PUT", url, headers=headers)
        except requests.RequestException as e:
            raise MusicDeleteError(str(e))

        logger.debug(response.text)

    logger.success(f"Rescanned all files from ACRCloud container.")
