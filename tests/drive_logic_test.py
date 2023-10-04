import pytest
import os.path
import datetime
from tests.test_tools import url_validator, date_validator
from drive_logic import Drive, DriveLocationNotFound

TEST_TRACK_ID = "1LwTsb1fsXpT9TkWcMAWWboxoF5kqcSzA"
TEST_TRACK_LINK = f'https://drive.google.com/file/d/{TEST_TRACK_ID}/view?usp=sharing'
LOCATION = 'selina mantur'
NON_EXISTENT_LOCATION = 'RISHON_LETZION'
EXISTENT_LOCATION_NAME = 'Mantur Beit Oren by Selina'
DASHBOARD = "Yost Koen"
DATE = datetime.date(2023, 8, 24)


@pytest.fixture
def drive():
    return Drive()


def test_download_files(drive):
    downloaded_files = drive.download_files(location=LOCATION,
                                            start_year=DATE.year, end_year=DATE.year,
                                            start_month=DATE.month, end_month=DATE.month,
                                            start_day=DATE.day, end_day=DATE.day)
    assert os.path.exists(downloaded_files[0]['path'])


def test_non_existent_location(drive):
    with pytest.raises(DriveLocationNotFound):
        _ = drive.get_location_directory(location=NON_EXISTENT_LOCATION)


def test_get_file_link(drive):
    drive_files = drive.get_files(location=LOCATION,
                                  start_year=DATE.year, end_year=DATE.year,
                                  start_month=DATE.month, end_month=DATE.month,
                                  start_day=DATE.day, end_day=DATE.day)
    for file in drive_files:
        url = drive.get_file_link(file['id'])
        assert url_validator(url)


def test_get_files(drive):
    drive_files = drive.get_files(location=LOCATION,
                                  start_year=DATE.year, end_year=DATE.year,
                                  start_month=DATE.month, end_month=DATE.month,
                                  start_day=DATE.day, end_day=DATE.day + 1)
    assert str(DATE) in drive_files[0]['name']
    assert str(DATE.replace(day=DATE.day + 1)) in drive_files[-1]['name']


def test_get_files_at_date_in_folder(drive):
    drive_location_folder_id = drive.get_location_directory(LOCATION)
    drive_files = drive.get_files_at_date_in_folder(folder_id=drive_location_folder_id,
                                                    year=DATE.year,
                                                    month=DATE.month,
                                                    day=DATE.day)
    for file in drive_files:
        assert str(DATE) in file['name']


def test_get_download_link(drive):
    drive_location_folder_id = drive.get_location_directory(LOCATION)
    drive_files = drive.get_files_at_date_in_folder(folder_id=drive_location_folder_id,
                                                    year=DATE.year,
                                                    month=DATE.month,
                                                    day=DATE.day)
    link = drive.get_download_link(drive_files[0]['id'])
    assert url_validator(link)


def test_get_location_dates(drive):
    location_dates = drive.get_location_dates(LOCATION)
    assert date_validator(location_dates[0])


def test_get_locations_and_dates(drive):
    locations_and_dates = drive.get_locations_and_dates(DASHBOARD)
    assert EXISTENT_LOCATION_NAME in [location['name'] for location in locations_and_dates]
    assert date_validator(locations_and_dates[0]['location_dates'][0])


def test_get_id_from_sharable_link(drive):
    track_id = drive.get_id_from_sharable_link(TEST_TRACK_LINK)
    assert track_id == TEST_TRACK_ID
