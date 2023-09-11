import os
import io
import pytest
from ..music_recognition import recognize, get_files_in_db, upload_to_db_protected, delete_id_from_db
from ..music_recognition import get_id_from_title, get_musical_metadata, get_human_readable_db
from ..music_recognition import delete_from_db, delete_id_from_db_protected_for_web, MusicDuplicationError

DIR_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'media')

TEST_TRACKS_IN_DB = ['intro + sound the system', 'Alawan', 'Red Samba', 'Billie Jean']
TEST_TRACK_LINK = 'https://drive.google.com/file/d/1LwTsb1fsXpT9TkWcMAWWboxoF5kqcSzA/view?usp=sharing'

TEST_FILE_CONTENT = open(os.path.join(DIR_PATH, 'Raggae_Soundsystem_intro.mp3'), 'rb').read()
TEST_UPLOADED_FILE = io.BytesIO(TEST_FILE_CONTENT)
TEST_UPLOADED_FILE.filename = 'Raggae_Soundsystem_intro.mp3'  # Set the filename attribute
WRONG_FILE_FORMAT = os.path.join(DIR_PATH, 'wrong_file_format.txt')


@pytest.fixture()
def cleanup():
    """Delete audio file from database after test"""
    file_to_delete = 'intro + sound the system'
    db = get_files_in_db()
    files_in_db = get_musical_metadata(db)
    if file_to_delete in list(files_in_db):
        file_id = get_id_from_title(db, file_to_delete)
        delete_id_from_db(file_id)
    yield
    db = get_files_in_db()
    files_in_db = get_musical_metadata(db)
    if file_to_delete in list(files_in_db):
        file_id = get_id_from_title(db, file_to_delete)
        delete_id_from_db(file_id)


@pytest.fixture()
def wrong_file_format_setup():
    """If not existent, create a .txt file to be recognized."""
    if not os.path.exists(WRONG_FILE_FORMAT):
        with open(WRONG_FILE_FORMAT, 'w') as file:
            text_input = "lorem ipsum"
            file.write(text_input)


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


def test_music_recognition_error(wrong_file_format_setup):
    assert not recognize(os.path.join(DIR_PATH, 'wrong_file_format.txt'))
    assert not os.path.exists(WRONG_FILE_FORMAT)


def test_get_files_in_db():
    assert type(get_files_in_db()) is dict


def test_upload_to_db_protected(cleanup):
    db_start = get_files_in_db()
    added_track_title = 'intro + sound the system'
    upload_to_db_protected(
        TEST_UPLOADED_FILE,
        title=added_track_title,
        artist='Jenja & The Band'
    )
    db_end = get_files_in_db()
    assert len(db_start['data']) < len(db_end['data'])

    end_db_titles = []
    for track_num in range(len(db_end['data'])):
        end_db_titles.append(db_end['data'][track_num]['title'])
    assert added_track_title in end_db_titles


def test_upload_to_db_duplicate_error(cleanup):
    added_track_title = 'intro + sound the system'
    upload_to_db_protected(
        TEST_UPLOADED_FILE,
        title=added_track_title,
        artist='Jenja & The Band'
    )

    with pytest.raises(MusicDuplicationError):
        upload_to_db_protected(
            TEST_UPLOADED_FILE,
            title=added_track_title,
            artist='Jenja & The Band'
        )


def test_get_ids_and_titles():
    db = get_files_in_db()
    db_files_ids = [file['id'] for file in db['data']]
    db_files_titles = [file['title'] for file in db['data']]
    titles_ids_db = get_musical_metadata(db)
    for file_title, file_id in list(map(lambda metadata: (metadata[0], metadata[1]['id']), titles_ids_db.items())):
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
    upload_to_db_protected(
        TEST_UPLOADED_FILE,
        title=added_track_title,
        artist='Jenja & The Band'
    )
    db_before_delete = get_files_in_db()
    delete_from_db(added_track_title)
    db_after_delete = get_files_in_db()
    assert db_after_delete != db_before_delete
    assert added_track_title not in db_after_delete


def test_delete_id_from_db_protected_for_web(cleanup):
    added_track_title = 'intro + sound the system'
    upload_to_db_protected(
        TEST_UPLOADED_FILE,
        title=added_track_title,
        artist='Jenja & The Band'
    )
    db_before_delete = get_files_in_db()
    file_id = get_id_from_title(db_before_delete, added_track_title)
    delete_id_from_db_protected_for_web(file_id)
    db_after_delete = get_files_in_db()
    assert db_after_delete != db_before_delete
    assert added_track_title not in db_after_delete


def test_list_container_files_and_results():
    results = list_container_files_and_results()
    assert issubclass(type(results), dict)


def test_add_to_container_recognizer():
    response = add_to_container_recognizer(TEST_TRACK_LINK)
    time.sleep(5)
    assert list_container_files_and_results()['data']
