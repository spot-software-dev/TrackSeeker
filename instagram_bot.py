import os
import requests
from moviepy.editor import VideoFileClip
from dotenv.main import load_dotenv
load_dotenv()

FILE_DIR_PATH = os.path.splitext(os.path.abspath(__file__))[0]
STORIES_DIR_PATH = os.environ.get('STORIES_DIR_PATH', os.path.join(FILE_DIR_PATH, "stories"))
if not os.path.exists(STORIES_DIR_PATH):
    os.makedirs(STORIES_DIR_PATH)


class IGBOT:
    @staticmethod
    def get_user_id(username: str) -> str:
        """
        Discover user ID from given username
        """
        url = "https://instagram-scraper-2022.p.rapidapi.com/ig/user_id/"
        querystring = {"user": username}
        headers = {
            "X-RapidAPI-Key": os.environ.get("X_RAPID_API_KEY"),
            "X-RapidAPI-Host": os.environ.get("X_RAPID_API_HOST")
        }
        response = requests.get(url, headers=headers, params=querystring)
        return response.json()['id']

    @staticmethod
    def download_user_stories(user_id: str) -> dict:
        stories = IGBOT.download_user_stories_as_videos(user_id)
        IGBOT.convert_story_videos_to_audio()
        return stories

    @staticmethod
    def download_user_stories_as_videos(user_id: str) -> dict:
        """
        Download user stories (named with its ID) and return each story ID with its story JSON
        """
        url = "https://instagram-scraper-2022.p.rapidapi.com/ig/stories/"
        querystring = {"id_user": user_id}
        headers = {
            "X-RapidAPI-Key": os.environ.get("X_RAPID_API_KEY"),
            "X-RapidAPI-Host": os.environ.get("X_RAPID_API_HOST")
        }
        response = requests.get(url, headers=headers, params=querystring)

        if response.json()['status'] == 'ok':
            stories = {}
            for story in response.json()['reels'][user_id]['items']:
                if story.get('has_audio'):
                    story_url = story['video_versions'][0]['url']
                    stories[story['id']] = story
                    file_path = os.path.join(STORIES_DIR_PATH, f"{story['id']}.mp4")
                    try:
                        with open(file_path, "wb") as f:
                            response = requests.get(story_url)
                            f.write(response.content)
                    except Exception as e:  # TODO: catch the relevant errors
                        f.close()
                        raise Exception(e)  # TODO: raise here the appropriate error, make sure to catch it in main!
                    finally:
                        f.close()
            return stories
        else:
            raise NotImplementedError  # TODO: raise here the appropriate error, make sure to catch it in main!

    @staticmethod
    def convert_story_videos_to_audio():
        for story_video in [os.path.join(STORIES_DIR_PATH, path) for path in os.listdir(STORIES_DIR_PATH)]:
            file_path, file_extension = os.path.splitext(story_video)
            if file_extension == ".mp4":
                video = VideoFileClip(story_video)
                video.audio.write_audiofile(f"{file_path}.mp3")
