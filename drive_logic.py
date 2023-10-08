from setup import google_key_generate
from loguru import logger
import os.path
import datetime
import io
import shutil

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

DOWNLOADED_STORIES_DIR = os.path.join(
    os.path.abspath(os.curdir), 'DownloadedStories')
os.makedirs(DOWNLOADED_STORIES_DIR, exist_ok=True)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/drive']

API_NAME = 'drive'
API_VERSION = 'v3'

MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
date_now = datetime.date.today()
logger.add(os.path.join(MAIN_DIR, 'logs', 'drive_logic',
           f"drive_logic_{date_now}.log"), rotation="1 day")


class DriveError(HttpError):
    """Raised when encountered an error while using Drive"""


class GoogleCloudAuthError(DriveError):
    """Raised when encountered an error authenticating google cloud"""

    def __init__(self, e):
        self.message = f"Encountered an error while authenticating google cloud: {e}"
        logger.error(self.message)

    def __str__(self):
        return self.message


class DriveDownloadError(DriveError):
    """Raised when encountered an error while downloading from Drive"""

    def __init__(self, e):
        self.message = f"Encountered an error while downloading from Drive: {e}"
        logger.error(self.message)

    def __str__(self):
        return self.message


class DriveMultipleFolders(DriveError):
    """Raised when found multiple folders while searching the specified folder."""

    def __init__(self, folders, partial_name):
        self.message = f"Found multiple folders while searching the specified folder ({partial_name}): {folders}"
        logger.error(self.message)

    def __str__(self):
        return self.message


class DriveLocationNotFound(DriveError):
    """Raised when no folder was found for specified location-folder."""

    def __init__(self, location):
        self.message = f"Didn't find any folders for the specified location-folder: {location}"
        logger.error(self.message)

    def __str__(self):
        return self.message


class DriveDashboardNotFound(DriveError):
    """Raised when no folder was found for specified user-dashboard-folder."""
    def __init__(self, username):
        self.message = f"Didn't find any folders for the specified user-dashboard-folder: {username}"
        logger.error(self.message)

    def __str__(self):
        return self.message


class DriveShareableLinkError(DriveError):
    """Raised when could not retrieve the Drive file's shareable link."""
    def __init__(self):
        self.message = "Error: Unable to retrieve the shareable link.."

    def __str__(self):
        return self.message


def clear_downloaded_stories_dir() -> None:
    """Removes all files in the downloaded stories dir."""
    for file in os.listdir(DOWNLOADED_STORIES_DIR):
        os.remove(os.path.join(DOWNLOADED_STORIES_DIR, file))


