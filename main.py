from logic import logic
from music_recognition import get_human_readable_db, upload_to_db_protected


def main():
    print(f"Tracks in the database are:\n{get_human_readable_db()}")
    upload_answer = input("Would you like to upload a file? (Y/N): ")
    if upload_answer == 'Y':
        file_path = input("Enter audio file full path to upload to your tracks database: ")
        title = input("What is the title for this song? ")
        album = input("And what is the name of the album? ")
        artist = input("And finally by what artist? ")
        print("Thank you, the upload starts now. It might take a while.")
        upload_to_db_protected(file_path, title, artist, album)
        print(f"Great! Your track is now in the database:\n{get_human_readable_db()}")
    username = input("Enter the exact username of the wanted profile to check its stories: ")
    recognized_tracks = logic(username)
    if recognized_tracks:
        print(f"Recognized {len(recognized_tracks)} tracks!")
        for track in recognized_tracks:
            print(f'Title: "{track["title"]}" Album: {track["album"]}')
    else:
        print("Didn't recognize any of your tracks in the user stories")


if __name__ == '__main__':
    main()
