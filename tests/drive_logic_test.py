import pytest
import os.path
import time
import datetime
from .test_tools import url_validator, date_validator
from ..drive_logic import Drive, DriveFolderNotFound
from ..instagram_bot import IGBOT

TEST_TRACK_ID = "1LwTsb1fsXpT9TkWcMAWWboxoF5kqcSzA"
TEST_TRACK_LINK = f'https://drive.google.com/file/d/{TEST_TRACK_ID}/view?usp=sharing'
LOCATION = 'Destino Ibiza'
LOCATION_DIR_ID = "1qdjeWMxkmKr-T1V2HFXPIoHR-OFNzQC_"
LOCATION2 = "Art Club"
NON_EXISTENT_LOCATION = 'RISHON_LETZION'
EXISTENT_LOCATION_NAME = LOCATION
STORY_STORY_LOCATIONS_DIR_ID = "178oc91hM5JbzdLQtyUvOdblmdq9pr2oG"
DATE = datetime.datetime(2023, 10, 13).date()
DATE2 = datetime.datetime(2023, 10, 1).date()
TODAY_DATE = datetime.datetime.today().date()


@pytest.fixture
def drive():
    return Drive()

# Build query
# Dir query


def test_build_get_dir_query_with_dir_name():
    dir_query = Drive.build_get_dir_query(dir_name=LOCATION)
    assert f"mimeType = 'application/vnd.google-apps.folder' and name contains '\"{LOCATION}\"'" == dir_query


def test_build_get_dir_query_with_parent_dir():
    dir_query = Drive.build_get_dir_query(
        parent_dir_id=STORY_STORY_LOCATIONS_DIR_ID)
    assert f"mimeType = 'application/vnd.google-apps.folder' and '{STORY_STORY_LOCATIONS_DIR_ID}' in parents" == dir_query


# Videos query

def test_build_get_videos_from_dir_query_with_parent_dir():
    videos_query = Drive.build_get_videos_from_dir_query(
        dir_id=STORY_STORY_LOCATIONS_DIR_ID)
    assert f"mimeType contains 'video/' and '{STORY_STORY_LOCATIONS_DIR_ID}' in parents" == videos_query


def test_build_get_videos_from_dir_query_with_date_range():
    videos_query = Drive.build_get_videos_from_dir_query(
        date=DATE, date_end=TODAY_DATE)
    assert f"mimeType contains 'video/' and createdTime >= '{DATE}T00:00:00' and createdTime <= '{TODAY_DATE}T23:59:59'" == videos_query


def test_build_get_videos_from_dir_query_with_single_date():
    videos_query = Drive.build_get_videos_from_dir_query(date=DATE)
    assert f"mimeType contains 'video/' and createdTime >= '{DATE}T00:00:00' and createdTime <= '{DATE}T23:59:59'" == videos_query


def test_build_get_videos_from_dir_query_with_location():
    videos_query = Drive.build_get_videos_from_dir_query(location=LOCATION)
    assert f"mimeType contains 'video/' and fullText contains '\"{LOCATION}\"'" == videos_query


def test_build_get_videos_from_dir_query_with_all_parameters():
    videos_query = Drive.build_get_videos_from_dir_query(
        dir_id=STORY_STORY_LOCATIONS_DIR_ID, date=DATE, date_end=TODAY_DATE, location=LOCATION)
    expected_query = f"mimeType contains 'video/' and '{STORY_STORY_LOCATIONS_DIR_ID}' in parents and createdTime >= '{DATE}T00:00:00' and createdTime <= '{TODAY_DATE}T23:59:59' and fullText contains '\"{LOCATION}\"'"
    assert expected_query == videos_query


# Use query

def test_get_dir_id(drive):
    dir_query = drive.build_get_dir_query(
        dir_name=LOCATION, parent_dir_id=STORY_STORY_LOCATIONS_DIR_ID)
    dir_id = drive.get_dir_id(query=dir_query, dir_name=LOCATION)
    assert LOCATION_DIR_ID == dir_id


def test_get_files_from_dir(drive):
    videos_query = drive.build_get_videos_from_dir_query(dir_id=LOCATION_DIR_ID, date=DATE)
    drive_videos = drive.get_files_from_dir(query=videos_query)

    assert drive_videos
    for video in drive_videos:
        assert str(DATE) in video['created_time']


def test_get_story_story_locations_dir_id(drive):
    story_story_locations_dir_id = drive.get_story_story_locations_dir_id()
    assert STORY_STORY_LOCATIONS_DIR_ID == story_story_locations_dir_id


def test_get_dirs_in_parent_dir(drive):
    dir_name = "Story-Story Stories"
    story_story_main_dir_query = drive.build_get_dir_query(dir_name=dir_name)
    story_story_main_dir_id = drive.get_dir_id(query=story_story_main_dir_query, dir_name=dir_name)
    story_story_dirs = drive.get_dirs_in_parent_dir(parent_dir_id=story_story_main_dir_id)
    assert story_story_dirs

    for directory in story_story_dirs:
        assert directory['name'] == 'STORY_STORY_LOCATIONS' or directory['name'] == 'STORY_STORY_USERS'


# Videos dates

def test_get_videos_at_date_in_dir(drive):
    locations_dir_id = drive.get_story_story_locations_dir_id()
    drive_location_folder_id = drive.get_dir_id_with_parent(
        parent_dir_id=locations_dir_id, dir_name=LOCATION)
    drive_videos = drive.get_videos_at_date_from_dir(dir_id=drive_location_folder_id,
                                                     year=DATE.year,
                                                     month=DATE.month,
                                                     day=DATE.day)
    assert drive_videos
    for video in drive_videos:
        assert str(DATE) in video['created_time']


