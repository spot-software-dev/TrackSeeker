from acrcloud.recognizer import ACRCloudRecognizer
from dotenv.main import load_dotenv
from os import environ
load_dotenv()

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
    :return: Is the recording in user database or not.
    """
    acr_recognizer = ACRCloudRecognizer(CONFIG)
    answer = acr_recognizer.recognize_by_file(recording_sample, start_seconds=0)
    return answer["status"]["msg"] == "Success"


def upload_to_db(user_full_track):
    raise NotImplementedError
