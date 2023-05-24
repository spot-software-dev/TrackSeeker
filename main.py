from .instagram_bot import IGBOT
from .gui import GUI
from .music_recognition import recognize


def main():
    gui = GUI()
    gui.run_gui()
    username = input("Enter Exact Username: ")
    instagram_bot = IGBOT()
    stories_music = instagram_bot.instagram_search(username)
    recognised_list = []
    for story in stories_music:
        if recognize(story):
            recognised_list.append(story)
    if recognised_list:
        for story in recognised_list:
            gui.display_links(story)
    else:
        gui.display_no_links()


if __name__ == '__main__':
    main()