def test_get_videos_at_date_range_from_dir(drive):
    drive_videos = drive.get_videos_at_date_range_from_dir(dir_name=LOCATION, parent_dir_id=STORY_STORY_LOCATIONS_DIR_ID,
                                                           start_year=DATE.year, start_month=DATE.month, start_day=DATE.day,
                                                           end_year=TODAY_DATE.year, end_month=TODAY_DATE.month, end_day=TODAY_DATE.day)
    assert drive_videos
    for video in drive_videos:
        created_time = datetime.datetime.strptime(video['created_time'], "%Y-%m-%dT%H:%M:%S.%fZ").date()
        assert DATE <= created_time <= TODAY_DATE


def test_get_dir_videos_dates(drive):
    drive_dir_dates = drive.get_dir_videos_dates(dir_name=LOCATION, parent_dir_id=STORY_STORY_LOCATIONS_DIR_ID)
    for date in drive_dir_dates:
        created_time = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        assert created_time <= TODAY_DATE


def test_get_locations_and_dates(drive):
    locations_and_dates = drive.get_locations_and_dates(locations_dir_id=STORY_STORY_LOCATIONS_DIR_ID)
    assert EXISTENT_LOCATION_NAME in [location['location'] for location in locations_and_dates]
    assert date_validator(locations_and_dates[0]['dates'][0])


# Get today information

def test_get_today_locations_stories_usernames(drive):
    usernames_to_download_by_location = drive.get_today_locations_stories_usernames(locations_dir_id=STORY_STORY_LOCATIONS_DIR_ID)
    assert EXISTENT_LOCATION_NAME in [usernames_locations['location'] for usernames_locations in usernames_to_download_by_location]


# Custom Error test

def test_non_existent_location(drive):
    nonexistent_location_dir_query = drive.build_get_dir_query(dir_name=NON_EXISTENT_LOCATION)
    with pytest.raises(DriveFolderNotFound):
        _ = drive.get_dir_id(query=nonexistent_location_dir_query, dir_name=NON_EXISTENT_LOCATION)


# Downloads

def test_get_download_link(drive):
    locations_dir_id = drive.get_story_story_locations_dir_id()
    get_location_query = drive.build_get_dir_query(parent_dir_id=locations_dir_id, dir_name=LOCATION)
    drive_location_folder_id = drive.get_dir_id(query=get_location_query, dir_name=NON_EXISTENT_LOCATION)
    drive_videos = drive.get_videos_at_date_from_dir(dir_id=drive_location_folder_id,
                                                     year=TODAY_DATE.year,
                                                     month=TODAY_DATE.month,
                                                     day=TODAY_DATE.day)
    link = drive.get_download_link(drive_videos[0]['id'])
    assert url_validator(link)


def test_download_files(drive):
    downloaded_files = drive.download_files(dir_name=LOCATION2, parent_dir_id=drive.STORY_STORY_LOCATIONS_DIR_ID,
                                            start_year=DATE2.year, end_year=DATE2.year,
                                            start_month=DATE2.month, end_month=DATE2.month,
                                            start_day=DATE2.day, end_day=DATE2.day)
    for file in downloaded_files:
        assert os.path.exists(file['path'])


# Video link

def test_get_video_link(drive):
    drive_videos = drive.get_videos_at_date_range_from_dir(dir_name=LOCATION, parent_dir_id=STORY_STORY_LOCATIONS_DIR_ID,
                                                           start_year=DATE.year, end_year=DATE2.year,
                                                           start_month=DATE.month, end_month=DATE2.month,
                                                           start_day=DATE.day, end_day=DATE2.day)
    for video in drive_videos:
        url = drive.get_video_link(video['id'])
        assert url_validator(url)


def test_get_id_from_sharable_link(drive):
    track_id = drive.get_id_from_sharable_link(TEST_TRACK_LINK)
    assert track_id == TEST_TRACK_ID


# Upload video

def test_upload_story_for_sync(drive):
    today_locations_usernames = drive.get_today_locations_stories_usernames(locations_dir_id=drive.STORY_STORY_LOCATIONS_DIR_ID)
    if not today_locations_usernames:
        pytest.skip("Locations followed do not have any location stories. Skipping test.")
    location = today_locations_usernames[0]['location']
    username = today_locations_usernames[0]['usernames'][0]
    igbot = IGBOT()
    user_stories_metadata = igbot.get_user_stories_metadata(username=username)
    story_id = user_stories_metadata[0]['id']
    downloaded_story_metadata = igbot.download_story(story_metadata=user_stories_metadata[0],
                                                     username=username,
                                                     location=location)
    story_name = f"{location}-{TODAY_DATE}-{story_id}-{username}"
    assert downloaded_story_metadata['name'] == f"{story_name}.mp4"
    drive.upload_story_for_sync(dir_id=drive.SPOT_LOCATIONS_DIR_ID, story_metadata=user_stories_metadata[0], location=location, username=username)
    time.sleep(15)
    videos_in_spot_dir = drive.get_videos_at_date_from_dir(dir_id=drive.SPOT_LOCATIONS_DIR_ID)
    assert story_name in [video['name'] for video in videos_in_spot_dir]
