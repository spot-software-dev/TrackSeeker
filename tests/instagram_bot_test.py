import pytest
import os
import datetime
from tests import TESTS_DIR
STORIES_TESTS_DIR = os.path.join(TESTS_DIR, 'test_instagram_bot_media')
os.environ['STORIES_DIR_PATH'] = STORIES_TESTS_DIR
from instagram_bot import IGBOT

date_now = datetime.date.today()

TEST_IG_USERNAME = 'pachaofficial'
TEST_IG_ID = '212110630'


def clean_stories_test_directory():
    """Removes all files in the """
    if os.listdir(STORIES_TESTS_DIR):
        for path in [os.path.join(STORIES_TESTS_DIR, path) for path in os.listdir(STORIES_TESTS_DIR)]:
            os.remove(path)


@pytest.fixture
def bot():
    return IGBOT()


@pytest.fixture
def setup():
    # Happens before test
    if os.listdir(STORIES_TESTS_DIR):
        clean_stories_test_directory()


def test_user_id(bot):
    test_id = bot.get_user_id(TEST_IG_USERNAME)
    assert test_id == TEST_IG_ID


def test_get_userinfo(bot):
    test_username = bot.get_userinfo(TEST_IG_ID)['username']
    assert test_username == TEST_IG_USERNAME


def test_download_story(bot, setup):
    stories_metadata = bot.get_user_stories_metadata(TEST_IG_USERNAME)
    stories = bot.download_story(stories_metadata, TEST_IG_USERNAME)
    test_dir_content = os.listdir(STORIES_TESTS_DIR)
    assert all([f"{date_now}-{story['id']}-{TEST_IG_USERNAME}.mp4" in test_dir_content for story in stories["stories"]])


def test_get_audio_urls_from_post_location_id(bot):
    location_audios = bot.get_audio_urls_from_post_location_id(1977542)  # Location ID of "Beit Haamudim"
    first_url = list(location_audios.values())[0][0]
    assert first_url.startswith("https://instagram")
