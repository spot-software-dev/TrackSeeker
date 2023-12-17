import datetime
import os.path

from loguru import logger
from instagram_bot import IGBOT, IGDownloadError
from music_recognition import list_container_files_and_results, add_to_container_recognizer
from drive_logic import Drive
from setup import MAIN_DIR
import time

date_now = datetime.date.today()
logger.add(os.path.join(MAIN_DIR, 'logs', 'music_recognition', f"music_recognition_{date_now}.log"), rotation="1 day")


def get_story_user(story_name: str) -> str:
    """Get the username of the user that uploaded the story"""
    return os.path.splitext(story_name.split("-")[-1])[0]


def get_story_id_from_name(story: dict) -> str:
    """
    pacha-2023-10-11-9999999_99999-thequeenikalala.mp4   ->   9999999_99999
    """
    story_name = story['name']
    story_id = story_name.split('-')[-2]

    return story_id


def remove_duplicated_users_from_locations_and_users(locations_and_users: list):
    for location_and_users in locations_and_users:
        location_and_users['usernames'] = set(location_and_users['usernames'])



def sync_user_stories(drive: Drive, instagram_bot: IGBOT) -> None:
    """
    Add each of today's Instagram location story user's stories that hasn't been uploaded yet to user's Drive

    :param drive: Drive object for Spot Google Drive requests
    :param instagram_bot: Instagram Bot object for Instagram user-stories searching and downloading

    Get a list of users from user's Google Drive Dashboard_locations,
    download by Instagram username all their currently uploaded stories
    that hasn't been uploaded yet to the main Drive stories folder
    and add them to user's main Drive stories folder.
    """
    today_usernames_by_locations = drive.get_today_locations_stories_usernames(locations_dir_id=drive.STORY_STORY_LOCATIONS_DIR_ID)
    remove_duplicated_users_from_locations_and_users(today_usernames_by_locations)
    spot_stories_locations_dirs = drive.get_spot_locations_dirs()
    spot_stories_locations_names = [location['name'] for location in spot_stories_locations_dirs]

    for usernames_by_location in today_usernames_by_locations:
        location_name = usernames_by_location['location']
        usernames = usernames_by_location['usernames']
        if location_name not in spot_stories_locations_names:
            drive.create_drive_dir(dir_name=location_name, parent_dir_id=drive.SPOT_LOCATIONS_DIR_ID)
            time.sleep(5)
        
        location_dir_id = drive.get_dir_id_with_parent(dir_name=location_name, parent_dir_id=drive.SPOT_LOCATIONS_DIR_ID)
        location_dir_videos = drive.get_all_videos_from_dir(dir_id=location_dir_id)
        location_dir_stories_id = [get_story_id_from_name(story=story) for story in location_dir_videos]

        for user_name in usernames:
            user_stories_metadata = instagram_bot.get_user_stories_metadata(username=user_name)
            for story_metadata in user_stories_metadata:
                if story_metadata['id'] in location_dir_stories_id:
                    logger.debug(f"Story already exists in Drive, Story ID: {story_metadata['id']}")
                    location_dir_stories_id.remove(story_metadata['id'])
                else:
                    try:
                        instagram_bot.download_story(story_metadata=story_metadata, username=user_name, location=location_name)
                        drive.upload_story_for_sync(dir_id=location_dir_id, story_metadata=story_metadata, username=user_name, location=location_name)
                    except IGDownloadError:
                        logger.warning(f"Encountered an error downloading file {story_metadata['id']}. Skipping file...")

    logger.success('Done syncing all stories uploaded today by users who tagged at least once a location SPOT follows')


def get_acrcloud_ids_from_drive_id(drive_id: str) -> list:
    """Get a list of ACRCloud file IDs of the entered Google Drive ID in ACRCloud container"""
    container_files = list_container_files_and_results()
    acrcloud_ids = []
    for container_file in container_files:
        container_file_drive_id = Drive.get_id_from_sharable_link(
            container_file['drive_url'])
        if drive_id == container_file_drive_id:
            acrcloud_ids.append(container_file['acrcloud_id'])

    return acrcloud_ids


def get_stories_not_in_acrcloud_container(drive: Drive) -> list:
    """
    Get all stories in Google Drive that are not yet in ACRCloud container

    :param drive: Drive object for Spot Google Drive requests
    """
    drive_files = drive.get_all_spot_videos()
    acrcloud_recognition_results = list_container_files_and_results()
    acrcloud_files_urls = [story_recognition['drive_url'] for story_recognition in acrcloud_recognition_results if story_recognition['drive_url']]
    acrcloud_files_ids = [drive.get_id_from_sharable_link(acrcloud_file_url) for acrcloud_file_url in acrcloud_files_urls]

    stories_to_add = []

    for file in drive_files:
        if file['id'] in acrcloud_files_ids:
            acrcloud_files_ids.remove(file['id'])
        else:
            stories_to_add.append(file)

    return stories_to_add


def sync_stories_to_recognize(drive: Drive):
    """
    Upload stories in Google Drive that are not yet in ACRCloud container.

    :param drive: Drive object for Spot Google Drive requests
    """
    logger.info(
        "Synchronizing ACRCloud stories with the stories saved in Google Drive")
    drive_stories_to_add = get_stories_not_in_acrcloud_container(drive)
    for drive_story in drive_stories_to_add:
        drive_story_url = Drive.get_video_sharable_link(drive_story['id'])
        add_to_container_recognizer(drive_story_url)


def master_sync(drive: Drive, instagram_bot: IGBOT):
    """Sync users stories to Google Drive and add their Google Drive links to ACRCloud recognize"""
    logger.info("Starting Master Sync...")
    sync_user_stories(drive, instagram_bot)
    sync_stories_to_recognize(drive)
    logger.success("Done Master Sync")


def location_logic(location: str, drive: Drive,
                   day: int = date_now.day, month: int = date_now.month, year: int = date_now.year,
                   end_day: int = 0, end_month: int = 0, end_year: int = 0) -> list:
    """
    Get stories tagged with a certain location on a certain date with a track present in the database.

    (Can be used with consecutive dates - fill end date parameters for the consecutive dates functionality)

    :param location: Location name of tagged location stories
    :param drive: Drive object for Spot Google Drive requests
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

    drive_files = drive.get_videos_at_date_range_from_dir(dir_name=location, parent_dir_id=drive.SPOT_LOCATIONS_DIR_ID,
                                                          start_year=year, start_month=month, start_day=day,
                                                          end_year=end_year, end_month=end_month, end_day=end_day)
    found_results = []
    for file in recognized_stories:
        if file['name'] in [drive_file['name'] for drive_file in drive_files]:
            drive_id = drive.get_id_from_sharable_link(file['drive_url'])
            download_url = drive.get_download_link(drive_id)
            file['download_url'] = download_url
            file_drive_id = drive.get_id_from_sharable_link(file['drive_url'])
            file['drive_url'] = drive.get_video_link(file_drive_id)
            found_results.append(file)

    logger.success("Finished searching stories in location")
    return found_results
