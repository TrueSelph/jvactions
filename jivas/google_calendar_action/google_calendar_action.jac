import:py os;
import:py pytz;
import:py logging;
import:py traceback;
import:py from logging {Logger}
import:py from datetime { datetime }
import:jac from jivas.agent.action.action { Action }
import:py from jvserve.lib.agent_interface { AgentInterface }
import:py from .modules.google_calendar_api {GoogleCalendarAPI}

node GoogleCalendarAction :Action: {
    
    has timezone:str = "America/Guyana";
    has scopes:list = ["https://www.googleapis.com/auth/calendar"];
    has calendar_id:str = "test@group.calendar.google.com";
    has base_url:str = "";
    has webhook_url:str = "";
    has resource_id:str = "";
    has expiration:int = 0;
    has last_modified_timestamp:int = 0;
    has info_type:str = "service_account";
    has project_id:str = "jivas-99999";
    has private_key_id:str = "2724242c4d8ee40d99999";
    has private_key:str = "-----BEGIN PRIVATE KEY-----";
    has client_email:str = "trueselph@jivas.iam.gserviceaccount.com";
    has client_id:str = "10778319399999";
    has auth_uri:str = "https://accounts.google.com/o/oauth2/auth";
    has token_uri:str = "https://oauth2.googleapis.com/token";
    has auth_provider_x509_cert_url:str = "https://www.googleapis.com/oauth2/v1/certs";
    has client_x509_cert_url:str = "https://www.googleapis.com/robot/v1/metadata/x509/trueselph%40jivas-422314.iam.gserviceaccount.com";
    has universe_domain:str = "googleapis.com";


    can on_enable() {
        # check if enabled
        if(self.enabled) {
            # register polls webhook
            self.enabled = self.on_register();
        }
    }

    can on_register() -> bool {
        if (not self.base_url) {
            # default to jivas base url in environment
            self.base_url = os.environ.get('JIVAS_BASE_URL');
        }

        if(self.enabled) {
            # setup procedure for webhook registration on google calendar api
            agent_id = self.get_agent().id; 
            module_root = self.get_module_root();
            # generate webhook key
            webhook_key = AgentInterface.encrypt_webhook_key(agent_id=agent_id, module_root=module_root, walker="google_calendar_interact");

            if(self.enabled and self.base_url and webhook_key) {
                # complete the full webhook url
                self.webhook_url = f'{self.base_url}/webhook/{webhook_key}';
                
                credentials = self.get_credentials();
                result = GoogleCalendarAPI.update_webhook(credentials, self.webhook_url, self.calendar_id, 2);
                self.resource_id = result["resourceId"];
                self.expiration = int(result["before_expiration"]);
                return True;
            } else {
                self.logger.error('unable to generate webhook url for Google Calendar, missing required parameters');
            }
            return False;
        }
    }

    can validate_request(headers:dict) -> bool {
        current_timestamp = int((datetime.now(pytz.timezone(self.timezone))).timestamp()); 

        valid_request = GoogleCalendarAPI.validate_request(headers, self.resource_id);
        if(valid_request) {
            self.last_modified_timestamp = int(current_timestamp);
        }

        if(current_timestamp > self.expiration and self.enabled){
            self.register_google_calendar_webhook();
        }

        return valid_request;
    }
    

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

    can healthcheck() -> bool {
        try {
            if(
                self.timezone and
                self.scopes and 
                self.calendar_id and 
                self.base_url and 
                self.webhook_url and
                self.info_type and
                self.project_id and 
                self.private_key_id and 
                self.private_key and 
                self.client_email and 
                self.client_id and 
                self.auth_uri and 
                self.token_uri and 
                self.auth_provider_x509_cert_url and 
                self.client_x509_cert_url and 
                self.universe_domain
            ) {
                return True;
            }
            return False;
        } except Exception as e {
            self.logger.error(f"An exception occurred in {self.label}:\n{traceback.format_exc()}\n");
            return False;
        }
    }

}


