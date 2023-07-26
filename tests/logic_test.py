import pytest
from logic import logic

YULA_BAR_USERNAME = 'yula.bar'
SHAKED_BEN_BARUCH_USERNAME = 'shaked.b.b'
SHAKED_WORK_USERNAME = 'shakedbbaruch'
PROFILES_WITHOUT_RECOGNIZED_MUSIC = [YULA_BAR_USERNAME, SHAKED_BEN_BARUCH_USERNAME]
PROFILES_WITH_RECOGNIZED_MUSIC = [SHAKED_WORK_USERNAME]


@pytest.mark.parametrize('profile', PROFILES_WITH_RECOGNIZED_MUSIC)
def test_logic(profile):
    recognized_songs = logic(profile)
    assert recognized_songs[0]['title'] == 'intro + sound the system'
    assert len(recognized_songs) == 1


@pytest.mark.parametrize('profile', PROFILES_WITHOUT_RECOGNIZED_MUSIC)
def test_blank_logic(profile):
    recognized_songs = logic(profile)
    assert not recognized_songs
