import datetime
import os.path

from loguru import logger  # TODO: Add logging to logger and its tests
from .instagram_bot import IGBOT, STORIES_DIR_PATH
from .music_recognition import recognize, MusicRecognitionError

MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
date_now = datetime.date.today()
logger.add(os.path.join(MAIN_DIR, 'logs', 'music_recognition', f"music_recognition_{date_now}.log"), rotation="1 day")


def logic(username: str) -> list:
    """
    Recognize tracks in database that an Instagram user uploaded to their story.

    :param username: Name of the Instagram user to search its stories
    :return: List of recognized tracks that exist in the database and in a user story
    """
    instagram_bot = IGBOT()
    user_id = instagram_bot.get_user_id(username)
    stories_music = instagram_bot.download_user_stories(user_id)
    recognised_tracks = []
    for story_id, story_metadata in stories_music.items():
        try:
            recognition_results = recognize(os.path.join(STORIES_DIR_PATH, f'{story_id}.mp3'))
            if recognition_results:
                for recognition in recognition_results:
                    recognised_tracks.append({
                        'title': recognition['title'],
                        'artist': story_metadata.get('artist'),
                        'album': story_metadata.get('album')
                    })
        except MusicRecognitionError as e:
            logger.critical(f"Error occurred while recognizing music from story ({story_id}.mp3)\n\tError message: {e}")
            # TODO: Display error message to user and ask to re-enter the file or reach support
            continue

    return recognised_tracks
