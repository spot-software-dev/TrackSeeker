import datetime
import os.path

from loguru import logger  # TODO: Add logging to logger and its tests
from .instagram_bot import IGBOT, STORIES_DIR_PATH
from .music_recognition import recognize, MusicRecognitionError, check_if_video_has_audio
from .drive_logic import Drive, clear_downloaded_stories_dir

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


def location_logic(location: str,
                   day: int = date_now.day, month: int = date_now.month, year: int = date_now.year,
                   end_day: int = 0, end_month: int = 0, end_year: int = 0) -> list:
    drive = Drive()
    downloaded_files = drive.download_files(location=location,
                                            start_day=day, end_day=end_day or day,
                                            start_month=month, end_month=end_month or month,
                                            start_year=year, end_year=end_year or year
                                            )

    recognized_stories = []
    for file in downloaded_files:
        if check_if_video_has_audio(file['path']):
            result = recognize(file['path'])
            if result:
                drive_url = drive.get_file_link(file['id'])
                download_url = drive.get_download_link(file['id'])
                logger.success(f"Recognized Song! In story ID: {file['id']}")
                recognized_stories.append({'drive_url': drive_url, 'download_url': download_url, 'metadata': result})
        else:
            logger.debug(f'File {file["path"]} has no audio. Deleting file.')
            os.remove(file['path'])

    clear_downloaded_stories_dir()

    return recognized_stories
