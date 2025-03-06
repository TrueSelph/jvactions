import:py json;
import:py logging;
import:py traceback;
import:py time;
import:py from logging {Logger}
import:py from jivas.agent.modules.agentlib.utils {Utils}
import:jac from jivas.agent.memory.frame { Frame }
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.action.interact_action { InteractAction }
import:jac from jivas.agent.action.interact { Interact }
import:jac from jivas.agent.action.interact_graph_walker { interact_graph_walker }
import:jac from jivas.agent.memory.interaction_response { TextInteractionMessage }




node NylasConfirmationAction :InteractAction: {
    # finds availabilies and schedules appointments on calendars

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has strict:bool = True; # if strict, only actions belonging to matched functions will be executed.
    has intent_prompt:str = "You are an intent classification model for determining what users want to do with their appointments. Perform the following steps to determine the intent of MESSAGE with context from HISTORY. Do not provide explanations, only the final output:\n1. For each key-value mapping in ANCHOR_INDEX, examine the list of statements in value mapped to each key against the MESSAGE.\n2. Determine which list of statements best align with the intent of MESSAGE.\n3. If there are one or more confident alignments, return the corresponding key or keys in a comma-separated list, otherwise, return 'unclassified'. \n\nMESSAGE: \n{utterance}\n\nANCHOR_INDEX: \n{anchor_index}\n\nHISTORY: \n{history}";
    has prompt:str = "";
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
    has appointments:list = [];
    has intents:dict={
        "confirm_yes":[
            "yes",
            "sure",
            "ok",
            "looks good",
            "go ahead",
            "that's right",
            "book it",
            "cancel"
        ],
        "confirm_no":[
            "nevermind",
            "don't book appointment",
            "don't cancel"
        ],
        "amend_data":[
            "there's something wrong",
            "no, the right thing is ...",
            "change",
            "amend",
            "can I book for other time instead"
        ]
    };
   
    can touch(visitor: interact_graph_walker) -> bool {
        # authorize the interact to run
        if(visitor.utterance) {
            return True; 
        }
        else{
            return False;
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
            }
            
            if(result) {
                # add the resulting intent, if any to the interaction to trigger the relevant action(s)
                saved_intent = visitor.frame_node.variable_get(key="nylas_intent");
                intent = result;

                if(intent == "confirm_yes"){
                    visitor.set_next_action("ConfirmBookingAction");
                }

                if(intent == "confirm_no"){
                    # clears the appointment details
                    visitor.frame_node.variable_set(key = "appointment_details", value={});
                    
                    if(saved_intent['intent'] == "book_appointment"){
                        visitor.frame_node.variable_set(key = "appointment", value={});
                        response_prompt = "Tell the user that no appointment was booked but you will be there to help whenever they are ready to schedule or cancel one";
                    }
                    if(saved_intent['intent'] == "cancel_appointment"){
                        visitor.frame_node.variable_set(key = "event", value={});
                        response_prompt = "Tell the user that no appointment was cancelled but you will be there to help whenever they are ready to schedule or cancel one";
                    }
                    visitor.interaction_node.add_directive(directive=response_prompt);
                    visitor.set_dequeue_action("NylasInteractAction");
                }
                
                if(intent == "amend_data"){
                    response_prompt = "Tell the user that you will make the necessarry changes to make sure the information is accurate";
                    visitor.interaction_node.add_directive(directive=response_prompt);
                }

                if(intent == "unclassified"){
                    # warning message if the user seems to be abandoning the process
                    if(saved_intent['intent'] == "book_appointment"){
                        response_prompt = "Tell the user that no appointment was booked but their information has been saved and that you will be there to continue the process whenever they are ready to schedule or cancel one";
                    }
                    if(saved_intent['intent'] == "cancel_appointment"){
                        response_prompt = "Tell the user that no appointment was cancelled but their information has been saved and that you will be there to continue the process whenever they are ready to schedule or cancel one";
                    }
                    visitor.interaction_node.add_directive(directive=response_prompt);
                    visitor.set_next_action("PersonaInteractAction");
                }
            }    
        }
        return visitor.export();
    }
}