class Drive:
    """Google Drive interaction for getting Instagram Stories, their dates and locations."""

    def __init__(self, username: str = ""):

        SERVICE_ACCOUNT_FILE = os.path.join(
            MAIN_DIR, 'service-account-key.json')

        try:
            logger.info(
                'Trying to authenticated Google Cloud service...')
            
            if not os.path.exists(SERVICE_ACCOUNT_FILE):
                logger.warning('Google authenication key was not found')
                logger.info('Trying to generate a new key...')
                
                google_key_generate()
                
                logger.success('Generated a new authenication key file.')

            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)

            self.service = build(API_NAME, API_VERSION,
                                     credentials=credentials)

            logger.success('Google Cloud service account is authenticated.')

        except Exception as e:
            raise GoogleCloudAuthError(e)

        self.username = username

    def get_location_directory_id(self, location: str, location_folder_id: str) -> str:
        """Get Instagram Location's collected stories Google Drive folder ID."""
        query = f"name contains \"'{location}_'\" and '{location_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"

        results = self.service.files().list(q=query).execute()
        folders = results.get('files', [])

        if not folders:
            raise DriveLocationNotFound(location=location)
        else:
            location_directory = []
            for folder in folders:
                location_directory.append(folder['id'])
                logger.debug(
                    f'Found folder with the name: {folder["name"]} and the ID: {folder["id"]}')
            if len(location_directory) > 1:
                raise DriveMultipleFolders(folders, location)
            return location_directory[0]

    def get_files_at_date_in_folder(self,
                                    folder_id: str,
                                    year: int = date_now.year,
                                    month: int = date_now.month,
                                    day: int = date_now.day):
        """
        Get all drive files in consecutive range of dates.
        :return: list of files as dictionaries - [{id: ..., name: ...}, {id: ..., name: ...}, ... ]
        :exception: HttpError: Couldn't get files from Drive
        """

        date = datetime.date(year=year, month=month, day=day)
        query = f"'{folder_id}' in parents and mimeType contains 'video/' and fullText contains '{date}'"
        try:

            page_token = None
            files = []
            while True:
                # Call the Drive v3 API
                results = self.service.files().list(q=query, fields="nextPageToken, files(id, name)",
                                                    pageToken=page_token).execute()
                items = results.get('files', [])

                if not items:
                    logger.info('No files found.')
                    return []
                files.extend([{"id": item["id"], "name": item["name"]}
                             for item in items])
                page_token = results.get('nextPageToken', None)
                if page_token is None:
                    break

        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            raise HttpError(resp=error.resp,
                            content=error.content, uri=error.uri)

        logger.info(f'Files in Drive for day {date}: {files}')
        return files

    def get_all_files(self):
        """
        Get all drive files.
        :return: list of files as dictionaries - [{id: ..., name: ...}, {id: ..., name: ...}, ... ]
        :exception: HttpError: Couldn't get files from Drive
        """

        query = f"mimeType contains 'video/'"
        try:
            page_token = None
            files = []
            while True:
                # Call the Drive v3 API
                results = self.service.files().list(q=query, fields="nextPageToken, files(id, name)",
                                                    pageToken=page_token).execute()
                items = results.get('files', [])

                if not items:
                    logger.info('No files found.')
                    return []
                files.extend([{"id": item["id"], "name": item["name"]} for item in items])
                page_token = results.get('nextPageToken', None)
                if page_token is None:
                    break

        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            raise HttpError(resp=error.resp, content=error.content, uri=error.uri)

        logger.info(f'Finished getting all {len(files)} files from drive')
        return files

    def get_location_dashboard_folder_id(self) -> str:
        """Get Client's Google Drive location-dashboard folder"""

        query = f"fullText contains \"'{self.username}'\" and fullText contains \"'Dashboard_locations'\" and mimeType = 'application/vnd.google-apps.folder'"
        results = self.service.files().list(q=query).execute()
        folders = results.get('files', [])
        if not folders:
            raise DriveDashboardNotFound(username=self.username)
        else:
            location_directory = []
            for folder in folders:
                location_directory.append(folder['id'])
                logger.debug(
                    f'Found folder with the name: {folder["name"]} and the ID: {folder["id"]}')
            if len(location_directory) > 1:
                raise DriveMultipleFolders(folders, self.username)
            return location_directory[0]

    def get_files(self, location: str,
                  start_year: int, start_month: int, start_day: int,
                  end_year: int, end_month: int, end_day: int) -> list:
        """
        Get all drive files in consecutive range of dates.
        :return: list of files as dictionaries - [{id: ..., name: ...}, {id: ..., name: ...}, ... ]
        :exception: HttpError: Couldn't get files from Drive
        """
        location_folder_id = self.get_location_dashboard_folder_id()
        folder_id = self.get_location_directory_id(location, location_folder_id)

        if not end_year or not end_month or not end_day:
            return self.get_files_at_date_in_folder(folder_id=folder_id,
                                                    year=start_year,
                                                    month=start_month,
                                                    day=start_day)
        start_date = datetime.datetime(
            year=start_year, month=start_month, day=start_day)
        end_date = datetime.datetime(
            year=end_year, month=end_month, day=end_day)
        current_date = start_date
        files = []

        while current_date <= end_date:
            files.extend(self.get_files_at_date_in_folder(folder_id=folder_id,
                                                          year=current_date.year,
                                                          month=current_date.month,
                                                          day=current_date.day))
            current_date += datetime.timedelta(days=1)

        return files

    @staticmethod
    def get_file_link(file_id: str) -> str:
        return f"https://drive.google.com/uc?id={file_id}"

    @staticmethod
    def get_file_sharable_link(file_id):
        return f'https://drive.google.com/file/d/{file_id}/view?usp=sharing'

    @staticmethod
    def get_id_from_sharable_link(link: str) -> str:
        return link.replace('https://drive.google.com/file/d/', '').replace('/view?usp=sharing', '')

    def _download(self, file_id: int, file_name: str) -> str:
        """
        Download the specified file to the Downloaded Stories folder and name it.
        :param file_id: Google Drive file ID.
        :param file_name: The name that the downloaded file will have.
        :return: Absolute path to the downloaded file
        :exception: DriveDownloadError: Couldn't download or save the Drive file
        """
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()

        downloader = MediaIoBaseDownload(fh, request, chunksize=204800)
        done = False

        try:
            while not done:
                status, done = downloader.next_chunk()
                logger.debug(
                    f"Download status: {int(status.progress() * 100)}")

            fh.seek(0)

            cleaned_file_name = file_name.replace(':', '-')
            file_path = os.path.join(DOWNLOADED_STORIES_DIR, cleaned_file_name)
            with open(file_path, "wb") as f:
                shutil.copyfileobj(fh, f)

            logger.success(
                f"Downloaded {file_name} and saved it in {file_path}")
            return file_path

        except Exception as e:
            raise DriveDownloadError(e)

    def download_files(self, location: str, start_year: int, start_month: int, start_day: int,
                       end_year: int, end_month: int, end_day: int) -> list:
        """Download video files from Drive in the time specified."""
        drive_files = self.get_files(location=location,
                                     start_year=start_year, start_month=start_month, start_day=start_day,
                                     end_year=end_year, end_month=end_month, end_day=end_day)
        downloaded_files = []
        for file in drive_files:
            downloaded_files.append(
                {'id': file['id'], 'path': self._download(file['id'], file['name'])})

        return downloaded_files

    def get_download_link(self, file_id: str):
        """Get the url link to download the file from drive"""
        logger.debug('Getting download link...')
        file_metadata = self.service.files().get(
            fileId=file_id, fields='webContentLink').execute()
        download_link = file_metadata.get('webContentLink')
        logger.success(f"Successfully got download link")
        return download_link

    def _get_files_in_folder(self, folder_id: str):
        """Get all files in folder"""

        results = []
        page_token = None

        while True:
            response = self.service.files().list(q=f"'{folder_id}' in parents",
                                                 spaces='drive',
                                                 fields='nextPageToken, files(id, name)',
                                                 pageToken=page_token).execute()

            files = response.get('files', [])
            results.extend(files)

            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        return results

    def get_location_dates(self, location: str, location_folder_id: str) -> list:
        """Get user's dates of collected location-stories"""
        folder_id = self.get_location_directory_id(location=location, location_folder_id=location_folder_id)
        drive_files = self._get_files_in_folder(folder_id)
        location_dates = set()
        for file in drive_files:
            file_date = file['name'].split('T')[0]
            location_dates.add(file_date)

        return sorted(list(location_dates))

    def _get_locations(self, location_folder_id: str) -> list:
        """
        Get from user's Google Drive folder all locations that were followed and acquired Instagram Stories.
        """
        query = f"'{location_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
        try:

            page_token = None
            location_folders = []
            while True:
                results = self.service.files().list(q=query, fields="nextPageToken, files(id, name)",
                                                    pageToken=page_token).execute()
                items = results.get('files', [])

                if not items:
                    logger.info('No files found.')
                    return []
                location_folders.extend([item["name"] for item in items])
                page_token = results.get('nextPageToken', None)
                if page_token is None:
                    break

        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            raise HttpError(resp=error.resp,
                            content=error.content, uri=error.uri)

        logger.info(f'Locations in Drive: {location_folders}')
        return location_folders

    def get_locations_and_dates(self) -> list:
        """
        Get from Google Drive all Story-Story user's dashboard locations that were followed
        and acquired Instagram Stories and all dates that someone posted a story tagging that location.
        """
        location_folder_id = self.get_location_dashboard_folder_id()
        locations_folders = self._get_locations(location_folder_id)
        locations_and_dates = []
        for location_folder in locations_folders:
            location_name = location_folder.split('_')[0]
            location_dates = self.get_location_dates(location_folder, location_folder_id)
            locations_and_dates.append(
                {'name': location_name, 'location_dates': location_dates})

        return locations_and_dates
