from loguru import logger
import traceback
import datetime
import time
from drive_logic import Drive
from instagram_bot import IGBOT

COOLDOWN_MINUTES = 120  # Not too much, not too little.


if __name__ == "__main__":
    drive = Drive()
    instagram_bot = IGBOT()
    date_now = datetime.datetime.today().date()
    drive.date_now = date_now
    instagram_bot.date_now = date_now
    while True:
        logger.info(f'Synchronizing at {date_now}')
        try:
            from logic import master_sync
            master_sync(drive, instagram_bot)
        except KeyError as e:
            logger.error(f"Got known KeyError problem. Read the warning and investigate JSON and username. Error: {e}")
        except Exception as e:
            logger.error(f'Error occurred: {e}. Traceback: {traceback.format_exc()}')
        else:
            logger.success(f'Completed sync with no errors at {date_now}')
            date_now = datetime.datetime.today().date()
            logger.debug(f"Updating date to {date_now}")
            drive.date_now = date_now
            instagram_bot.date_now = date_now

        logger.info('Clearing stories directory...')
        IGBOT.clean_stories_directory()
        time.sleep(60 * COOLDOWN_MINUTES)
