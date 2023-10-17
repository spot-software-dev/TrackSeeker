from setup import google_key_generate
from loguru import logger
import os.path
import datetime
import io
import shutil

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from ssl import SSLWantWriteError

from instagram_bot import STORIES_DIR_PATH

DOWNLOADED_STORIES_DIR = os.path.join(
    os.path.abspath(os.curdir), 'DownloadedStories')
os.makedirs(DOWNLOADED_STORIES_DIR, exist_ok=True)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/drive']

API_NAME = 'drive'
API_VERSION = 'v3'

MAIN_DIR = os.path.dirname(os.path.abspath(__file__))


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


class DriveUploadError(DriveError):
    """Raised when encountered an error while uploading to Drive"""

    def __init__(self, e):
        self.message = f"Encountered an error while uploading to Drive: {e}"
        logger.error(self.message)

    def __str__(self):
        return self.message


class DriveCreateDirError(DriveError):
    """Raised when encountered an error while creating a Drive directory"""

    def __init__(self, e):
        self.message = f"Encountered an error while creating a Drive directory: {e}"
        logger.error(self.message)

    def __str__(self):
        return self.message


class DriveMultipleDirs(DriveError):
    """Raised when found multiple folders while searching the specified folder."""

    def __init__(self, dirs, partial_name):
        self.message = f"Found multiple folders while searching the specified folder ({partial_name}): {dirs}"
        logger.error(self.message)

    def __str__(self):
        return self.message


class DriveFolderNotFound(DriveError):
    """Raised when no folder was found for specified folder."""

    def __init__(self, dir_name):
        self.message = f"Didn't find any folders for the specified folder: {dir_name}"
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


class DriveMainStoriesDirError(DriveError):
    """Raised when no folder was found for specified main-stories-folder."""

    def __init__(self, username):
        self.message = f"Didn't find main-stories-folder for user: {username}"

    def __str__(self):
        return self.message


def clear_downloaded_stories_dir() -> None:
    """Removes all files in the downloaded stories dir."""
    for file in os.listdir(DOWNLOADED_STORIES_DIR):
        os.remove(os.path.join(DOWNLOADED_STORIES_DIR, file))


