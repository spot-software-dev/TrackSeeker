from loguru import logger
from datetime import datetime

if __name__ == "__main__":
    drive = Drive()
    while True:
        logger.info(f'Synchronizing at {datetime.now()}')
        try:
            from logic import master_sync
            master_sync(drive)
        except Exception as e:
            logger.error(f'Error occurred: {e}')
        else:
            logger.success(f'Completed sync with no errors at {datetime.now()}')
