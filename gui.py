from loguru import logger


class GUI:
    @staticmethod
    def display_link(recognition: dict) -> None:
        logger.info(f"Found a match! {recognition['title']} by {recognition['artist']} played in {recognition['url']}")

    @staticmethod
    def display_no_links():
        logger.info('No recognitions found :)')
