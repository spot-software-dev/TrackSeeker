import os
import time

from loguru import logger
from drive_logic import Drive
from os import path
import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from dotenv.main import load_dotenv

load_dotenv()
MAIN_DIR = path.dirname(path.abspath(__file__))
date_now = datetime.date.today()
logger.add(path.join(MAIN_DIR, 'logs', 'story_story_logic', f"story_story_logic_{date_now}.log"), rotation="1 day")


class StoryStoryError(ValueError):
    """Raised when an error relating to story-story.co website interaction occurs."""


class StoryStoryLoginError(StoryStoryError):
    """Raised when failed to log in to story-story.co due to bad user credentials."""
    def __init__(self):
        self.message = f"Entered wrong login E-mail or Password"
        logger.error(self.message)

    def __str__(self):
        return self.message


class StoryStoryButtonError(StoryStoryError):
    """Raised when the story-story Button entered is not found."""
    def __init__(self, e):
        self.message = f"Couldn't find the button specified. Error: {e}"
        logger.error(self.message)

    def __str__(self):
        return self.message


class StoryStoryDashboardError(StoryStoryError):
    """Raised when the story-story Dashboard name entered is not found."""
    def __init__(self, dashboard_name):
        self.message = f"No Dashboard named {dashboard_name}"
        logger.error(self.message)

    def __str__(self):
        return self.message


class StoryStoryCanNotFindLocation(StoryStoryError):
    """Raised when the Instagram location entered can not be found in story-story"""
    def __init__(self, location):
        self.message = f"Story-Story cannot find Instagram Location - {location}"
        logger.error(self.message)

    def __str__(self):
        return self.message


class StoryStorySession:
    """Class to enter Instagram location to get its stories."""

    def __init__(self, email: str = os.environ['EMAIL'], password: str = os.environ['PASSWORD']):
        """Login to the user. """
        driver_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        website_url = "https://app.story-story.co"

        # Create a webdriver instance
        self.driver = webdriver.Chrome()

        # Open the website
        self.driver.get(website_url)

        # Locate the login fields and enter credentials
        email_field = self.driver.find_element(By.NAME, "email")
        password_field = self.driver.find_element(By.NAME, "password")

        email_field.send_keys(email)
        password_field.send_keys(password)

        # Submit the login form
        password_field.send_keys(Keys.RETURN)

        logger.info(f"Entered E-mail: {email}")

        try:
            assert "You entered the wrong email or password." not in self.driver.page_source
            logger.success(f"Successfully Entered")
        except AssertionError as _:
            StoryStoryLoginError()

    def _click_button(self, button_text: str):
        """Clicks a web button."""
        # Locate and click the link to the desired button
        try:
            button_link = self.driver.find_element(By.PARTIAL_LINK_TEXT, button_text)
        except NoSuchElementException as error:
            logger.error(f"No Button named {button_text}.")
            raise StoryStoryButtonError(error)

        button_link.click()

    def _enter_dashboard(self, name: str):
        dashboard_name = name.title()
        # Locate and click the link to the desired dashboard
        try:
            self._click_button(dashboard_name)
        except StoryStoryButtonError as _:
            raise StoryStoryDashboardError(dashboard_name)

    def _enter_dashboard_settings(self):
        self._click_button("go to settings")

    def _get_locations_number(self):
        locations_fields_list = self.driver.find_elements(By.CLASS_NAME, "following-list-item.following-location-item")
        return len(locations_fields_list)

    def _enter_new_location(self, location: int):
        """Add an Instagram location to the story-story Dashboard"""
        logger.info(f"Entered location {location}")

        location_input_field = self.driver.find_element(By.CSS_SELECTOR, '[placeholder="Add a location ID"]')
        location_input_field.send_keys(location)
        location_input_field.send_keys(Keys.RETURN)
        time.sleep(1)
        if "We were not able to add this location" in self.driver.page_source:
            raise StoryStoryCanNotFindLocation(location)

        logger.success(f"Successfully added location {location}")

    def __del__(self):
        self.driver.close()

    def add_location(self, dashboard_name: str, location):
        """Add Instagram location to entered story-story Dashboard"""
        logger.info(f"Entered location {location} to be added in {dashboard_name} dashboard")
        self._enter_dashboard(dashboard_name)
        time.sleep(0.5)
        self._enter_dashboard_settings()
        time.sleep(0.1)
        self._enter_new_location(location)
        del self
        logger.success(f"Successfully added location {location}")

    def get_instagram_followed_locations_and_dates(self, dashboard_name: str) -> list[dict]:
        """Get all tracked Instagram locations and dates that stories are present"""
        logger.debug(f"Getting locations from dashboard {dashboard_name}")
        self._enter_dashboard(dashboard_name)
        time.sleep(0.5)
        self._enter_dashboard_settings()
        time.sleep(0.5)
        locations_names = []
        for location_element in self.driver.find_elements(By.CLASS_NAME, "following-location-item__name"):
            name = location_element.find_elements(By.TAG_NAME, 'span')[0].text
            locations_names.append(name)

        drive = Drive()
        locations = []
        for name in locations_names:
            location_dates = drive.get_location_dates(f"{name}_")
            locations.append({'name': name, 'location_dates': location_dates})

        del self
        logger.info(f"Instagram locations in dashboard: {', '.join(locations_names)}")
        return locations
