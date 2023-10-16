from loguru import logger  # TODO: Add logging to instagram_bot.py and tests
import os
import requests
import time
import datetime
import xmltodict
from dotenv.main import load_dotenv
load_dotenv()

RAPID_API_TIME_LIMIT = 1
MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_DIR_PATH = os.path.join(MAIN_DIR, 'instagram_bot_media')
STORIES_DIR_PATH = os.environ.get('STORIES_DIR_PATH', FILE_DIR_PATH)
if not os.path.exists(STORIES_DIR_PATH):
    os.makedirs(STORIES_DIR_PATH)

date_now = datetime.date.today()
logger.add(os.path.join(MAIN_DIR, 'logs', "instagram_bot",
           f"instagram_bot_{date_now}.log"), rotation="1 day")


class IGError(OSError):
    """Raised when an error relating the Instagram API occurred"""
    pass


class IGGetError(IGError):
    """Raised when an error occurred while getting Instagram info using Instagram API"""
    pass


class IGDownloadError(IGGetError):
    """Raised when an error occurred while downloading Instagram Stories using Instagram API"""
    pass


class IGMetaDataError(IGGetError):
    """Raised when an error occurred while getting Instagram Stories metadata using Instagram API"""
    pass


class IGBOT:
    def __init__(self):
        self.last_request_time = time.time()

    def fix_request_time(self):
        wiggle_room_sec = 0.5 
        time_now = time.time()
        time_difference = time_now - self.last_request_time
        if time_difference < RAPID_API_TIME_LIMIT + wiggle_room_sec:
            # RAPID API allows 1 request per second
            time.sleep(RAPID_API_TIME_LIMIT + wiggle_room_sec - time_difference)

        self.last_request_time = time.time()

    def get_user_id(self, username: str) -> str:
        """
        Discover user ID from given username
        """
        url = "https://instagram-scraper-2022.p.rapidapi.com/ig/user_id/"
        querystring = {"user": username}
        headers = {
            "X-RapidAPI-Key": os.environ.get("X_RAPID_API_KEY"),
            "X-RapidAPI-Host": os.environ.get("X_RAPID_API_HOST")
        }

        self.fix_request_time()

        response = requests.get(url, headers=headers, params=querystring)

        self.last_request_time = time.time()

        if not response.ok:
            raise IGGetError(response.text)
        return response.json()['id']

    def get_userinfo(self, id_user: str) -> dict:
        """
        Discover user info (like username) from given user ID
        """
        url = "https://instagram-scraper-2022.p.rapidapi.com/ig/info/"
        querystring = {"id_user": id_user}
        headers = {
            "X-RapidAPI-Key": os.environ.get("X_RAPID_API_KEY"),
            "X-RapidAPI-Host": os.environ.get("X_RAPID_API_HOST")
        }

        self.fix_request_time()

        response = requests.get(url, headers=headers, params=querystring)

        self.last_request_time = time.time()

        if not response.ok:
            raise IGGetError(response.text)
        return response.json()['user']

    def download_story(self, story_metadata: dict, username: str, location: str) -> dict:
        """Download story to a temp folder and add name and download path to story metadata for Drive upload"""
        download_url = story_metadata['download_url']
        story_id = story_metadata['id']
        story_name = f"{location}-{date_now}-{story_id}-{username}.mp4"
        file_path = os.path.join(STORIES_DIR_PATH, story_name)

        self.fix_request_time()

        logger.info(f'Trying to download story {story_name}...')

        try:

            with open(file_path, "wb") as f:
                response = requests.get(download_url)
                f.write(response.content)

            logger.success(f'Downloaded story {story_name} successfully.')

            story_metadata['path'] = file_path
            story_metadata['name'] = story_name
            return story_metadata

        except Exception as e:
            raise IGDownloadError(e)

    def get_user_stories_metadata(self, username: str) -> list[dict[str, str]]:
        """
        Download user stories (named with its ID) and return each story ID with its story JSON
        """

        user_id = self.get_user_id(username=username)

        url = "https://instagram-scraper-2022.p.rapidapi.com/ig/stories/"
        querystring = {"id_user": user_id}
        headers = {
            "X-RapidAPI-Key": os.environ.get("X_RAPID_API_KEY"),
            "X-RapidAPI-Host": os.environ.get("X_RAPID_API_HOST")
        }

        self.fix_request_time()

        response = requests.get(url, headers=headers, params=querystring)

        self.last_request_time = time.time()

        if response.ok:
            if "Something went wrong" in response.text:
                raise IGMetaDataError(response.text)
            user_stories_metadata = []
            if response.json().get('reels'):
                for story in response.json()['reels'][user_id]['items']:
                    if story.get('has_audio'):
                        story_url = story['video_versions'][0]['url']
                        user_stories_metadata.append({"id": story['id'], "download_url": story_url})
            else:
                # TODO: Change the logger message. It is not necessarily true that the user has no stories
                logger.info(
                    f"User has no stories. User ID: {user_id} Username: {username}")
            return user_stories_metadata
        else:
            raise IGMetaDataError(response.text)

    def get_audio_urls_from_post_location_id(self, location_id: int) -> dict:
        """Get usernames and their audio URL of recent Instagram Posts in entered location"""
        url = "https://instagram-scraper-2022.p.rapidapi.com/ig/locations/"
        querystring = {"location_id": location_id}
        headers = {
            "X-RapidAPI-Key": os.environ.get("X_RAPID_API_KEY"),
            "X-RapidAPI-Host": os.environ.get("X_RAPID_API_HOST")
        }

        self.fix_request_time()

        response = requests.get(url, headers=headers, params=querystring)

        self.last_request_time = time.time()

        if response.ok:
            sections = response.json(
            )['native_location_data']['recent']['sections']
            location_audios = dict()
            for section in sections:
                medias = section['layout_content']['medias']
                for media in [media for media in medias if media['media'].get('video_dash_manifest')]:
                    xml_data = xmltodict.parse(
                        media['media']['video_dash_manifest'])
                    audio_represent_url = xml_data['MPD']['Period']['AdaptationSet'][1]['Representation']['BaseURL']
                    if type(audio_represent_url) is str:
                        audio_url = audio_represent_url
                    else:
                        audio_url = audio_represent_url['#text']
                    if not location_audios.get(media['media']['user']['username']):
                        location_audios[media['media']
                                        ['user']['username']] = []
                    location_audios[media['media']['user']
                                    ['username']].append(audio_url)

            return location_audios
        else:
            raise IGGetError(response.text)

    # TODO: Add clean_stories_directory method to bot init and change tests accordingly (replaces setup).
    # TODO: Make sure tests that need files in the stories directory get them using pytest.fixture!
    @staticmethod
    def clean_stories_directory():
        """
        Delete all files in stories directory
        """
        for file in os.listdir(STORIES_DIR_PATH):
            os.remove(os.path.join(STORIES_DIR_PATH, file))
