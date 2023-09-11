from loguru import logger
import os.path
import datetime
import io
import shutil
from moviepy.editor import VideoFileClip

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
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


class DriveShareableLinkError(DriveError):
    """Raised when could not make file's Drive link shareable."""
    def __init__(self):
        self.message = "Error: Unable to make the link shareable."

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
                try:
                    self.creds.refresh(Request())
                except RefreshError as _:
                    logger.info('Token expired. Removing and logging in to Google to create a new token...')
                    os.remove(os.path.join(MAIN_DIR, 'token.json'))
                    self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(self.creds.to_json())

    def get_location_directory(self, location: str) -> str:
        query = f"fullText contains \"'{location}_'\" and mimeType = 'application/vnd.google-apps.folder'"

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

    def get_files(self, location: str,
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

        folder_id = self.get_location_directory(location)

        while current_date <= end_date:
            files.extend(self.get_files_at_date_in_folder(folder_id=folder_id,
                                                          year=current_date.year,
                                                          month=current_date.month,
                                                          day=current_date.day))
            current_date += datetime.timedelta(days=1)

        return files

    def _make_link_shareable(self, file_id: str) -> None:
        """
        Make link shareable.
        :exception: DriveShareableLinkError: Unable to make the Drive file link shareable
        """
        # Create a permission for "Anyone with the link" with view access
        permission = {
            'type': 'anyone',
            'role': 'reader',
        }
        # Update the file's permissions
        service = build(API_NAME, API_VERSION, credentials=self.creds)
        service.permissions().create(fileId=file_id, body=permission).execute()
        logger.info(f"The file at 'https://drive.google.com/uc?id={file_id}' is now shareable by anyone with the link.")

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

    @staticmethod
    def _download_audio(file_url: str, file_name: str) -> str or None:
        """
        Download the specified file as audio to the Downloaded Stories folder and name it.
        :param file_url: Google Drive file url.
        :param file_name: The name that the downloaded file will have.
        :return: Absolute path to the downloaded file
        """
        try:
            # Create a VideoFileClip object
            video_clip = VideoFileClip(file_url)
        except OSError as e:
            if "MoviePy error: failed to read the first frame of video file" in str(e):
                logger.debug("File might be corrupted, skipping file.")
                return
            elif "Server returned 403 Forbidden (access denied)" in str(e):
                logger.debug("Cannot access file right now, skipping file...")
                return
            else:
                raise e

        # Extract audio from the video
        audio_clip = video_clip.audio
        if not audio_clip:
            return

        cleaned_file_name = file_name.replace(':', '-')
        cleaned_file_name_mp3 = f"{os.path.splitext(cleaned_file_name)[0]}.mp3"
        output_audio_file_name = os.path.join(DOWNLOADED_STORIES_DIR, cleaned_file_name_mp3)

        # Save the audio to a file
        audio_clip.write_audiofile(output_audio_file_name)

        # Close the clips
        audio_clip.close()
        video_clip.close()

        return output_audio_file_name

    def download_files(self, location: str, start_year: int, start_month: int, start_day: int,
                       end_year: int, end_month: int, end_day: int) -> list:
        """Download video files from Drive in the time specified."""
        drive_files = self.get_files(location=location,
                                     start_year=start_year, start_month=start_month, start_day=start_day,
                                     end_year=end_year, end_month=end_month, end_day=end_day)
        downloaded_files = []
        for file in drive_files:
            file_url = self.get_file_link(file['id'])
            self._make_link_shareable(file['id'])
            downloaded_file_path = self._download_audio(file_url, file['name'])
            if downloaded_file_path:
                downloaded_files.append({'id': file['id'], 'path': downloaded_file_path})

        return downloaded_files

    def get_download_link(self, file_id: str):
        """Get the url link to download the file from drive"""
        logger.debug('Getting download link...')
        service = build(API_NAME, API_VERSION, credentials=self.creds)
        file_metadata = service.files().get(fileId=file_id, fields='webContentLink').execute()
        download_link = file_metadata.get('webContentLink')
        logger.success(f"Successfully got download link")
        return download_link

    def _get_files_in_folder(self, folder_id: str):
        """Get all files in folder"""
        service = build(API_NAME, API_VERSION, credentials=self.creds)

        results = []
        page_token = None

        while True:
            response = service.files().list(q=f"'{folder_id}' in parents",
                                            spaces='drive',
                                            fields='nextPageToken, files(id, name)',
                                            pageToken=page_token).execute()

            files = response.get('files', [])
            results.extend(files)

            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        return results

    def get_location_dates(self, location: str) -> list:
        """Get location present stories dates"""
        folder_id = self.get_location_directory(location=location)
        drive_files = self._get_files_in_folder(folder_id)
        location_dates = set()
        for file in drive_files:
            file_date = file['name'].split('T')[0]
            location_dates.add(file_date)

        return sorted(list(location_dates))
