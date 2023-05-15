from .instagram_bot import IGBOT
from .gui import GUI
from .music_recognition import recognize


def main():
    gui = GUI()
    gui.run_gui()
    username = input("Enter Exact Username: ")
    instagram_bot = IGBOT()
    stories_music = instagram_bot.instagram_search(username)
    user_music_path = input("Enter File Path:\n")
    links = recognize(user_music_path, stories_music)
    if links:
        gui.display_links(links)
    else:
        gui.display_no_links()


if __name__ == '__main__':
    main()

