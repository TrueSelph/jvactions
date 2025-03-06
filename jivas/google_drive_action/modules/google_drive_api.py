from datetime import datetime, timezone
import io
import logging
import traceback
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.discovery import build
import requests

NAME = 'drive'
VERSION = 'v3'

class GoogleDriveAPI:
    
    logger = logging.getLogger(__name__)
    
    @staticmethod
    def create_folder(creds, folder_name):
        try:
            # build service
            credentials = service_account.Credentials.from_service_account_info(
                creds['credentials'], scopes=creds['scopes']
            )
            service = build(NAME, VERSION, credentials=credentials)
            
            # action
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }

            if creds['folder_id']:
                folder_metadata['parents'] = [creds['folder_id']]

            folder = service.files().create(body=folder_metadata, fields='id').execute()
            return folder.get('id')
        except Exception as e:
            GoogleDriveAPI.logger.error(f"unable to create folder: {traceback.format_exc()}")
            return {'error': e }


    @staticmethod
    def upload_file(creds, file_path, file_name, folder_id):
        try:
            # build service
            credentials = service_account.Credentials.from_service_account_info(
                creds['credentials'], scopes=creds['scopes']
            )
            service = build(NAME, VERSION, credentials=credentials)

            # action
            media = MediaFileUpload(file_path)
            file_metadata = {
                'name': file_name
            }

            if folder_id:
                file_metadata['parents'] = [folder_id]
            else:
                file_metadata['parents'] = [creds['folder_id']]

            file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            return file.get('id')
        except Exception as e:
            GoogleDriveAPI.logger.error(f"unable to upload file: {traceback.format_exc()}")
            return {'error': e }


    @staticmethod
    def upload_file_via_url(creds, url, file_name, folder_id):
        try:
            # build service
            credentials = service_account.Credentials.from_service_account_info(
                creds['credentials'], scopes=creds['scopes']
            )
            service = build(NAME, VERSION, credentials=credentials)

            # upload_file
            response = requests.get(url)
            media_content = io.BytesIO(response.content)
            mime_type = response.headers.get('content-type')

            media = MediaIoBaseUpload(fd=media_content, mimetype=mime_type, resumable=True)
            file_metadata = {'name': file_name}

            if folder_id:
                file_metadata['parents'] = [folder_id]
            else:
                file_metadata['parents'] = [creds['folder_id']]

            file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

            return file.get('id')
        
        except Exception as e:
            GoogleDriveAPI.logger.error(f"unable to upload file via url: {traceback.format_exc()}")
            return {'error': e}
    
    
    @staticmethod
    def share_file_or_folder(creds, file_id, email_address, role='reader'):
        try:
            # build service
            credentials = service_account.Credentials.from_service_account_info(
                creds['credentials'], scopes=creds['scopes']
            )
            service = build(NAME, VERSION, credentials=credentials)

            # action
        
            if type(email_address) == list:
                for email in email_address:

                    permission = {
                        'type': 'user',
                        'role': role,
                        'emailAddress': email

                    }
                    service.permissions().create(fileId=file_id, body=permission, fields='id', sendNotificationEmail=False).execute()

            else:
                permission = {
                    'type': 'user',
                    'role': role,
                    'emailAddress': email_address

                }
                service.permissions().create(fileId=file_id, body=permission, fields='id', sendNotificationEmail=False).execute()

        except Exception as e:
            GoogleDriveAPI.logger.error(f"unable to share file: {traceback.format_exc()}")
            return {'error': e }


    @staticmethod
    def get_file_share_link(creds, folder_id):
        try:
            # build service
            credentials = service_account.Credentials.from_service_account_info(
                creds['credentials'], scopes=creds['scopes']
            )
            service = build(NAME, VERSION, credentials=credentials)

            # action
            # Get the folder metadata
            folder_metadata = service.files().get(fileId=folder_id, fields='webViewLink').execute()

            # Extract the web view link from the metadata
            share_link = folder_metadata.get('webViewLink')

            return share_link
        except Exception as e:
            GoogleDriveAPI.logger.error(f"unable to get shared folder link: {traceback.format_exc()}")
            return {'error': e }
        

    @staticmethod
    def get_files_in_folder(creds, folder_id):
        try:
            # build service
            credentials = service_account.Credentials.from_service_account_info(
                creds['credentials'], scopes=creds['scopes']
            )
            service = build(NAME, VERSION, credentials=credentials)

            # action
            results = service.files().list(
                q=f"'{folder_id}' in parents",
                fields="files(id, name)"
            ).execute()

            files = results.get('files', [])
            return files
        except Exception as e:
            GoogleDriveAPI.logger.error(f"unable to get files: {traceback.format_exc()}")
            return {'error': e }


    @staticmethod
    def move_to_trash(creds, file_id):
        try:
            # build service
            credentials = service_account.Credentials.from_service_account_info(
                creds['credentials'], scopes=creds['scopes']
            )
            service = build(NAME, VERSION, credentials=credentials)

            # action
            body_value = {'trashed': True}

            response = service.files().update(fileId=file_id, body=body_value).execute()

            return response
        except Exception as e:
            GoogleDriveAPI.logger.error(f"unable to move to trash: {traceback.format_exc()}")
            return {'error': e }

