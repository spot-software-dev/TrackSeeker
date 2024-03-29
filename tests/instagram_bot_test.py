import pytest
import os
from tests import TESTS_DIR
STORIES_TESTS_DIR = os.path.join(TESTS_DIR, 'test_instagram_bot_media')
os.environ['STORIES_DIR_PATH'] = STORIES_TESTS_DIR
from instagram_bot import IGBOT

TEST_IG_USERNAME = 'yula.bar'
TEST_IG_ID = '8539536167'


def clean_stories_test_directory():
    """Removes all files in the """
    if os.listdir(STORIES_TESTS_DIR):
        for path in [os.path.join(STORIES_TESTS_DIR, path) for path in os.listdir(STORIES_TESTS_DIR)]:
            os.remove(path)


@pytest.fixture
def bot():
    return IGBOT()


@pytest.fixture()
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


def test_download_user_stories_as_videos(bot, setup):
    stories = bot.download_user_stories_as_videos(TEST_IG_ID)
    test_dir_content = os.listdir(STORIES_TESTS_DIR)
    assert all(extension == '.mp4' for extension in map(lambda path: os.path.splitext(path)[1], test_dir_content))
    assert all([f"{story['id']}.mp4" in test_dir_content for story in stories.values()])


def test_convert_story_videos_to_audio(bot):
    bot.convert_story_videos_to_audio()
    assert '.mp3' in map(lambda path: os.path.splitext(path)[1], os.listdir(STORIES_TESTS_DIR))


def test_download_user_stories(bot, setup):
    stories = bot.download_user_stories(TEST_IG_ID)
    test_dir_audio_content = [path for path in os.listdir(STORIES_TESTS_DIR) if path.endswith('.mp3')]
    assert all([f"{story['id']}.mp3" in test_dir_audio_content for story in stories.values()])


def test_get_audio_urls_from_post_location_id(bot):
    location_audios = bot.get_audio_urls_from_post_location_id(1977542)  # Location ID of "Beit Haamudim"
    first_url = list(location_audios.values())[0][0]
    assert first_url.startswith("https://instagram")
