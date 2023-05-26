import unittest
import os
from music_recognition import recognize

TESTS_DIR = os.path.dirname(os.path.realpath(__file__))
MEDIA_TESTS_DIR = os.path.join(TESTS_DIR, 'media')


class MyTestCase(unittest.TestCase):
    def test_existing_track_wav(self):
        audio_path = os.path.join(MEDIA_TESTS_DIR, 'red_samba_sample.wav')
        self.assertEqual(recognize(audio_path), 'Success')

    def test_existing_track_aac(self):
        audio_path = os.path.join(MEDIA_TESTS_DIR, 'red_samba_sample.aac')
        self.assertEqual(recognize(audio_path), 'Success')

    def test_non_existing_track_aac(self):
        audio_path = os.path.join(MEDIA_TESTS_DIR, 'Panoramaxx_sample.aac')
        self.assertEqual(recognize(audio_path), 'No result')

    def test_existing_famous_track(self):
        audio_path = os.path.join(MEDIA_TESTS_DIR, 'Billie_Jean_sample.wav')
        self.assertEqual(recognize(audio_path), 'Success')

    def test_non_existing_famous_track(self):
        audio_path = os.path.join(MEDIA_TESTS_DIR, 'Space_Oddity_sample.wav')
        self.assertEqual(recognize(audio_path), 'No result')


if __name__ == '__main__':
    unittest.main()
