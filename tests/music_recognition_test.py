import os
import pytest
from music_recognition import recognize, get_files_in_db, upload_to_db, delete_id_from_db
from music_recognition import get_id_from_title, get_ids_and_titles, MusicRecognitionError, get_human_readable_db, delete_from_db

DIR_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'media')
TEST_TRACKS_IN_DB = ['intro + sound the system', 'Alawan', 'Red Samba', 'Billie Jean']


@pytest.fixture()
def cleanup():
    """Delete audio file from database after test"""
    file_to_delete = 'intro + sound the system'
    db = get_files_in_db()
    files_in_db = get_ids_and_titles(db)
    if file_to_delete in list(files_in_db):
        file_id = get_id_from_title(db, file_to_delete)
        delete_id_from_db(file_id)
    yield
    db = get_files_in_db()
    files_in_db = get_ids_and_titles(db)
    if file_to_delete in list(files_in_db):
        file_id = get_id_from_title(db, file_to_delete)
        delete_id_from_db(file_id)


def test_existing_track_wav():
    assert recognize(os.path.join(DIR_PATH, 'red_samba_sample.wav'))


def test_existing_track_aac():
    assert recognize(os.path.join(DIR_PATH, 'red_samba_sample.aac'))


def test_non_existing_track_aac():
    assert not recognize(os.path.join(DIR_PATH, 'Panoramaxx_sample.aac'))


def test_non_existing_famous_track():
    assert not recognize(os.path.join(DIR_PATH, 'Space_Oddity_sample.wav'))


def test_existing_famous_track():
    assert recognize(os.path.join(DIR_PATH, 'Billie_Jean_sample.wav'))


def test_music_recognition_error():
    with pytest.raises(MusicRecognitionError):
        recognize(os.path.join(DIR_PATH, 'wrong_file_format.txt'))


def test_get_files_in_db():
    assert type(get_files_in_db()) is dict


def test_upload_to_db(cleanup):
    db_start = get_files_in_db()
    added_track_title = 'intro + sound the system'
    upload_to_db(
        os.path.join(DIR_PATH, 'Raggae_Soundsystem_intro.mp3'),
        title=added_track_title,
        artist='Jenja & The Band'
    )
    db_end = get_files_in_db()
    assert len(db_start['data']) < len(db_end['data'])

    end_db_titles = []
    for track_num in range(len(db_end['data'])):
        end_db_titles.append(db_end['data'][track_num]['title'])
    assert added_track_title in end_db_titles


def test_get_ids_and_titles():
    db = get_files_in_db()
    db_files_ids = [file['id'] for file in db['data']]
    db_files_titles = [file['title'] for file in db['data']]
    titles_ids_db = get_ids_and_titles(db)
    for file_title, file_id in titles_ids_db.items():
        assert file_id in db_files_ids
        assert file_title in db_files_titles


def test_get_id_from_title():
    db = get_files_in_db()
    assert type(get_id_from_title(db, 'Red Samba')) == int


def test_get_human_readable_db():
    db = get_human_readable_db()
    db_tracks_titles = [track['title'] for track in db]
    for track in TEST_TRACKS_IN_DB:
        assert track in db_tracks_titles


def test_delete_from_db(cleanup):   
    added_track_title = 'intro + sound the system'
    upload_to_db(
        os.path.join(DIR_PATH, 'Raggae_Soundsystem_intro.mp3'),
        title=added_track_title,
        artist='Jenja & The Band'
    )
    db_before_delete = get_files_in_db()
    delete_from_db(added_track_title)
    db_after_delete = get_files_in_db()
    assert db_after_delete != db_before_delete
    assert added_track_title not in db_after_delete
