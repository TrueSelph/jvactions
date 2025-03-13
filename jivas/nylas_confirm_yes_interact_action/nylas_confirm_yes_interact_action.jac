import:py json;
import:py logging;
import:py traceback;
import:py time;
import:py from logging {Logger}
import:jac from jivas.agent.memory.frame { Frame }
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.action.interact_action { InteractAction }
import:jac from jivas.agent.action.interact_graph_walker { interact_graph_walker }
import:jac from jivas.agent.action.model_action { ModelAction, ModelActionResult }



node ConfirmBookingAction :InteractAction: {

    # creates calendar bookings
    has description:str = "creates events on calendars ";
    has appointment_booked_prompt:str = "Your goal is to tell the user their appointment has been booked. Also warn them that arriving 15 minutes after the appointment time or later may lead to the forfeit of their appointment. Ask if they need help with anything else. Use commas to seperate currency values";
    has nylas_action:str = "NylasCalendarAction";
    has appointments:list = [];

    can touch(visitor: interact_graph_walker) -> bool {
        if(visitor.utterance or (visitor.resume_action_node == self)) {
            return True;
        }

        else{
            return False;
        }
    }

    can execute(visitor: interact_graph_walker) -> dict {
        intent = visitor.frame_node.variable_get(key="nylas_intent");
        nylas_action = visitor.agent_node.get_actions().get(action_label=self.nylas_action);
        
        if(intent['intent'] == "book_appointment"){
            appt = {};
            appt = visitor.frame_node.variable_get(key = "appointment");
            for calendar_id in appt['calendar_ids']{
                event = nylas_action.create_event(
                    bearer_token=appt["bearer_token"],
                    grant_url=appt["grant_url"],
                    calendar_id=calendar_id,
                    start_time=appt["start_time"],
                    duration=appt["duration"],
                    purpose=appt["purpose"],
                    email=appt["email"],
                    user_name=appt["user_name"]
                    # customer_status= appt["customer_status"]
                );
            }
            if(event){
                date_time = appt["start_time"].split(" ");
                date = date_time[0];
                time = date_time[1];
                created_appt = {
                    "bearer_token":appt["bearer_token"],
                    "grant_url": appt["grant_url"],
                    "event_id": event['data']['id'],
                    "calendar_id": event['data']['calendar_id'],
                    "date": date,
                    "time": time,
                    "duration":appt["duration"],
                    "purpose":appt["purpose"],
                    "cost":appt['cost'],
                    "email":appt["email"],
                    "user_name":appt["user_name"]
                    # "customer_status": customer_statuss
                };
                nylas_action.appointments.append(created_appt);
                visitor.frame_node.get_agent().export_descriptor();
                visitor.frame_node.variable_set(key = "appointment_details", value={});
                visitor.frame_node.variable_set(key = "appointment", value={});
                visitor.interaction_node.add_directive(directive=self.appointment_booked_prompt);
            }
        }

        if(intent['intent'] == "cancel_appointment"){
            event = visitor.frame_node.variable_get(key = "event");
            deleted_event = nylas_action.delete_event(
                grant_url=event["grant_url"],
                calendar_id=event['calendar_id'],
                event_id=event['event_id'],
                bearer_token=event['bearer_token']
            );
            if(deleted_event){
                for appointment in nylas_action.appointments{
                    if(event['event_id'] == appointment['event_id']){
                        nylas_action.appointments.remove(appointment);
                    }
                }
                appointment_deleted_prompt = "Tell the user that the appointment has been successfully cancelled";
                visitor.interaction_node.add_directive(directive=appointment_deleted_prompt);
                visitor.frame_node.variable_set(key = "event", value={});

            }
        }
        # nylas_action_node = visitor.agent_node.get_actions().get(action_label="NylasInteractAction");
        # Interact.dequeue_interact_action(nylas_action_node);
        visitor.dequeue_action("NylasInteractAction");
        visitor.set_next_action("PersonaInteractAction");
        return visitor.export();
    }


    can healthcheck() -> bool {
        try {
            if (self.appointment_booked_prompt and self.nylas_action) {
                return True;
            }

            return False;
        } except Exception as e {
            self.logger.error(f"An exception occurred in {self.label}:\n{traceback.format_exc()}\n");
            return False;
        }
    }

}
