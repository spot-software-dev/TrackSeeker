import unittest
import os
from music_recognition import recognize

DIR_PATH = os.path.dirname(os.path.realpath(__file__))


class MyTestCase(unittest.TestCase):
    def test_existing_track_wav(self):
        self.assertEqual(recognize(os.path.join(DIR_PATH, 'red_samba_sample.wav')), True)

    def test_existing_track_aac(self):
        self.assertEqual(recognize(os.path.join(DIR_PATH, 'red_samba_sample.aac')), True)

    def test_non_existing_track_aac(self):
        self.assertEqual(recognize(os.path.join(DIR_PATH, 'Panoramaxx_sample.aac')), False)

    def test_non_existing_famous_track(self):
        self.assertEqual(recognize(os.path.join(DIR_PATH, 'Billie_Jean_sample.wav')), False)


if __name__ == '__main__':
    unittest.main()
