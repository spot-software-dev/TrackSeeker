from loguru import logger  # TODO: Add logging to instagram_bot.py and tests
import os
import requests
import time
import datetime
import xmltodict
from moviepy.editor import VideoFileClip
from dotenv.main import load_dotenv
load_dotenv()

MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_DIR_PATH = os.path.join(MAIN_DIR, 'instagram_bot_media')
STORIES_DIR_PATH = os.environ.get('STORIES_DIR_PATH', FILE_DIR_PATH)
if not os.path.exists(STORIES_DIR_PATH):
    os.makedirs(STORIES_DIR_PATH)

date_now = datetime.date.today()
logger.add(os.path.join(MAIN_DIR, 'logs', "instagram_bot", f"instagram_bot_{date_now}.log"), rotation="1 day")


class IGError(OSError):
    """Raised when an error relating the Instagram API occurred"""
    pass


class IGGetError(IGError):
    """Raised when an error occurred while getting Instagram info using Instagram API"""
    pass


class IGDownloadError(IGError):
    """Raised when an error occurred while downloading Instagram Stories using Instagram API"""
    pass


class IGBOT:
    def __init__(self):
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

        time_now = time.time()
        time_difference = time_now - self.last_request_time
        if time_difference < 1:
            time.sleep(1 - time_difference)  # RAPID API allows 1 request per second

        response = requests.get(url, headers=headers, params=querystring)

        self.last_request_time = time.time()

        if not response.ok:
            raise IGGetError(response.text)
        return response.json()['id']

    def get_userinfo(self, user_id: str) -> dict:
        """
        Discover user info (like username) from given user ID
        """
        url = "https://instagram-scraper-2022.p.rapidapi.com/ig/info/"
        querystring = {"id_user": user_id}
        headers = {
            "X-RapidAPI-Key": os.environ.get("X_RAPID_API_KEY"),
            "X-RapidAPI-Host": os.environ.get("X_RAPID_API_HOST")
        }

        time_now = time.time()
        time_difference = time_now - self.last_request_time
        if time_difference < 1:
            time.sleep(1 - time_difference)

        response = requests.get(url, headers=headers, params=querystring)

        self.last_request_time = time.time()

        if not response.ok:
            raise IGGetError(response.text)
        return response.json()['user']

    @staticmethod
    def convert_story_videos_to_audio():
        for story_video in [os.path.join(STORIES_DIR_PATH, path) for path in os.listdir(STORIES_DIR_PATH)]:
            file_path, file_extension = os.path.splitext(story_video)
            if file_extension == ".mp4":
                video = VideoFileClip(story_video)
                video.audio.write_audiofile(f"{file_path}.mp3")

    def download_user_stories(self, user_id: str) -> dict:
        stories = self.download_user_stories_as_videos(user_id)
        IGBOT.convert_story_videos_to_audio()
        return stories

    def download_user_stories_as_videos(self, user_id: str) -> dict:
        """
        Download user stories (named with its ID) and return each story ID with its story JSON
        """
        url = "https://instagram-scraper-2022.p.rapidapi.com/ig/stories/"
        querystring = {"id_user": user_id}
        headers = {
            "X-RapidAPI-Key": os.environ.get("X_RAPID_API_KEY"),
            "X-RapidAPI-Host": os.environ.get("X_RAPID_API_HOST")
        }

        time_now = time.time()
        time_difference = time_now - self.last_request_time
        if time_difference < 1:
            time.sleep(1 - time_difference)

        response = requests.get(url, headers=headers, params=querystring)

        self.last_request_time = time.time()

        if response.ok:
            if "Something went wrong" in response.text:
                raise IGDownloadError(response.text)
            stories = {}
            if response.json().get('reels'):
                for story in response.json()['reels'][user_id]['items']:
                    if story.get('has_audio'):
                        story_url = story['video_versions'][0]['url']
                        stories[story['id']] = story
                        file_path = os.path.join(STORIES_DIR_PATH, f"{story['id']}.mp4")
                        with open(file_path, "wb") as f:
                            response = requests.get(story_url)
                            f.write(response.content)
            else:
                logger.info("User has no stories")  # TODO: Change the logger message. It is not necessarily true that the user has no stories
            return stories
        else:
            raise IGDownloadError(response.text)

    def get_audio_urls_from_post_location_id(self, location_id: int) -> dict:
        """Get usernames and their audio URL of recent Instagram Posts in entered location"""
        url = "https://instagram-scraper-2022.p.rapidapi.com/ig/locations/"
        querystring = {"location_id": location_id}
        headers = {
            "X-RapidAPI-Key": os.environ.get("X_RAPID_API_KEY"),
            "X-RapidAPI-Host": os.environ.get("X_RAPID_API_HOST")
        }

        time_now = time.time()
        time_difference = time_now - self.last_request_time
        if time_difference < 1:
            time.sleep(1 - time_difference)

        response = requests.get(url, headers=headers, params=querystring)

        self.last_request_time = time.time()

        if response.ok:
            sections = response.json()['native_location_data']['recent']['sections']
            location_audios = dict()
            for section in sections:
                medias = section['layout_content']['medias']
                for media in [media for media in medias if media['media'].get('video_dash_manifest')]:
                    xml_data = xmltodict.parse(media['media']['video_dash_manifest'])
                    audio_represent_url = xml_data['MPD']['Period']['AdaptationSet'][1]['Representation']['BaseURL']
                    if type(audio_represent_url) is str:
                        audio_url = audio_represent_url
                    else:
                        audio_url = audio_represent_url['#text']
                    if not location_audios.get(media['media']['user']['username']):
                        location_audios[media['media']['user']['username']] = []
                    location_audios[media['media']['user']['username']].append(audio_url)

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
