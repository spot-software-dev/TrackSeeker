from loguru import logger
import datetime
from drive_logic import Drive

if __name__ == "__main__":
    drive = Drive()
    while True:
        date_now = datetime.datetime.today().date()
        Drive.date_now = date_now
        logger.info(f'Synchronizing at {date_now}')
        try:
            from logic import master_sync
            master_sync(drive)
        except Exception as e:
            logger.error(f'Error occurred: {e}')
        else:
            logger.success(f'Completed sync with no errors at {date_now}')

