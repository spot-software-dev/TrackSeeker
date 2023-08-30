import pytest
import os.path
from tests.test_tools import url_validator
import datetime
from logic import logic, location_logic

YULA_BAR_USERNAME = 'yula.bar'
SHAKED_BEN_BARUCH_USERNAME = 'shaked.b.b'
SHAKED_WORK_USERNAME = 'shakedbbaruch'
PROFILES_WITHOUT_RECOGNIZED_MUSIC = [YULA_BAR_USERNAME, SHAKED_BEN_BARUCH_USERNAME]
PROFILES_WITH_RECOGNIZED_MUSIC = [SHAKED_WORK_USERNAME]

LOCATION = 'selina mantur'
LOCATION2 = 'art club'
NON_EXISTENT_LOCATION = 'RISHON_LETZION'
DATE = datetime.date(2023, 8, 24)

DIR_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'DownloadedStories')


@pytest.mark.parametrize('profile', PROFILES_WITH_RECOGNIZED_MUSIC)
def test_logic(profile):
    recognized_songs = logic(profile)
    assert recognized_songs[0]['title'] == 'intro + sound the system'
    assert len(recognized_songs) == 1


@pytest.mark.parametrize('profile', PROFILES_WITHOUT_RECOGNIZED_MUSIC)
def test_blank_logic(profile):
    recognized_songs = logic(profile)
    assert not recognized_songs


def test_location_logic():
    recognized_stories = location_logic(location=LOCATION2, day=26)
    print(f"Recognized Stories: {recognized_stories}")
    first_story_url = recognized_stories[0]['drive_url']
    first_story_download_url = recognized_stories[0]['download_url']
    assert url_validator(first_story_url)
    assert url_validator(first_story_download_url)
