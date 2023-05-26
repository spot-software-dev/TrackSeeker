from .instagram_bot import IGBOT
from .gui import GUI
from .music_recognition import recognize


def recognition_error_handler(error_msg: str) -> None:
    raise NotImplementedError  # TODO: Handle recognition error


def main():
    gui = GUI()
    gui.run_gui()
    username = input("Enter Exact Username: ")
    instagram_bot = IGBOT()
    stories_music = instagram_bot.instagram_search(username)
    recognised_list = []
    for story in stories_music:
        recognition_result = recognize(story)
        if recognition_result == 'Success':
            recognised_list.append(story)
        else:
            recognition_error_handler(recognition_result)
    if recognised_list:
        for story in recognised_list:
            gui.display_links(story)
    else:
        gui.display_no_links()


if __name__ == '__main__':
    main()
