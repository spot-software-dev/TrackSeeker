import pytest
import os
import datetime
from tests import STORIES_TESTS_DIR
STORIES_TESTS_DIR = os.path.join(TESTS_DIR, 'test_instagram_bot_media')
os.environ['STORIES_DIR_PATH'] = STORIES_TESTS_DIR

date_now = datetime.date.today()

TEST_IG_USERNAME = 'pachaofficial'
TEST_IG_ID = '212110630'
TEST_LOCATION = 'Pacha'


@pytest.fixture
def setup(igbot):
    igbot.clean_stories_directory()


def test_user_id(igbot):
    test_id = igbot.get_user_id(TEST_IG_USERNAME)
    assert test_id == TEST_IG_ID


def test_get_userinfo(igbot):
    test_username = igbot.get_userinfo(TEST_IG_ID)['username']
    assert test_username == TEST_IG_USERNAME


def test_download_story(igbot, setup):
    stories_metadata = igbot.get_user_stories_metadata(TEST_IG_USERNAME)
    stories = []
    for story in stories_metadata:
        igbot.download_story(story, TEST_IG_USERNAME, TEST_LOCATION)
    test_dir_content = os.listdir(STORIES_TESTS_DIR)
    assert all([f"{date_now}-{story['id']}-{TEST_IG_USERNAME}.mp4" in test_dir_content for story in stories])
