import datetime
import os.path

from loguru import logger  # TODO: Add logging to logger and its tests
from instagram_bot import IGBOT, STORIES_DIR_PATH
from music_recognition import recognize, MusicRecognitionError
from music_recognition import list_container_files_and_results, add_to_container_recognizer
from drive_logic import Drive

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


def get_acrcloud_ids_from_drive_id(drive_id: str) -> list:
    """Get a list of ACRCloud file IDs of the entered Google Drive ID in ACRCloud container"""
    container_files = list_container_files_and_results()
    acrcloud_ids = []
    for container_file in container_files:
        container_file_drive_id = Drive.get_id_from_sharable_link(container_file['drive_url'])
        if drive_id == container_file_drive_id:
            acrcloud_ids.append(container_file['acrcloud_id'])

    return acrcloud_ids


def get_stories_not_in_acrcloud_container() -> list:
    """Get all stories in Google Drive that are not yet in ACRCloud container"""
    drive = Drive()
    drive_files = drive.get_all_files()
    acrcloud_recognition_results = list_container_files_and_results()
    acrcloud_files_urls = [story_recognition['drive_url'] for story_recognition in acrcloud_recognition_results]
    acrcloud_files_ids = [drive.get_id_from_sharable_link(acrcloud_file_url) for acrcloud_file_url in acrcloud_files_urls]

    stories_to_add = []

    for file in drive_files:
        if file['id'] in acrcloud_files_ids:
            acrcloud_files_ids.remove(file['id'])
        else:
            stories_to_add.append(file)

    return stories_to_add


def sync_stories_to_recognize():
    """Upload stories in Google Drive that are not yet in ACRCloud container."""
    logger.info("Synchronizing ACRCloud stories with the stories saved in Google Drive")
    drive_stories_to_add = get_stories_not_in_acrcloud_container()
    for drive_story in drive_stories_to_add:
        drive_story_url = Drive.get_file_sharable_link(drive_story['id'])
        add_to_container_recognizer(drive_story_url)


def location_logic(location: str,
                   day: int = date_now.day, month: int = date_now.month, year: int = date_now.year,
                   end_day: int = 0, end_month: int = 0, end_year: int = 0) -> list:
    """
    Get stories tagged with a certain location on a certain date with a track present in the database.
    (Can be used with consecutive dates - fill end date parameters for the consecutive dates functionality)
    :param location: Location name of tagged location stories
    :param day: Day of the date to search stories on (also the starting day of consecutive days)
    :param month: Month of the date to search stories on (also the starting month of consecutive days)
    :param year: Year of the date to search stories on (also the starting year of consecutive days)
    :param end_day: End day of the dates to search stories on
    :param end_month: End month of the dates to search stories on
    :param end_year: End year of the dates to search stories on
    :return: All stories with music tracks present in the database with Drive URL, Metadata and a download link
    """
    logger.info("Starting location search...")
    stories_recognition_results = list_container_files_and_results()
    recognized_stories = [story for story in stories_recognition_results if story['results']]

    drive = Drive()
    drive_files = drive.get_files(location,
                                  start_year=year, start_month=month, start_day=day,
                                  end_year=end_year, end_month=end_month, end_day=end_day)
    found_results = []
    for file in recognized_stories:
        if file['name'] in [drive_file['name'] for drive_file in drive_files]:
            drive_id = drive.get_id_from_sharable_link(file['drive_url'])
            download_url = drive.get_download_link(drive_id)
            file['download_url'] = download_url
            file_drive_id = drive.get_id_from_sharable_link(file['drive_url'])
            file['drive_url'] = drive.get_file_link(file_drive_id)
            found_results.append(file)

    logger.success("Finished searching stories in location")
    return found_results
