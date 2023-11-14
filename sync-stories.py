from loguru import logger
import traceback
import datetime
import time
from drive_logic import Drive
from instagram_bot import IGBOT

COOLDOWN_MINUTES = 30  # Not too much, not too little.


def update_date(igbot: IGBOT, drive_obj: Drive):
    """Update the date_now variable with the current date."""
    current_date = datetime.datetime.today().date()
    logger.debug(f"Updating date to {current_date}")
    drive_obj.date_now = current_date
    igbot.date_now = current_date
    return current_date


if __name__ == "__main__":
    drive = Drive()
    instagram_bot = IGBOT()
    date_now = update_date(instagram_bot, drive)
    while True:
        logger.info(f'Synchronizing at {date_now}')
        try:
            from logic import master_sync
            master_sync(drive, instagram_bot)
        except Exception as e:
            logger.error(f'Error occurred: {e}. Traceback: {traceback.format_exc()}')
        else:
            logger.success(f'Completed sync with no errors at {date_now}')
            time.sleep(60 * COOLDOWN_MINUTES)
            date_now = update_date(instagram_bot, drive)

        logger.info('Clearing stories directory...')
        IGBOT.clean_stories_directory()
