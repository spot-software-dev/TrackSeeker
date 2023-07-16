import instaloader
import os
from moviepy.editor import VideoFileClip
from dotenv.main import load_dotenv
from os import environ
load_dotenv()

BOT_USERNAME = environ.get('BOT_USERNAME', '')
BOT_PASSWORD = environ.get('BOT_PASSWORD', '')

FILE_DIR_PATH = os.path.splitext(os.path.abspath(__file__))[0]


class IGBOT:
    def __init__(self):
        self.bot = instaloader.Instaloader()
        self.bot.login(BOT_USERNAME, BOT_PASSWORD)

    def get_userID(self, username: str) -> int:
        return self.bot.check_profile_id(username).userid

    def download_user_stories(self, userid: int) -> None:
        for story in self.bot.get_stories(userids=[userid]):
            for story_item in story.get_items():
                self.bot.download_storyitem(story_item, 'stories')

    @staticmethod
    def get_video_paths() -> list:
        videos = []
        for file in os.listdir('stories'):
            if file[-4:] == '.mp4':
                # TODO: make the paths according to where the file gets ran
                #  (so that in the tests it will not look for the main stories folder, but the tests stories folder)
                videos.append(os.path.join(FILE_DIR_PATH, 'stories', file))
        return videos

    @staticmethod
    def convert_to_mp3(videos_paths: list) -> list:
        music_paths = []
        for video_path in videos_paths:
            audio_filename = f"{os.path.splitext(video_path)[0]}.mp3"
            video = VideoFileClip(video_path)
            video.audio.write_audiofile(audio_filename)
            music_paths.append(audio_filename)
        return music_paths

    def instagram_search(self, username: str) -> list:
        """
        Search and download Instagram stories of the entered username or all of instagram's
        stories tagged with the #Hashtag

        :param username: Instagram Username / #Hashtag
        :type username: str
        :return: paths for story audio files found
        :rtype: list[str, str, str...] / None
        """
        userid = self.get_userID(username)
        self.download_user_stories(userid)
        stories_paths = self.get_video_paths()
        return self.convert_to_mp3(stories_paths)
