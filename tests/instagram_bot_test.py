import pytest
import os
from time import sleep
from tests import TESTS_DIR
STORIES_TESTS_DIR = os.path.join(TESTS_DIR, 'stories')
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
    # Happens before each test
    if os.listdir(STORIES_TESTS_DIR):
        clean_stories_test_directory()
    yield  # Does nothing


@pytest.fixture()
def teardown():
    yield  # Does nothing
    if os.listdir(STORIES_TESTS_DIR):
        clean_stories_test_directory()


def test_user_id(bot):
    yula_id = bot.get_user_id(TEST_IG_USERNAME)
    assert (yula_id == TEST_IG_ID)


def test_download_user_stories_as_videos(bot, setup):
    stories = bot.download_user_stories_as_videos(TEST_IG_ID)
    test_dir_content = os.listdir(STORIES_TESTS_DIR)
    assert all(extension == '.mp4' for extension in map(lambda path: os.path.splitext(path)[1], test_dir_content))
    assert all([f"{story['id']}.mp4" in test_dir_content for story in stories.values()])


def test_convert_story_videos_to_audio(bot):
    bot.convert_story_videos_to_audio()
    assert '.mp3' in map(lambda path: os.path.splitext(path)[1], os.listdir(STORIES_TESTS_DIR))


def test_download_user_stories(bot, setup, teardown):
    stories = bot.download_user_stories(TEST_IG_ID)
    test_dir_audio_content = [path for path in os.listdir(STORIES_TESTS_DIR) if path.endswith('.mp3')]
    assert all([f"{story['id']}.mp3" in test_dir_audio_content for story in stories.values()])
    sleep(0.01)
