"""This module contains the GoogleDriveAPI class which is used to interact with the Google Drive API."""

import io
import logging
import traceback
from typing import List, Optional, Union

import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

NAME = "drive"
VERSION = "v3"


class GoogleDriveAPI:
    """Class for interacting with the Google Drive API."""

    logger = logging.getLogger(__name__)

    @staticmethod
    def create_folder(creds: dict, folder_name: str) -> Union[str, dict]:
        """Creates a folder in Google Drive."""
        try:
            # build service
            credentials = service_account.Credentials.from_service_account_info(
                creds["credentials"], scopes=creds["scopes"]
            )
            service = build(NAME, VERSION, credentials=credentials)

            # action
            folder_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [creds["folder_id"]] if creds.get("folder_id") else None,
            }

            folder = service.files().create(body=folder_metadata, fields="id").execute()
            return folder.get("id")
        except Exception as e:
            GoogleDriveAPI.logger.error(
                f"unable to create folder: {traceback.format_exc()}"
            )
            return {"error": str(e)}

    @staticmethod
    def upload_file(
        creds: dict, file_path: str, file_name: str, folder_id: Optional[str] = None
    ) -> Union[str, dict]:
        """Uploads a file to Google Drive."""
        try:
            # build service
            credentials = service_account.Credentials.from_service_account_info(
                creds["credentials"], scopes=creds["scopes"]
            )
            service = build(NAME, VERSION, credentials=credentials)

            # action
            media = MediaFileUpload(file_path)
            file_metadata = {
                "name": file_name,
                "parents": (
                    [folder_id]
                    if folder_id
                    else [creds["folder_id"]] if creds.get("folder_id") else []
                ),
            }

            file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            return file.get("id")
        except Exception as e:
            GoogleDriveAPI.logger.error(
                f"unable to upload file: {traceback.format_exc()}"
            )
            return {"error": str(e)}

    @staticmethod
    def upload_file_via_url(
        creds: dict, url: str, file_name: str, folder_id: Optional[str] = None
    ) -> Union[str, dict]:
        """Uploads a file to Google Drive via a URL."""
        try:
            # build service
            credentials = service_account.Credentials.from_service_account_info(
                creds["credentials"], scopes=creds["scopes"]
            )
            service = build(NAME, VERSION, credentials=credentials)

            # upload_file
            response = requests.get(url)
            media_content = io.BytesIO(response.content)
            mime_type = response.headers.get("content-type")

            media = MediaIoBaseUpload(
                fd=media_content, mimetype=mime_type, resumable=True
            )
            file_metadata = {
                "name": file_name,
                "parents": (
                    [folder_id]
                    if folder_id
                    else [creds["folder_id"]] if creds.get("folder_id") else []
                ),
            }

            file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )

            return file.get("id")

        except Exception as e:
            GoogleDriveAPI.logger.error(
                f"unable to upload file via url: {traceback.format_exc()}"
            )
            return {"error": str(e)}

    @staticmethod
    def share_file_or_folder(
        creds: dict,
        file_id: str,
        email_address: Union[str, List[str]],
        role: str = "reader",
    ) -> Optional[dict]:
        """Shares a file or folder with a specified email address."""
        try:
            # build service
            credentials = service_account.Credentials.from_service_account_info(
                creds["credentials"], scopes=creds["scopes"]
            )
            service = build(NAME, VERSION, credentials=credentials)

            if isinstance(email_address, list):
                for email in email_address:
                    permission = {"type": "user", "role": role, "emailAddress": email}
                    service.permissions().create(
                        fileId=file_id,
                        body=permission,
                        fields="id",
                        sendNotificationEmail=False,
                    ).execute()
            else:
                permission = {
                    "type": "user",
                    "role": role,
                    "emailAddress": email_address,
                }
                service.permissions().create(
                    fileId=file_id,
                    body=permission,
                    fields="id",
                    sendNotificationEmail=False,
                ).execute()
            return None
        except Exception as e:
            GoogleDriveAPI.logger.error(
                f"unable to share file: {traceback.format_exc()}"
            )
            return {"error": str(e)}

    @staticmethod
    def get_file_share_link(creds: dict, folder_id: str) -> Union[str, dict]:
        """Gets the shareable link for a file or folder."""
        try:
            credentials = service_account.Credentials.from_service_account_info(
                creds["credentials"], scopes=creds["scopes"]
            )
            service = build(NAME, VERSION, credentials=credentials)

            folder_metadata = (
                service.files().get(fileId=folder_id, fields="webViewLink").execute()
            )
            share_link = folder_metadata.get("webViewLink")
            return share_link
        except Exception as e:
            GoogleDriveAPI.logger.error(
                f"unable to get shared folder link: {traceback.format_exc()}"
            )
            return {"error": str(e)}

    @staticmethod
    def get_files_in_folder(creds: dict, folder_id: str) -> Union[List[dict], dict]:
        """Gets the list of files in a specified folder."""
        try:
            credentials = service_account.Credentials.from_service_account_info(
                creds["credentials"], scopes=creds["scopes"]
            )
            service = build(NAME, VERSION, credentials=credentials)

            results = (
                service.files()
                .list(q=f"'{folder_id}' in parents", fields="files(id, name)")
                .execute()
            )

            files = results.get("files", [])
            return files
        except Exception as e:
            GoogleDriveAPI.logger.error(
                f"unable to get files: {traceback.format_exc()}"
            )
            return {"error": str(e)}

    @staticmethod
    def move_to_trash(creds: dict, file_id: str) -> Union[dict, dict]:
        """Moves a file to the trash."""
        try:
            credentials = service_account.Credentials.from_service_account_info(
                creds["credentials"], scopes=creds["scopes"]
            )
            service = build(NAME, VERSION, credentials=credentials)

            body_value = {"trashed": True}

            response = service.files().update(fileId=file_id, body=body_value).execute()

            return response
        except Exception as e:
            GoogleDriveAPI.logger.error(
                f"unable to move to trash: {traceback.format_exc()}"
            )
            return {"error": str(e)}
