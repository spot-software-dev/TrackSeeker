import pytest
import os
from music_recognition import recognize

DIR_PATH = os.path.dirname(os.path.realpath(__file__))


def test_existing_track_wav():
    assert recognize(os.path.join(DIR_PATH, 'red_samba_sample.wav'))


def test_existing_track_aac():
    assert recognize(os.path.join(DIR_PATH, 'red_samba_sample.aac'))


def test_non_existing_track_aac():
    assert not recognize(os.path.join(DIR_PATH, 'Panoramaxx_sample.aac'))


def test_non_existing_famous_track():
    assert not recognize(os.path.join(DIR_PATH, 'Billie_Jean_sample.wav'))
