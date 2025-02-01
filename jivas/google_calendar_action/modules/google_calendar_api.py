"""This module contains the GoogleCalendarAPI class which is used to interact with the Google Calendar API."""

from datetime import datetime, timezone

from google.oauth2 import service_account
from googleapiclient.discovery import build

NAME = "calendar"
VERSION = "v3"


class GoogleCalendarAPI:
    """Class for interacting with the Google Calendar API."""

    @staticmethod
    def create_event(creds: dict, event_info: dict) -> dict:
        """Creates an event in the Google Calendar."""
        credentials = service_account.Credentials.from_service_account_info(
            creds["credentials"], scopes=creds["scopes"]
        )
        service = build(NAME, VERSION, credentials=credentials)
        event = (
            service.events()
            .insert(calendarId=creds["calendar_id"], body=event_info)
            .execute()
        )
        return event

    @staticmethod
    def list_events(
        creds: dict,
        max_results: int = 2500,
        single_events: bool = True,
        order_by: str = "startTime",
    ) -> list:
        """Lists events from the Google Calendar."""
        credentials = service_account.Credentials.from_service_account_info(
            creds["credentials"], scopes=creds["scopes"]
        )
        service = build(NAME, VERSION, credentials=credentials)
        now = datetime.now(timezone.utc).isoformat()
        if single_events:
            events_result = (
                service.events()
                .list(
                    calendarId=creds["calendar_id"],
                    timeMin=now,
                    maxResults=max_results,
                    singleEvents=single_events,
                    orderBy=order_by,
                )
                .execute()
            )
        else:
            events_result = (
                service.events()
                .list(
                    calendarId=creds["calendar_id"],
                    timeMin=now,
                    maxResults=max_results,
                    singleEvents=single_events,
                )
                .execute()
            )

        events = events_result.get("items", [])
        return events

    @staticmethod
    def get_event(creds: dict, event_id: str) -> dict:
        """Gets an event from the Google Calendar."""
        credentials = service_account.Credentials.from_service_account_info(
            creds["credentials"], scopes=creds["scopes"]
        )
        service = build(NAME, VERSION, credentials=credentials)
        event = (
            service.events()
            .get(calendarId=creds["calendar_id"], eventId=event_id)
            .execute()
        )
        return event

    @staticmethod
    def delete_event(creds: dict, event_id: str) -> bool:
        """Deletes an event from the Google Calendar."""
        try:
            credentials = service_account.Credentials.from_service_account_info(
                creds["credentials"], scopes=creds["scopes"]
            )
            service = build(NAME, VERSION, credentials=credentials)
            service.events().delete(
                calendarId=creds["calendar_id"], eventId=event_id
            ).execute()
            return True
        except Exception:
            return False

    @staticmethod
    def update_event(creds: dict, event_id: str, updated_event_info: dict) -> dict:
        """Updates an event in the Google Calendar."""
        credentials = service_account.Credentials.from_service_account_info(
            creds["credentials"], scopes=creds["scopes"]
        )
        service = build(NAME, VERSION, credentials=credentials)
        updated_event = (
            service.events()
            .update(
                calendarId=creds["calendar_id"],
                eventId=event_id,
                body=updated_event_info,
            )
            .execute()
        )
        return updated_event
