import logging
from datetime import datetime, timedelta, timezone
import uuid
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

NAME = 'calendar'
VERSION = 'v3'
class GoogleCalendarAPI:

    logger = logging.getLogger(__name__)

    @staticmethod
    def create_event(creds, event_info):
        credentials = service_account.Credentials.from_service_account_info(
            creds['credentials'], scopes=creds['scopes']
        )
        service = build(NAME, VERSION, credentials=credentials, cache_discovery=False)
        event = service.events().insert(calendarId=creds['calendar_id'], body=event_info).execute()
        return event

    @staticmethod
    def list_events(creds, maxResults=2500, singleEvents=True, orderBy="startTime"):
        credentials = service_account.Credentials.from_service_account_info(
            creds['credentials'], scopes=creds['scopes']
        )
        service = build(NAME, VERSION, credentials=credentials)
        now = datetime.now(timezone.utc).isoformat()
        if singleEvents:
            events_result = service.events().list(
                calendarId=creds['calendar_id'],
                timeMin=now,
                maxResults=maxResults,
                singleEvents=singleEvents,
                orderBy=orderBy
            ).execute()
        else:
            events_result = service.events().list(
                calendarId=creds['calendar_id'],
                timeMin=now,
                maxResults=maxResults,
                singleEvents=singleEvents
            ).execute()

        events = events_result.get("items", [])
        return events

    @staticmethod
    def get_event(creds, eventId):
        credentials = service_account.Credentials.from_service_account_info(
            creds['credentials'], scopes=creds['scopes']
        )
        service = build(NAME, VERSION, credentials=credentials)
        event = service.events().get(calendarId=creds['calendar_id'], eventId=eventId).execute()
        return event

    @staticmethod
    def delete_event(creds, event_id):
        try:
            credentials = service_account.Credentials.from_service_account_info(
                creds['credentials'], scopes=creds['scopes']
            )
            service = build(NAME, VERSION, credentials=credentials)
            service.events().delete(calendarId=creds['calendar_id'], eventId=event_id).execute()
            return True
        except Exception as e:
            return False

    @staticmethod
    def update_event(creds, eventId, updated_event_info):
        credentials = service_account.Credentials.from_service_account_info(
            creds['credentials'], scopes=creds['scopes']
        )
        service = build(NAME, VERSION, credentials=credentials)
        updated_event = service.events().update(
            calendarId=creds['calendar_id'],
            eventId=eventId,
            body=updated_event_info
        ).execute()
        return updated_event

    @staticmethod
    def update_webhook(creds, webhook_url, calendar_id, days_before=1):
        """
        Updates the webhook for a Google Calendar.

        Parameters:
        - creds: Credentials for Google API.
        - webhook_url: The URL to receive notifications.
        - calendar_id: The ID of the calendar to be watched.
        - channel_id: A unique ID for the channel(agent_id).
        - resource_id: The identifier for the watched resource.

        Returns:
        dict: A dictionary containing details of the channel, such as kind, id, resourceId, resourceUri, and expiration.
        """

        channel_id = uuid.uuid4().hex

        credentials = service_account.Credentials.from_service_account_info(
            creds['credentials'], scopes=creds['scopes']
        )

        service = build(NAME, VERSION, credentials=credentials)

        channel = {
            'id': channel_id,
            'type': 'web_hook',
            'address': webhook_url
        }

        try:
            response = service.events().watch(
                calendarId=calendar_id,  # Or use your specific calendar ID
                body=channel
            ).execute()

            # get x days before expiration
            timestamp_seconds = int(response['expiration']) / 1000
            expiration_datetime = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
            new_expiration_datetime = expiration_datetime - timedelta(days=days_before)
            expiration_timestamp = int(new_expiration_datetime.timestamp())
            response['before_expiration'] = expiration_timestamp
            
            return response
        except HttpError as error:
            GoogleCalendarAPI.logger.error(f"Error: {error}")
            return ""


    @staticmethod
    def validate_request(request, resource_id):
        try:
            # Ensure headers exist before accessing
            id = request.get("x-goog-resource-id")

            if not id:
                GoogleCalendarAPI.logger.error("Missing 'X-Goog-Resource-Id' header")
                return False

            return id == resource_id

        except AttributeError as e:
            GoogleCalendarAPI.logger.error(f"Invalid request object: {e}")
            return False
