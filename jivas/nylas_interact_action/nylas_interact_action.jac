import:py json;
import:py logging;
import:py traceback;
import:py time;
import:py from logging {Logger}
import:py from jivas.agent.modules.agentlib.utils {Utils}
import:jac from jivas.agent.memory.frame { Frame }
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.action.interact_action { InteractAction }
import:jac from jivas.agent.memory.interaction { Interaction }
import:jac from jivas.agent.action.interact_graph_walker { interact_graph_walker }
import:jac from jivas.agent.memory.interaction_response { TextInteractionMessage }




node NylasInteractAction :InteractAction: {
    # finds availabilies and schedules appointments on calendars

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has strict:bool = False; # if strict, only actions belonging to matched functions will be executed.
    has intent_prompt:str = "You are an intent classification model for determining what users want to do with their appointments. Perform the following steps to determine the intent of MESSAGE with context from HISTORY. Do not provide explanations, only the final output:\n1. For each key-value mapping in ANCHOR_INDEX, examine the list of statements in value mapped to each key against the MESSAGE.\n2. Determine which list of statements best align with the intent of MESSAGE.\n3. If there are one or more confident alignments, return the corresponding key or keys in a comma-separated list, otherwise, return 'unclassified'. \n\nMESSAGE: \n{utterance}\n\nANCHOR_INDEX: \n{anchor_index}\n\nHISTORY: \n{history}";
    has prompt:str = "Refer to the APPOINTMENT_DETAILS below to perform entity extraction of the best answer from the user message. Do not make up answers. The best answer should sensibly satisfy 'prompt' key under each main key in the APPOINTMENT_DETAILS structure. Users may give one word answers in response to questions so use the HISTORY to determine what is being asked and extract the answer. \n Reference the the current date and time, {current_date}, to determine date and time the user is specifying. If a valid answer is extracted from the user message, return only a JSON structure using the key from the APPOINTMENT_DETAILS structure below and the matching extracted answer from the user message as the value.\n If there is no valid extracted answer for a key, return an empty json struct. Return extracted data without markdown delimiters, JSON or explanations!\n APPOINTMENT_DETAILS: {appointment_details}\nHISTORY:{history}";
    has model_name:str = "gpt-4o";
    has history:bool = True;
    has history_size:int = 5;
    has model_max_tokens:int = 4096;
    has max_statement_length:int = 500;
    has nylas_model_action:str = "NylasCalendarAction";
    has model_action:str = "LangChainModelAction";
    has model_op:str = "chatopenai";
    has temperature:float = 0.2;
    has exceptions:list = ['FunctionInteractAction']; # list of actions which are included in intent, regardless
    has timezone:str = "America/Guyana";
    has nylas_version:str = "v3";
    has nylas_base_url:str = "";
    has grant_id:str = "";
    has nylas_api_key:str= "";
    has cal_email:str = "";
    has calendar_id:str = "5df1d2dd7bb48a398b19bc44a2bbd18b1e10949f86e209e9a04d17f74fda88fd@group.calendar.google.com";
    has appointments:list = [];
    has anchors:list = ["Appointment", "Booking", "Cancelling", "Rescheduling", "Schedule", "Details and information necessary to make a booking", "book for time", "mentioning services, emails, dates and times to book for", "scheduling", "reserving", "agreeing to dates and times", "time is good", "The user shares personal information such as name and email"];
    has intents:dict={
        "book_appointment":[
            "wanting to book appointment",
            "asking or giving information to book appointment",
            "finding available times to schedule appointments",
            "providing personal details such as name and email to book appointment"
        ],
        "cancel_appointment":[
            "wants to cancel appointment",
            "does not want to go to appointment anymore"
        ]
    };
    has services:dict={
        "exam":{
            "cost": 2000,
            "duration": 60
        },
        "check_up":{
            "cost": 1000,
            "duration": 30
        }
    };
    has appointment_details:dict={
        "purpose":{
            "prompt":"the reason for booking the appointment. Choose from list of options"
        },
        "date":{
            "prompt":"the date for an appointment in date format YYYY-MM-DD. Based on the utterance and the current date extract the most appropriate date. If the period involves a range of time such as week or month choose the first working day in the future available at the start of the range."
        },
        "time_of_day":{
            "prompt":"the time of day for an appointment. Choose from 'morning', 'noon' or 'afternoon'."
        },
        "start_time":{
            "prompt":"the time given by the user. Only return time in HH:MM:SS format. Do whatever conversion is necessary. Never return words. Do not extract terms such as 'morning' or 'afternoon' or 'anytime' as times. Only return times in the 8:00 to 16:30 time range"
        },
        "user_name":{
            "prompt": "the user's full name"
        },
        "email":{
            "prompt": "the user's email address. Extract any email the user gives in the format someone@domain.com"
        }
    };

    can touch(visitor: interact_graph_walker) -> bool {
        # authorize the interact to run
        if ("NylasInteractAction" not in (visitor.interaction_node.get_intents())) {
            return False;
        }
        else{
            return True; 
        }

    }

    can execute(visitor: interact_graph_walker) -> dict {
        intent ="";
 
       if(self.intents) {
            # grab the history
            history = visitor.frame_node.get_transcript(interactions = self.history_size, max_statement_length = self.max_statement_length);

            # prepare the prompt
            prompt_messages = [
                {"system": self.intent_prompt}
            ];
            
            # set the prompt variables
            prompt_variables = {
                "anchor_index": Utils.escape_string(json.dumps(self.intents)),
                "utterance": visitor.utterance,
                "history": history
            };           
                        
            result = None;

            if(model_action:=self.get_agent().get_actions().get(action_label=self.model_action)) {
                
                if(langchain_result := model_action.call_model(
                    prompt_messages = prompt_messages,
                    prompt_variables = prompt_variables,
                    kwargs = {
                        "model_name": self.model_name,
                        "model_temperature": self.temperature,
                        "model_max_tokens": self.model_max_tokens
                    },
                    interaction_node = visitor.interaction_node
            )) {
            
                result = langchain_result.get_json_result(); 
                if(not result){
                    result = langchain_result.get_result();
                }        
            }
                self.logger.debug(f"LLM result: {result}");
            }
            
            # add the resulting intent, if any to the interaction to trigger the relevant action(s)
            intent = result if result else "";
            saved_intent = {};
            if(intent == "unclassified"){
                saved_intent = visitor.frame_node.variable_get(key="nylas_intent");
                if(saved_intent){
                    if ("intent" in saved_intent) {
                        intent = saved_intent['intent'];
                    }   
                }
                else{
                    intent = "unclassified";
                }
            }
            visitor.frame_node.variable_set(key="nylas_intent", value = {"intent":intent});

        }


                
        base_version_url = self.nylas_base_url + "/" + self.nylas_version;
        grant_url = base_version_url + "/grants/" + self.grant_id;
        bearer_token = "Bearer " + self.nylas_api_key;
        
        # intent = visitor.frame_node.variable_get(key="nylas_intent");
        target_date = "";
        target_time = "";
        purpose = "";
        time_of_day = "";
        email = "";
        end_time="";
        user_name = "";
        customer_status = "";
        calendar_id = self.calendar_id;
        current_date = Utils.date_now(timezone=self.timezone, date_format='%Y-%m-%d %H:%M:%S');
        
        services_list = [];
        for service in self.services{
            service_name = service.replace("_", " ");
            services_list.append(service_name);
        }
        if(self.services){
            self.appointment_details['purpose']['options'] = services_list;
        }
        personal_details = visitor.frame_node.variable_get(key = "personal_details");
        if(personal_details){
            if('email' in personal_details){
                email = personal_details['email'];
            }
            if('user_name' in personal_details){
                user_name = personal_details['user_name'];
            }
        }

        if (self.history) {
            # grab the history
            prompt_messages = [];       
            statements = visitor.frame_node.get_transcript_statements(interactions = self.history_size, max_statement_length = self.max_statement_length);
            if (statements) {
                prompt_messages.extend(statements);
                self.logger.debug(f"history: {json.dumps(statements)}");
            }

            prompt_messages.extend([{"system": self.prompt}]);
            prompt_messages.extend([{"human": "{utterance}"}]);
        } else {
            # here we cater to whether we have context information or not..
            prompt_messages = [
                {"system": self.prompt},
                {"human": "{utterance}"}
            ];
        }     
        result_set = {};

        if(model_action := visitor.agent_node.get_actions().get(action_label=self.model_action)) {
            if( result_set := model_action.call_model(
                prompt_messages = prompt_messages,
                prompt_variables = {
                    "utterance": visitor.utterance,
                    "current_date": current_date,
                    "appointment_details": self.appointment_details,
                    "history": statements
                },
                kwargs = {
                    "model_name": self.model_name,
                    "model_temperature": self.temperature,
                    "model_max_tokens": self.model_max_tokens
                },
                interaction_node = visitor.interaction_node
            )) {
                result_struct = result_set.get_json_result();
            }
        }
        
        if(result_struct){
            #save details for appointment 
            answer_set = visitor.frame_node.variable_get(key = "appointment_details");
            if(not answer_set){
                answer_set = {};
            }
            if(result_struct){
                answer_set.update(result_struct);
            }
            visitor.frame_node.variable_set(key = "appointment_details", value = answer_set);
            result = visitor.frame_node.variable_get(key = "appointment_details");
            print(result);
            if(result){
                if('date' in result){
                    target_date = result['date'];
                }
                if("start_time" in result){
                    target_time = result['start_time'];
                }
                # if('end_time' in result): end_time = result['end_time'];
                if('purpose' in result){
                    purpose = result['purpose'];
                }
                if('time_of_day' in result){
                    time_of_day = result['time_of_day'];
                }
                if('email' in result){
                    email = result['email'];
                }
                if('user_name' in result){
                    user_name = result['user_name'];
                }
            }
        }
        email = email.lower();

        print("target date: ", target_date, "     target_time:", target_time, "    time of day", time_of_day);
        print("name ", user_name, "       email ", email, "      purpose: ", purpose, "      intent",intent);
        prompt_variables = {};
        
        if(nylas_action := visitor.agent_node.get_actions().get(action_label=self.nylas_model_action)){

            if(intent == "book_appointment"){
                if(not purpose){
                    purpose_prompt = "Ask the user for the reason they would like to book the appointment. Tell them they can choose from the list of {options}. Use natural language. Do not ask for anything else other than their reason";
                    purpose_prompt_directive = purpose_prompt.format(options=self.appointment_details["purpose"]["options"]);
                    visitor.interaction_node.add_directive(directive=purpose_prompt_directive);
                }
                elif(purpose){
                    purpose.lower();
                    purpose = purpose.replace(" ", "_");

                    # finds the nearest available times if no date or time are provided
                    if(not target_date and not target_time){
                        start_time = nylas_action.round_up_time(current_date);
                    }

                    #sets a time to start searching availability 
                    elif(target_date and not target_time){
                        if(time_of_day == "morning"){
                            start_time = target_date + " 08:00:00";
                        }
                        elif(time_of_day == "midday"){
                            start_time = target_date + " 11:30:00";
                        }
                        elif(time_of_day == "afternoon"){
                            start_time = target_date + " 13:00:00";
                        }
                        else{
                            start_time = target_date + " 08:00:00";
                        }
                        print(start_time);
                    }

                    elif(not target_date and target_time){
                        start_time = Utils.date_now() + " " + target_time;
                    }

                    elif(target_date and target_time){
                        start_time =target_date + " " + target_time;
                    }

                    if(purpose in self.services){
                        service_details = self.services[purpose];
                        if("cost" in service_details){
                            cost = service_details['cost'];
                        }
                        else{
                            cost = "";
                        }
                        if("duration" in service_details){
                            duration = service_details['duration'];
                        }
                        else{
                            duration = 60;
                        }
                    }

                    if(nylas_action.convert_to_epoch(start_time) < int(time.time())){
                        #ensures start time is in the future
                        epoch_time = nylas_action.convert_to_epoch(start_time);
                        current_epoch = int(time.time());
                        start_time = nylas_action.round_up_time(current_date);
                    }

                    times = nylas_action.get_available_times(start_time = start_time, base_url=base_version_url, duration= duration, cal_email=self.cal_email, calendar_id=calendar_id, bearer_token=bearer_token);
                
                    if(target_date and target_time){
                        if(start_time in times){
                            calendar_ids = [calendar_id];
                            if(not user_name){
                                # prompt_messages = [{"system": "Ask the user to give their name to make the booking under"}];
                                get_user_name_directive = "Ask the user to give their name to make the booking under";
                                visitor.interaction_node.add_directive(directive=get_user_name_directive);
                            }
                            elif(not email){
                                get_email_directive = "Ask the user to give their email so that you can schedule the booking on their calendar. Remind them to ensure that the correct email format is used";
                                visitor.interaction_node.add_directive(directive=get_email_directive);
                            }
                            if(email and user_name){
                                visitor.frame_node.variable_set(key = "personal_details", value = {"email":email, "user_name":user_name});
                                visitor.frame_node.variable_set(key = "appointment", value = {
                                    "bearer_token":bearer_token,
                                    "grant_url":grant_url,
                                    "calendar_ids":calendar_ids,
                                    "start_time":start_time,
                                    "duration":duration,
                                    "purpose":purpose,
                                    "cost":cost,
                                    "email":email,
                                    "user_name":user_name,
                                    "customer_status": customer_status}
                                );
                                approve_appointment_prompt = "Your goal is to tell the details of their appointment are service - {purpose}, date -  {target_date}, time - {target_time}, cost - ${cost} duration - {duration} minutes. Represent the prceding information as a bullet list. The appointment is for {user_name} at email {email}. Use commas to seperate currency values and represent time in HH:MM am/pm format. Ask them to read over the details to confirm that this information is correct. Ask if they would they like to schedule the booking now if everything looks alright";
                                approve_appointment_directive = approve_appointment_prompt.format(
                                    target_date=target_date,
                                    target_time=target_time,
                                    purpose=purpose,
                                    cost=cost,
                                    duration=duration,
                                    user_name=user_name,
                                    email=email
                                    );
                                visitor.interaction_node.add_directive(directive=approve_appointment_directive);
                                visitor.set_resume_action("NylasConfirmationAction"); 
                                #books appointment once it is determined that the time requested is available
                            }
                        }
                        else{
                            answer_set = visitor.frame_node.variable_get(key = "appointment_details");
                            answer_set.update({"start_time": ""});
                            time_unavailable_prompt = "Your goal is to let the user know that {date} at {time} is not available. Give them some currently available options. Be conversational and only give 3 other options currently available from {available}. Only use dates and times that are in 'available' list. Group times that fall under the same date. inform them that there are other times available too and they only need to ask and you will be able to tell them if it is available";
                            time_unavailable_directive = time_unavailable_prompt.format(date= target_date,time=target_time, available=times);
                            visitor.interaction_node.add_directive(directive=time_unavailable_directive);
                        }
                    }
                    elif(times){
                        date_time = times[0].split(" ");
                        date = date_time[0];
                        answer_set = visitor.frame_node.variable_get(key = "appointment_details");
                        answer_set.update({"date": date});

                        visitor.frame_node.variable_set(key = "appointment_details", value = answer_set);

                        available_prompt = "your goal is to inform the user that based on their request, the nearest available time they can select to book their appointment is at {times} but there are other times available. Represent time using the HH:MM am/pm format. \nAvoid giving more than 3 different times. Only use dates and times that are in available_times. DO not make up available times. \nGroup times that fall under the same date and show in the markdown list.";
                        available_prompt_directive = available_prompt.format(times=times);
                        visitor.interaction_node.add_directive(directive=available_prompt_directive);
                    }
                    elif(not times){
                        no_times_prompt = "Your goal is to inform the user that there are no available times for the date they requested. Ask them if they would like to try another date or time. Be conversational and offer to help them find a time that works for them";
                        visitor.interaction_node.add_directive(directive=no_times_prompt);
                    }
                }
            }

            if(intent == "cancel_appointment"){
                all_appointments = [];
                for appointment in nylas_action.appointments{
                    print("\nAppointment\n", appointment);
                    if(email){
                        if(appointment['email'] == email){
                            if(target_date and target_time){
                                if(appointment['date']==target_date and appointment['time']==target_time){
                                    all_appointments.append(appointment);
                                    appt_details = appointment;
                                    event_id = appointment['event_id'];
                                    print("appointment to cancel", all_appointments);
                                }
                            }
                            elif(target_date){
                                if(appointment['date']==target_date){
                                    all_appointments.append(appointment);
                                    appt_details = appointment;
                                    event_id = appointment['event_id'];
                                    print("appointment to cancel", appt_details);
                                }
                            }
                            elif(target_time){
                                if(appointment['time']==target_time){
                                    all_appointments.append(appointment);
                                    appt_details = appointment;
                                    event_id = appointment['event_id'];
                                    print("appointment to cancel", appt_details);
                                }
                            }
                            elif(not target_date and not target_time){
                                all_appointments.append(appointment);
                                appt_details = appointment;
                                event_id = appointment['event_id'];
                                print("appointment to cancel", appt_details);
                            }
                        }
                    }
                    else{
                        get_email_prompt = "Ask the user to give their email so that you can search for their scheduled apointments. Remind them to ensure that the correct email format is used and that they enter the same email they used to book the appointment";
                        visitor.interaction_node.add_directive(directive=get_email_prompt);
                    }
                }
                if(all_appointments){
                    booked_appointments: dict[str, list[str]] = {"date":[], "time":[], "purpose":[]};
                    for appointment in all_appointments{
                        booked_appointments['date'].append(appointment['date']);
                        booked_appointments['time'].append(appointment['time']);
                        booked_appointments['purpose'].append(appointment['purpose']);
                    }
                    if(len(all_appointments)>1){
                        get_appt_cancel_prompt = "Ask the user if they would like to cancel or reschedule {purpose} appointment set on {date} at {time}. List all appointments separately and ask them to please specify the date and time of the appointment they want to cancel. Represent time in HH:MM am/pm format. Do not give duplicate info";
                        appt_cancel_prompt_directive = get_appt_cancel_prompt.format(
                            purpose=booked_appointments['purpose'],
                            date=booked_appointments['date'],
                            time=booked_appointments["time"]
                        );
                        visitor.interaction_node.add_directive(directive=appt_cancel_prompt_directive);
                    }
                    else{
                        visitor.set_resume_action ("NylasConfirmationAction");
                       
                        visitor.frame_node.variable_set(key = "event", value={
                            "event_id":all_appointments[0]['event_id'],
                            "calendar_id":all_appointments[0]['calendar_id'],
                            "bearer_token":all_appointments[0]['bearer_token'],
                            "grant_url":all_appointments[0]['grant_url']
                        });
                        approve_cancellation_prompt = "Ask the user if they are sure they would like to cancel or reschedule {purpose} appointment set on {date} at {time}. Represent time in HH:MM am/pm format. Do not give duplicate info";
                        approve_cancellation_prompt_directive = approve_cancellation_prompt.format(
                            purpose=booked_appointments['purpose'],
                            date=booked_appointments['date'],
                            time=booked_appointments["time"]
                        );
                        visitor.interaction_node.add_directive(directive=approve_cancellation_prompt_directive); 
                    }
                }
            }
        }
        return visitor.export();
    }


    can healthcheck() -> bool {
        try {
            # Check core attributes that must exist and be correctly typed
            if (
                self.intent_prompt and
                self.prompt and
                self.model_name and
                self.model_max_tokens > 0 and
                self.max_statement_length > 0 and
                self.nylas_model_action and
                self.model_action and
                self.model_op and
                self.timezone and
                self.intents and
                self.nylas_version and
                self.nylas_base_url and
                self.nylas_api_key and
                self.calendar_id and
                self.services and 
                self.appointment_details
            ) {
                return True;  # All checks passed
            }

            return False;  # One of the type checks or presence checks failed
        } except Exception as e {
            self.logger.error(f"An exception occurred in {self.label}:\n{traceback.format_exc()}\n");
            return False;
        }
    }
}