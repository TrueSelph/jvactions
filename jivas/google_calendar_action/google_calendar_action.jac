import:py logging;
import:py traceback;
import:py from logging {Logger}
import:jac from agent.action.action { Action }
import:py from .modules.google_calendar_api {GoogleCalendarAPI}

node GoogleCalendarAction :Action: {
    has name:str = "google_calendar_action";
    has description:str = "Manages events and schedules on the specified Google Calendar.";
    has scopes:list = ["https://www.googleapis.com/auth/calendar"];
    has calendar_id:str = "";

    has info_type:str = "service_account";
    has project_id:str = "";
    has private_key_id:str = "";
    has private_key:str = "";
    has client_email:str = "";
    has client_id:str = "";
    has auth_uri:str = "https://accounts.google.com/o/oauth2/auth";
    has token_uri:str = "https://oauth2.googleapis.com/token";
    has auth_provider_x509_cert_url:str = "https://www.googleapis.com/oauth2/v1/certs";
    has client_x509_cert_url:str = "";
    has universe_domain:str = "googleapis.com";


    can get_credentials() -> dict {

        credentials = {
            "credentials": {
                "type": self.info_type,
                "project_id": self.project_id,
                "private_key_id": self.private_key_id,
                "private_key": self.private_key,
                "client_email": self.client_email,
                "client_id": self.client_id,
                "auth_uri": self.auth_uri,
                "token_uri": self.token_uri,
                "auth_provider_x509_cert_url": self.auth_provider_x509_cert_url,
                "client_x509_cert_url": self.client_x509_cert_url,
                "universe_domain": self.universe_domain
            },
            "scopes": self.scopes,
            "calendar_id": self.calendar_id
        };
        return credentials;
    }


    can create_event(event_info:dict) -> dict {
        credentials = self.get_credentials();
        event = GoogleCalendarAPI.create_event(credentials, event_info);
        return event;
    }


    can list_events(max_results:int = 2500, singleEvents:bool = True, orderBy:str = "startTime") -> list {
        credentials = self.get_credentials();
        events = GoogleCalendarAPI.list_events(credentials, maxResults=max_results, singleEvents=singleEvents, orderBy=orderBy);
        return events;
    }


    can get_event(event_id:str) -> dict {
        credentials = self.get_credentials();
        event = GoogleCalendarAPI.get_event(credentials, event_id);
        return event;
    }


    can update_event(event_id:str, event_info:dict) -> dict {
        credentials = self.get_credentials();
        event = GoogleCalendarAPI.update_event(credentials, event_id, event_info);
        return event;
    }


    can delete_event(event_info:dict) -> bool {
        credentials = self.get_credentials();
        result = GoogleCalendarAPI.delete_event(credentials, event_info);
        return result;
    }

}


