import:py json;
import:py logging;
import:py traceback;
import:py from datetime { datetime, timedelta }
import:py time; 
import:py pytz; 
import:py requests; 
import:py from logging {Logger}
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.memory.frame { Frame }


node NylasCalendarAction :Action: {
    # finds availabilies and schedules appointments on calendars

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has strict:bool = True; # if strict, only actions belonging to matched functions will be executed.
    has prompt:str = "";
    has model_name:str = "";
    has history_size:int = 5;
    has max_statement_length:int = 500;
    has model_action:str = "LangchainAction";
    has model_op:str = "chatopenai";
    has temperature:float = 0.2;
    has model_max_tokens:int = 4096;
    has timezone:str = "America/Guyana";
    has top_n:int = 3;
    has services:dict={};
    has appointments:list = [];
    has open_hours:list = [
        {
            "days": [
                1,
                2,
                3,
                4,
                5
            ],
            "timezone": "America/Guyana",
            "start": "8:00",
            "end": "16:30"
        },
        {
            "days": [6],
            "timezone": "America/Guyana",
            "start": "9:00",
            "end": "14:00"
        }
    ];


    can get_available_times(start_time: str, base_url:str, duration: int, cal_email:str, calendar_id:str, end_time: str="", bearer_token:str="", date_format:str="%Y-%m-%d %H:%M:%S") -> list {
        url = base_url + "/calendars/availability";
        #checks for availablity for a 3 day period
        if(not end_time){
            time_after = 3;
            period = "days";
            end_time = self.find_time_after_duration(start_time, period, time_after);
        }
        
        epoch_start_time = self.convert_to_epoch(start_time);
        epoch_end_time = self.convert_to_epoch(end_time);

        search_details = {
            "participants": [
                {
                    "email": cal_email, 
                    "calendar_ids": [calendar_id]
                }
            ],
            "duration_minutes": duration,
            "start_time": epoch_start_time,
            "end_time": epoch_end_time,
            "interval_minutes": duration,
            "round_to": duration,
            "availability_rules": {
                "default_open_hours": self.open_hours
            }
        };
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': bearer_token
        };
        payload = json.dumps(search_details);

        response = requests.request("POST", url, headers=headers, data=payload);

        available = response.json();

        times:list = [];
        if("data" in available){
            n = 0;
            for time in available["data"]["time_slots"]{
                start_times = self.convert_timestamp(time["start_time"]);
                if(start_times not in times){
                    times.append(start_times);
                    n+=1;
                }
                if(n == self.top_n){
                    break;
                }
            }
        }    
        return times;
    }

    can create_event(start_time:str, grant_url:str, duration:int, purpose:str, calendar_id:str, user_name:str, email:str, bearer_token:str="", location:str="Georgetown", timezone:str="America/Guyana") -> dict {
        url = grant_url + "/events?calendar_id=" + calendar_id;

        period = "minutes";
        end_time = self.find_time_after_duration(start_time, period, duration);
        start_epoch_time = self.convert_to_epoch(time=start_time);
        end_epoch_time = self.convert_to_epoch(time=end_time);

        event_info = {
            "title": purpose,
            "busy": True,
            "participants": [
                {
                    "name": user_name,
                    "email": email
                }
            ],
            "description": user_name,
            "when": {
                "start_time": start_epoch_time,
                "end_time": end_epoch_time,
                "start_timezone": timezone,
                "end_timezone": timezone
            },
            "location": location
        };

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": bearer_token
        };
        # Convert payload to JSON string
        payload_json = json.dumps(event_info);

        # Send POST request
        response = requests.request("POST", url, headers=headers, data=payload_json);
        event= response.json();

        date_time = start_time.split(" ");
        date = date_time[0];
        time = date_time[1];
        if("data" in event){
            event_id = event['data']['id'];
            calendar_id = event['data']['calendar_id'];
        }
        return event;
    }

    can delete_event(grant_url:str, calendar_id:str, event_id:str, bearer_token:str) -> str{
        url = grant_url + "/events/" + event_id + "?notify_participants=true&calendar_id=" + calendar_id;
        payload:dict = {};
        headers = {
            'Accept': 'application/json',
            'Authorization': bearer_token
        };
        response = requests.request("DELETE", url, headers=headers, data=payload);

        return (response.text);        
    }

    can get_all_events(grant_url:str, calendar_id:str, bearer_token:str) -> dict{
        url = self.grant_url + "/events?limit=50&calendar_id=" + self.calendar_id;
        payload:dict = {};
        headers = {
        'Accept': 'application/json',
        'Authorization': bearer_token
        };
        response = requests.request("GET", url, headers=headers, data=payload);

        return response.json();
    }

    can get_event(grant_url:str, calendar_id:str, event_id:str , bearer_token:str) -> str{
        bearer_token = "Bearer " + self.nylas_api_key;
        url = grant_url + "/events/" + event_id + "?calendar_id=" + calendar_id;
        payload: dict[str, str] = {};
        headers = {
            'Accept': 'application/json',
            'Authorization': bearer_token
        };

        response = requests.request("GET", url, headers=headers, data=payload);

        return response.json();
    }

    can convert_to_epoch(time:str, timezone:str = "America/Guyana", date_format:str = "%Y-%m-%d %H:%M:%S") -> int{
        try{
            # Create a timezone object based on the provided timezone_str
            input_tz = pytz.timezone(timezone);

            # Parse the date string into a datetime object
            time_strp = datetime.strptime(time, date_format);
            localized_time = input_tz.localize(time_strp);

            # Convert to UTC
            utc_time = localized_time.astimezone(pytz.utc);

            # Convert datetime objects to epoch times (Unix timestamp)
            epoch_time = int(utc_time.timestamp());

            return epoch_time;
        }
        
        except Exception{
            return 0;
        }
    }

    can find_time_after_duration(time:str, period:str, duration:int, date_format:str = "%Y-%m-%d %H:%M:%S") -> str{
        # returns the time after a specified duration
        try{
            start_time = datetime.strptime(time, date_format);
            if period == "seconds"{
                end_time = start_time + timedelta(seconds=duration);
            }
            elif period == "minutes"{
                end_time = start_time + timedelta(minutes=duration);
            }
            elif period == "hours"{
                end_time = start_time + timedelta(hours=duration);
            }
            elif period == "days"{
                end_time = start_time + timedelta(days=duration);
            }
            elif period == "weeks"{
                end_time = start_time + timedelta(weeks=duration);
            }
            formatted_end_time = end_time.strftime(date_format);  
            return formatted_end_time;
        }
        except Exception{
            return "";
        }
    }

    can convert_timestamp(epoch_timestamp:int, timezone:str = "America/Guyana", date_format:str = "%Y-%m-%d %H:%M:%S") -> str{
        try{
            # Create a timezone object based on the provided timezone_str
            tz = pytz.timezone(timezone);

            # Convert the epoch timestamp to a datetime object
            dt = datetime.fromtimestamp(epoch_timestamp, tz=pytz.UTC);

            # Convert the datetime to the specified timezone
            dt = dt.astimezone(tz);

            # Format the datetime according to the provided format
            formatted_datetime = dt.strftime(date_format);

            return formatted_datetime;
        }
        except Exception{
            return "";
        }
    }

    can round_up_time(time:str, date_format:str = "%Y-%m-%d %H:%M:%S") -> str{
        time_strp = datetime.strptime(time, date_format);
        # Rounds up to next half hour by adding 30 minutes to current hour
        new_time = time_strp.replace(second=0, minute=0, hour=time_strp.hour) + timedelta(minutes=((time_strp.minute//30)+1)*30);
        formatted_new_time = new_time.strftime(date_format);
        return formatted_new_time;
    }

        can healthcheck() -> bool {
        try {
            if (self.prompt and
                self.model_name and
                self.history_size and
                self.max_statement_length > 0 and
                self.model_action and
                self.model_op and
                self.model_max_tokens and
                self.timezone and
                self.top_n > 0
            ) {
                # Validate the 'open_hours' structure
                if (type(self.open_hours) == list && len(self.open_hours) > 0) {
                    # Required subkeys for each open_hours entry
                    required_keys = ["days", "timezone", "start", "end"];

                    for _entry in self.open_hours {
                        # Check if each entry is a dictionary
                        if (type(_entry) != dict) {
                            return False;  # Entry is not a dictionary
                        }
                        
                        # Ensure all required keys are present
                        for key in required_keys {
                            if (key not in _entry) {
                                return False;  # Missing a required key
                            }
                        }

                        # Validate 'days' is a list of integers
                        if (type(_entry.days) != list) {
                            return False; # Invalid 'days' format
                        }

                        # Validate 'timezone', 'start', 'end' are strings
                        if (type(_entry.timezone) != str || type(_entry.start) != str || type(_entry.end) != str) {
                            return False;  # Invalid type for 'timezone', 'start', or 'end'
                        }
                    }

                    return True;  # All checks passed for open_hours
                }

                return False;  # open_hours is not a valid list
            }

            return False;  # One of the other conditions failed
        } except Exception as e {
            self.logger.error(f"An exception occurred in {self.label}:\n{traceback.format_exc()}\n");
            return False;  # Catch-all for unexpected errors
        }
    }
}
