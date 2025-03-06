import:py logging;
import:py traceback;
import:py from logging {Logger}
import:jac from jivas.agent.action.interact_action { InteractAction }
import:jac from jivas.agent.action.interact_graph_walker { interact_graph_walker }

node InterviewInteractAction :InteractAction: {
    # Accepts a collection of questions and orchestrates a conversation to gatther responses from the user

    has intro_directive:str = "Explain that you are about to ask a few questions to gather some information.";
    has task_directive:str = "Ask the question: '{question}'.";
    has outtro_directive:str = "Explain that there are no more questions. Thank the user for participating.";
    has functions:list = [];

    has question_index:dict = {
        "full_name": {
            "question":"What is your full name?", 
            "description": "a person's full name including their first, middle (if any) and last name", 
            "type": "string", 
            "required": True
        },
        "age": {
            "question":"How old are you?", 
            "description": "the age of person", 
            "type": "string", 
            "required": True
        },
        "purpose_of_visit": {
            "question":"What is the purpose of your visit today?", 
            "description": "a descriptive reason for visiting the clinic", 
            "type": "string", 
            "required": False
        }
    };
    
    can on_register() {
        self.init_question_functions();
    }

    can postupdate() {
        self.init_question_functions();
    }

    can touch(visitor: interact_graph_walker) -> bool {
        if visitor.utterance {
            return True;
        }
    }

    can execute(visitor: interact_graph_walker) -> dict {
        # process incoming response and set the directive, if any
        self.process_response(visitor);
        return visitor.export();
    }

    can init_question_functions() {
        # converts the question index items to functions in order to perform extraction
        question_functions:list = [];

        for (index, question_item) in (self.question_index).items() {
            question_functions.append(
                {
                    "type": "function",
                    "function": {
                        "name": index,
                        "description": f"A direct answer to '{question_item.get('question')}', described by '{question_item.get('description')}'",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "response": {
                                    "type": question_item.get('type', 'string'),
                                    "description": question_item.get('description')
                                }
                            },
                            "required": ["response"]
                        }
                    }
                }
            );
        }

        self.functions = question_functions;
    }


    can process_response(visitor: interact_graph_walker) -> str {
        # assesses utterance based on questions and state; 
        # queues the most appropriate directive(s), if applicable
        
        # check the user session for InterviewSession obj
        if( interview_session_data := visitor.frame_node.variable_get(key=self.get_type()) ) {
            # this is an active session, process incoming response

            # wrap the interview session data in the object for easier handling
            interview_session = InterviewSession(
                active_index=interview_session_data.get('active_index', ''),
                responses=interview_session_data.get('responses', {}),
                active=interview_session_data.get('active', False)
            );

            if interview_session.is_active() {

                # assess the response, look for any trace of applicable responses to question
                results = visitor.interaction_node.get_functions(action_label = self.get_type());
                # parse and update any responses
                interview_session = self.update_responses(results, interview_session);
                            
                # grab the next question index, if any
                if ( next_index := interview_session.get_next_index(self.question_index.keys()) ) {
                    
                    # add next question directive
                    if( question_item := self.question_index.get(next_index) ) {
                        task_directive = self.task_directive.format(question=question_item.get('question'));
                        visitor.interaction_node.add_directive(directive = task_directive);
                    }

                } else {
                    # we don't have any more questions
                    visitor.interaction_node.add_directive(directive = self.outtro_directive);
                    # set InterviewSession to inactive
                    interview_session.set_active(False);
                    # clear functions to prohibit future extraction
                    self.functions = [];
                }

                # update the interview session in the frame
                visitor.frame_node.variable_set(key=self.get_type(), value=interview_session.export() );
            }

        } else {
            # this is a fresh user or a new interview, initiate
            interview_session = InterviewSession();
            # grab the next question index
            next_index = interview_session.get_next_index(self.question_index.keys());
            # set the interview session
            visitor.frame_node.variable_set(key=self.get_type(), value=interview_session.export() );
            # prepare directives
            if(self.intro_directive) {
                visitor.interaction_node.add_directive(directive = self.intro_directive);
            }
            # add first question directive
            if( question_item := self.question_index.get(next_index) ) {
                task_directive = self.task_directive.format(question=question_item.get('question'));
                visitor.interaction_node.add_directive(directive = task_directive);
            }
        }

    }

    can update_responses(results:list, interview_session:InterviewSession) {
        # returns a dictionary of question indexes and associated response texts

        for item in results {
            index = item.get('name');
            response = item.get('args', {}).get('response', None);

            if index and response {
                interview_session.set_response(index=index, response=response);
            }
        }

        return interview_session;
    }

}

obj InterviewSession {
    # object which represents the interview session data
    has active_index:str = "";
    has responses:dict = {};
    has active:bool = True;

    can is_active() {
        return self.active;
    }

    can set_active(active:bool) {
        self.active = active;
    }

    can get_active_index() {
        return self.active_question_index;
    }

    can set_active_index(index:str) {
        self.active_index = index;
    }

    can get_next_index(indexes:list) {

        if( indexes ) {
            response_indexes = self.responses.keys();
            for item in indexes {
                if item not in response_indexes {
                    self.set_active_index(item);
                    return item;
                }
            }
        }

        return None;
    }

    can get_responses() {
        return self.responses;
    }

    can get_response(index:str) {
        return self.responses.get(index, None);
    }

    can set_response(index:str, response:str) {
        self.responses[index] = response;
    }

    can clear_responses() {
        self.responses = {};
    }

    can export() {
        return {
            'active_index': self.active_index,
            'responses': self.responses,
            'active': self.active
        };
    }
}
