import pytest
import os.path
import datetime
from tests.test_tools import url_validator
from drive_logic import Drive, DriveLocationNotFound

LOCATION = 'selina mantur'
NON_EXISTENT_LOCATION = 'RISHON_LETZION'
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
        _ = drive.get_location_directory(similar_name=NON_EXISTENT_LOCATION)


def test_get_file_link(drive):
    drive_files = drive.get_files(similar_name=LOCATION,
                                  start_year=DATE.year, end_year=DATE.year,
                                  start_month=DATE.month, end_month=DATE.month,
                                  start_day=DATE.day, end_day=DATE.day)
    for file in drive_files:
        url = drive.get_file_link(file['id'])
        assert url_validator(url)


def test_get_files(drive):
    drive_files = drive.get_files(similar_name=LOCATION,
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
