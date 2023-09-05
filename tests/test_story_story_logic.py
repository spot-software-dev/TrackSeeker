from story_story_logic import StoryStorySession
from time import sleep


NAME = "Yost Koen"
LOCATION = 1606276279607269


def test_get_instagram_locations():
    session = StoryStorySession()
    locations = session.get_instagram_followed_locations_and_dates(NAME)
    assert len(locations) > 2
    assert type(locations[0]['name']) is str
    assert len(locations[0]['location_dates']) > 1


def test_add_location():
    session = StoryStorySession()
    locations_before = session.get_instagram_followed_locations_and_dates(NAME)
    sleep(1)
    session = StoryStorySession()
    session.add_location(NAME, LOCATION)
    sleep(1)
    session = StoryStorySession()
    locations_after = session.get_instagram_followed_locations_and_dates(NAME)
    assert len(locations_after) > len(locations_before)
