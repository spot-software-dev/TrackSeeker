from loguru import logger
import datetime
import time
from drive_logic import Drive
from instagram_bot import IGBOT

COOLDOWN_MINUTES = 30  # Not too much, not too little.


if __name__ == "__main__":
    drive = Drive()
    instagram_bot = IGBOT()
    while True:
        date_now = datetime.datetime.today().date()
        drive.date_now = date_now
        instagram_bot.date_now = date_now
        logger.info(f'Synchronizing at {date_now}')
        try:
            from logic import master_sync
            master_sync(drive, instagram_bot)
        except Exception as e:
            logger.error(f'Error occurred: {e}')
        else:
            logger.success(f'Completed sync with no errors at {date_now}')

        time.sleep(60 * COOLDOWN_MINUTES)

        logger.info('Clearing stories directory...')
        IGBOT.clean_stories_directory()
