import os
from dotenv.main import load_dotenv
load_dotenv()

TESTS_DIR = os.path.dirname(os.path.realpath(__file__))
STORIES_TESTS_DIR = os.path.join(TESTS_DIR, 'test_instagram_bot_media')
MEDIA_TESTS_DIR = os.path.join(TESTS_DIR, 'media')
os.environ['STORIES_DIR_PATH'] = STORIES_TESTS_DIR
