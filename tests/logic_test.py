from tests.test_tools import url_validator
from logic import location_logic, get_stories_not_in_acrcloud_container
from music_recognition import list_container_files_and_results

LOCATION = 'art club'


def test_location_logic(drive):
    recognized_stories = location_logic(location=LOCATION, drive=drive, day=26, month=8, year=2023, end_day=26, end_month=8, end_year=2023)
    print(f"Recognized Stories: {recognized_stories}")
    first_story_url = recognized_stories[0]['drive_url']
    first_story_download_url = recognized_stories[0]['download_url']
    assert url_validator(first_story_url)
    assert url_validator(first_story_download_url)


def test_get_stories_not_in_acrcloud_container(drive):
    acrcloud_recognition_results = list_container_files_and_results()
    acrcloud_files_urls = [story_recognition['drive_url'] for story_recognition in acrcloud_recognition_results]
    acrcloud_files_ids = [drive.get_id_from_sharable_link(acrcloud_file_url) for acrcloud_file_url in
                          acrcloud_files_urls]
    stories_to_add = get_stories_not_in_acrcloud_container(drive)
    assert all([story['id'] not in acrcloud_files_ids for story in stories_to_add])
