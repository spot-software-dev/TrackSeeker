from loguru import logger
import os.path
import datetime
import io
import shutil

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

DOWNLOADED_STORIES_DIR = os.path.join(os.path.abspath(os.curdir), 'DownloadedStories')
os.makedirs(DOWNLOADED_STORIES_DIR, exist_ok=True)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/drive']

API_NAME = 'drive'
API_VERSION = 'v3'

MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
date_now = datetime.date.today()
logger.add(os.path.join(MAIN_DIR, 'logs', 'drive_logic', f"drive_logic_{date_now}.log"), rotation="1 day")


class DriveError(HttpError):
    """Raised when encountered an error while using Drive"""


class DriveDownloadError(DriveError):
    """Raised when encountered an error while downloading from Drive"""
    def __init__(self, e):
        self.message = f"Encountered an error while downloading from Drive: {e}"
        logger.error(self.message)

    def __str__(self):
        return self.message


class DriveMultipleFolders(DriveError):
    """Raised when found multiple folders for specified location-folder."""
    def __init__(self, folders, partial_name):
        self.message = f"Found multiple folders for the specified location-folder ({partial_name}): {folders}"
        logger.error(self.message)

    def __str__(self):
        return self.message


class DriveLocationNotFound(DriveError):
    """Raised when no folder was found for specified location-folder."""
    def __init__(self):
        self.message = "Didn't find any folders for the specified location-folder"
        logger.error(self.message)

    def __str__(self):
        return self.message


def clear_downloaded_stories_dir() -> None:
    """Removes all files in the downloaded stories dir."""
    for file in os.listdir(DOWNLOADED_STORIES_DIR):
        os.remove(os.path.join(DOWNLOADED_STORIES_DIR, file))


class Drive:
    def __init__(self):
        self.creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        token_path = os.path.join(MAIN_DIR, 'token.json')
        credentials_path = os.path.join(MAIN_DIR, 'credentials.json')
        if os.path.exists(token_path):
            self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(self.creds.to_json())

    def get_location_directory(self, similar_name: str) -> str:
        keyword = similar_name
        query = f"name contains '{keyword}' and mimeType = 'application/vnd.google-apps.folder'"

        service = build(API_NAME, API_VERSION, credentials=self.creds)
        results = service.files().list(q=query).execute()
        folders = results.get('files', [])

        if not folders:
            logger.info('No folders found.')
            raise DriveLocationNotFound()
        else:
            location_directory = []
            for folder in folders:
                location_directory.append(folder['id'])
                logger.debug(f'Found folder with the name: {folder["name"]} and the ID: {folder["id"]}')
            if len(location_directory) > 1:
                raise DriveMultipleFolders(folders, similar_name)
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
            service = build(API_NAME, API_VERSION, credentials=self.creds)

            page_token = None
            files = []
            while True:
                # Call the Drive v3 API
                results = service.files().list(q=query, fields="nextPageToken, files(id, name)",
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

        logger.info(f'Files in Drive for day {date}: {files}')
        return files

    def get_files(self, similar_name: str,
                  start_year: int, start_month: int, start_day: int,
                  end_year: int, end_month: int, end_day: int) -> list:
        """
        Get all drive files in consecutive range of dates.
        :return: list of files as dictionaries - [{id: ..., name: ...}, {id: ..., name: ...}, ... ]
        :exception: HttpError: Couldn't get files from Drive
        """
        start_date = datetime.datetime(year=start_year, month=start_month, day=start_day)
        end_date = datetime.datetime(year=end_year, month=end_month, day=end_day)
        current_date = start_date
        files = []

        folder_id = self.get_location_directory(similar_name)

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

    def _download(self, file_id: int, file_name: str) -> str:
        """
        Download the specified file to the Downloaded Stories folder and name it.
        :param file_id: Google Drive file ID.
        :param file_name: The name that the downloaded file will have.
        :return: Absolute path to the downloaded file
        :exception: DriveDownloadError: Couldn't download or save the Drive file
        """
        service = build(API_NAME, API_VERSION, credentials=self.creds)
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()

        downloader = MediaIoBaseDownload(fh, request, chunksize=204800)
        done = False

        try:
            while not done:
                status, done = downloader.next_chunk()
                logger.debug(f"Download status: {int(status.progress() * 100)}")

            fh.seek(0)

            cleaned_file_name = file_name.replace(':', '-')
            file_path = os.path.join(DOWNLOADED_STORIES_DIR, cleaned_file_name)
            with open(file_path, "wb") as f:
                shutil.copyfileobj(fh, f)

            logger.success(f"Downloaded {file_name} and saved it in {file_path}")
            return file_path

        except Exception as e:
            raise DriveDownloadError(e)

    def download_files(self, location: str, start_year: int, start_month: int, start_day: int,
                       end_year: int, end_month: int, end_day: int) -> list:
        """Download video files from Drive in the time specified."""
        drive_files = self.get_files(similar_name=location,
                                     start_year=start_year, start_month=start_month, start_day=start_day,
                                     end_year=end_year, end_month=end_month, end_day=end_day)
        downloaded_files = []
        for file in drive_files:
            downloaded_files.append({'id': file['id'], 'path': self._download(file['id'], file['name'])})

        return downloaded_files