class Drive:
    """Google Drive interaction for getting Instagram Stories, their dates and locations."""

    date_now = datetime.datetime.today().date()
    logger.add(os.path.join(MAIN_DIR, 'logs', 'drive_logic', f"drive_logic_{date_now}.log"), rotation="1 day")

    def __init__(self):
        """Authenticate Google Drive interaction with the necessary approval scopes."""

        SERVICE_ACCOUNT_FILE = os.path.join(
            MAIN_DIR, 'service-account-key.json')

        try:
            logger.info(
                'Trying to authenticated Google Cloud service...')

            if not os.path.exists(SERVICE_ACCOUNT_FILE):
                logger.warning('Google authentication key was not found')
                logger.info('Trying to generate a new key...')

                google_key_generate()

                logger.success('Generated a new authentication key file.')

            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)

            self.service = build(API_NAME, API_VERSION,
                                 credentials=credentials)

            logger.success('Google Cloud service account is authenticated.')

        except Exception as e:
            raise GoogleCloudAuthError(e)

        self.STORY_STORY_LOCATIONS_DIR_ID = self.get_story_story_locations_dir_id()
        self.SPOT_LOCATIONS_DIR_ID = self.get_spot_locations_dir_id()

    @staticmethod
    def build_get_dir_query(**kwargs):
        """
        Construct a Google Drive query for directory id.

        Available key-word arguments: dir_name, parent_dir_id
        """

        query = f"mimeType = 'application/vnd.google-apps.folder'"

        dir_name = kwargs.get('dir_name')
        parent_dir_id = kwargs.get('parent_dir_id')

        if dir_name:
            query += f" and name contains '\"{dir_name}\"'"
        if parent_dir_id:
            query += f" and '{parent_dir_id}' in parents"

        return query

    @staticmethod
    def build_get_videos_from_dir_query(**kwargs):
        """
        Construct a Google Drive query for videos.

        Available key-word arguments: dir_id, date, date_end, location
        """
        query = f"mimeType contains 'video/'"

        dir_id = kwargs.get('dir_id')
        date = kwargs.get('date')
        date_end = kwargs.get('date_end')
        location = kwargs.get('location')

        if dir_id:
            query += f" and '{dir_id}' in parents"
        if date and date_end:
            query += f" and createdTime >= '{date}T00:00:00' and createdTime <= '{date_end}T23:59:59'"
        if date and not date_end:
            query += f" and createdTime >= '{date}T00:00:00' and createdTime <= '{date}T23:59:59'"
        if location:
            query += f" and fullText contains '\"{location}\"'"

        return query

    def get_dir_id(self, query: str, dir_name: str):

        results = self.service.files().list(q=query).execute()
        files = results.get('files', [])

        if not files:
            raise DriveFolderNotFound(dir_name=dir_name)
        else:
            drive_dir = []
            for dir in files:
                drive_dir.append(dir['id'])
                logger.debug(f'Found directory with the name: {dir["name"]} and the ID: {dir["id"]}')
            if len(drive_dir) > 1:
                raise DriveMultipleDirs(dirs=files, partial_name=dir_name)
            return drive_dir[0]

    def get_files_from_dir(self, query: str):

        try:
            page_token = None
            files = []
            while True:
                results = self.service.files().list(q=query, fields="nextPageToken, files(id, name, createdTime)",
                                                    pageToken=page_token).execute()
                items = results.get('files', [])

                if not items:
                    logger.info('No files found.')
                    return []

                files.extend([{"id": item["id"], "name": item["name"], 'created_time': item["createdTime"]} for item in items])
                page_token = results.get('nextPageToken', None)
                logger.info(f'Found {len(files)} files.')

                if page_token is None:
                    break

        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            raise HttpError(resp=error.resp,
                            content=error.content, uri=error.uri)

        return files

    def get_all_spot_videos(self):
        """
        Get all spot locations stories Drive videos.
        :return: list of videos as dictionaries - [{id: ..., name: ...}, {id: ..., name: ...}, ... ]
        :exception: HttpError: Couldn't get files from Drive
        """
        spot_locations = self.get_dirs_in_parent_dir(self.SPOT_LOCATIONS_DIR_ID)
        all_videos = []
        for location in spot_locations:
            location_stories = self.get_all_videos_from_dir(location['id'])
            all_videos += location_stories
        return all_videos

    def get_all_videos_from_dir(self, dir_id: str):
        """Get all videos in directory"""

        query = self.build_get_videos_from_dir_query(dir_id=dir_id)
        videos = self.get_files_from_dir(query=query)

        return videos

    def get_story_story_locations_dir_id(self):
        """Get story story locations Google Drive directory ID."""

        dir_name = "STORY_STORY_LOCATIONS"
        locations_dir_query = self.build_get_dir_query(dir_name=dir_name)
        locations_dir_id = self.get_dir_id(query=locations_dir_query, dir_name=dir_name)

        return locations_dir_id

    def get_spot_locations_dir_id(self):
        """Get Spot ( our ) locations Google Drive directory ID."""

        dir_name = "Spot Stories"
        locations_dir_query = self.build_get_dir_query(dir_name=dir_name)
        locations_dir_id = self.get_dir_id(query=locations_dir_query, dir_name=dir_name)

        return locations_dir_id

    def get_dir_id_with_parent(self, parent_dir_id: str, dir_name: str):
        """Get Google Drive directory ID with parent folder"""

        dir_query = self.build_get_dir_query(parent_dir_id=parent_dir_id, dir_name=dir_name)
        dir_id = self.get_dir_id(query=dir_query, dir_name=dir_name)

        return dir_id

    def get_videos_at_date_from_dir(self, dir_id: str,
                                    year: int = date_now.year,
                                    month: int = date_now.month,
                                    day: int = date_now.day):
        """
        Get all drive files at a specific date. Default is today's date 
        :return: list of files as dictionaries - [{id: ..., name: ...}, {id: ..., name: ...}, ... ]
        :exception: HttpError: Couldn't get files from Drive
        """

        date = datetime.date(year=year, month=month, day=day)
        query = self.build_get_videos_from_dir_query(dir_id=dir_id, date=date)
        videos = self.get_files_from_dir(query=query)

        return videos

    def get_videos_at_date_range_from_dir(self, dir_name: str, parent_dir_id: str,
                                          start_year: int, start_month: int, start_day: int,
                                          end_year: int, end_month: int, end_day: int) -> list:
        """
        Get all drive files in consecutive range of dates.
        :return: list of files as dictionaries - [{id: ..., name: ...}, {id: ..., name: ...}, ... ]
        :exception: HttpError: Couldn't get files from Drive
        """

        start_date = datetime.date(year=start_year, month=start_month, day=start_day)
        end_date = datetime.date(year=end_year, month=end_month, day=end_day)

        dir_id = self.get_dir_id_with_parent(parent_dir_id=parent_dir_id, dir_name=dir_name)
        query = self.build_get_videos_from_dir_query(dir_id=dir_id, date=start_date, end_date=end_date)
        videos = self.get_files_from_dir(query=query)

        return videos

    def get_dir_videos_dates(self, dir_name: str, parent_dir_id: str) -> list:
        """Get from Google Drive directory all the videos dates from name convention"""
        dir_id = self.get_dir_id_with_parent(dir_name=dir_name, parent_dir_id=parent_dir_id)
        query = self.build_get_videos_from_dir_query(dir_id=dir_id)
        videos = self.get_files_from_dir(query=query)

        location_dates = set()
        for file in videos:
            file_date = file['created_time'].split('T')[0]
            location_dates.add(file_date)

        return sorted(list(location_dates))

    def get_dirs_in_parent_dir(self, parent_dir_id: str) -> list[dict[str, str]]:
        """
        Get from Google Drive parent directory all child directories.
        """
        query = self.build_get_dir_query(parent_dir_id=parent_dir_id)
        dirs = self.get_files_from_dir(query=query)

        return dirs

    def get_locations_and_dates(self, locations_dir_id: str) -> list:
        """
        Get from Google Drive locations parent dir all available locations and dates.
        """
        location_dirs = self.get_dirs_in_parent_dir(parent_dir_id=locations_dir_id)
        locations_and_dates = []

        for location_dir in location_dirs:
            location_dir_name_with_id = location_dir['name']
            location_dir_name = location_dir_name_with_id.split('_')[0]

            location_dates = self.get_dir_videos_dates(dir_name=location_dir_name, parent_dir_id=locations_dir_id)
            locations_and_dates.append({'location': location_dir_name, 'dates': location_dates})

        return locations_and_dates

    def get_today_locations_stories_usernames(self, locations_dir_id: str):
        """
        Get the locations and iterate over its videos to get the usernames of the stories that were uploaded today.
        returns [{"location": "pacha", "usernames": ["...", "...", "..."]}, {"location": ...}]
        """

        location_dirs = self.get_dirs_in_parent_dir(parent_dir_id=locations_dir_id)
        usernames_to_download = []

        for location in location_dirs:
            location_dir_name_with_id = location['name']
            location_dir_name = location_dir_name_with_id.split("_")[0]
            location_dir_id = self.get_dir_id_with_parent(parent_dir_id=locations_dir_id, dir_name=location_dir_name)
            location_videos = self.get_videos_at_date_from_dir(dir_id=location_dir_id)

            usernames_to_download.append({"location": location_dir_name, "usernames": []})

            for video in location_videos:
                video_username_by_name = os.path.splitext(video['name'].split('-')[-1])[0]
                usernames_to_download[-1]['usernames'].append(video_username_by_name)

        return usernames_to_download

    def get_spot_locations_dirs(self):
        """Gets all the location directories inside Spot Stories"""

        location_dirs = self.get_dirs_in_parent_dir(parent_dir_id=self.SPOT_LOCATIONS_DIR_ID)
        return location_dirs

    def get_today_spot_stories_dir_videos(self):
        """Get from user's Google Drive main stories folder all today's stories"""

        videos = self.get_videos_at_date_from_dir(dir_id=self.SPOT_LOCATIONS_DIR_ID)
        return videos

    def _upload_story_for_sync_in_chunks(self, dir_id: str, story_metadata: dict, username: str, location: str):

        story_id = story_metadata['id']
        story_file_name = f"{location}-{self.date_now}-{story_id}-{username}.mp4"

        file_path = os.path.join(STORIES_DIR_PATH, story_file_name)

        # Create a resumable upload session
        media = MediaFileUpload(file_path, mimetype='video/mp4', chunksize=1024 * 1024, resumable=True)

        file_metadata = {
            'name': story_file_name,
            'parents': [dir_id]
        }

        logger.info(f'Trying to upload {story_file_name} to Drive directory {dir_id}...')

        try:
            request = self.service.files().create(
                body=file_metadata, media_body=media, fields='id')

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.debug(f'Uploaded {int(status.progress() * 100)}%')

        except HttpError as e:
            raise DriveUploadError(f'Error uploading {story_file_name}: {str(e)}')
        else:
            uploaded_file_id = response.get('id')
            if uploaded_file_id:
                logger.success(f'Successfully uploaded {story_file_name} to Drive with ID: {uploaded_file_id}')

    def upload_story_for_sync(self, dir_id: str, story_metadata: dict, username: str, location: str):

        story_id = story_metadata['id']
        story_file_name = f"{location}-{self.date_now}-{story_id}-{username}.mp4"

        file_path = os.path.join(STORIES_DIR_PATH, story_file_name)

        media = MediaFileUpload(file_path, mimetype='video/mp4')

        file_metadata = {
            'name': story_file_name,
            'parents': [dir_id]
        }

        logger.info(f'Trying to upload {story_file_name} to Drive directory {dir_id}...')

        try:
            response = self.service.files().create(
                body=file_metadata, media_body=media, fields='id').execute()

        except HttpError as e:
            raise DriveUploadError(f'Error uploading {story_file_name}: {str(e)}')
        except SSLWantWriteError as e:
            logger.warning(f'Received SSLWantWriteError: {e}')
            self._upload_story_for_sync_in_chunks(dir_id, story_metadata, username, location)
            return
        except TimeoutError as e:
            logger.warning(f'Received SSL error Timeout: {e}')
            self._upload_story_for_sync_in_chunks(dir_id, story_metadata, username, location)
            return

        else:
            uploaded_file_id = response.get('id')
            if uploaded_file_id:
                logger.success(f'Successfully uploaded {story_file_name} to Drive with ID: {uploaded_file_id}')

    def create_drive_dir(self, dir_name, parent_dir_id):
        """Creating a directory in google drive by parent_dir_id"""

        dir_metadata = {
            'name': dir_name,
            'parents': [parent_dir_id],
            'mimeType': 'application/vnd.google-apps.folder'
        }

        logger.info(f'Trying to create directory {dir_name} to parent directory id {parent_dir_id}...')

        try:
            drive_dir = self.service.files().create(body=dir_metadata, fields='id').execute()
        except HttpError as e:
            raise DriveCreateDirError(e)

        new_dir_id = drive_dir.get('id')
        if new_dir_id:
            logger.success(f'Successfully created directory {dir_name} to parent directory id {parent_dir_id}...')

    @staticmethod
    def get_video_link(file_id: str) -> str:
        return f"https://drive.google.com/uc?id={file_id}"

    @staticmethod
    def get_video_sharable_link(file_id):
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

    def download_files(self, dir_name: str, parent_dir_id: str, start_year: int, start_month: int, start_day: int,
                       end_year: int, end_month: int, end_day: int) -> list:
        """Download video files from Drive dir in the time specified."""

        drive_videos = self.get_videos_at_date_range_from_dir(dir_name=dir_name, parent_dir_id=parent_dir_id,
                                                              start_year=start_year, start_month=start_month, start_day=start_day,
                                                              end_year=end_year, end_month=end_month, end_day=end_day)
        downloaded_files = []
        for file in drive_videos:
            downloaded_files.append(
                {'id': file['id'], 'path': self._download(file['id'], file['name'])})

        return downloaded_files

    def get_download_link(self, file_id: str):
        """Get the url link to download the file from drive"""
        logger.debug('Getting download link...')
        file_metadata = self.service.files().get(fileId=file_id, fields='webContentLink').execute()
        download_link = file_metadata.get('webContentLink')
        logger.success(f"Successfully got download link")
        return download_link
