from datetime import datetime
from loguru import logger
from os import path
from .instagram_bot import IGBOT
from .gui import GUI
from .music_recognition import recognize, MusicRecognitionError

MAIN_DIR = path.abspath(__file__)
time_now = datetime.now()
logger.add(path.join(MAIN_DIR, 'logs', f"music_recognition_{time_now.strftime('%x')}.log"), rotation="1 day")


def main():
    gui = GUI()
    gui.run_gui()
    username = input("Enter Exact Username: ")
    instagram_bot = IGBOT()
    stories_music = instagram_bot.instagram_search(username)
    recognised_list = []
    for story in stories_music:
        try:
            recognition_result = recognize(story)
            if recognition_result:
                recognised_list.append(story)
        except MusicRecognitionError as e:
            logger.critical(f"Error occurred while recognizing music from story ({story})\n\tError message: {e}")
            # TODO: Display error message to user and ask to re-enter the file or reach support
            continue
    if recognised_list:
        for story in recognised_list:
            gui.display_links(story)
    else:
        gui.display_no_links()


if __name__ == '__main__':
    main()
