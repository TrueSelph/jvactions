import:py random;
import:py uuid;
import:py logging;
import:py traceback;
import:py from logging { Logger }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:jac from jivas.agent.memory.interaction_response { TextInteractionMessage, MediaInteractionMessage, MultiInteractionMessage }
import:jac from jivas.agent.action.interact_action { InteractAction }
import:jac from jivas.agent.action.interact_graph_walker { interact_graph_walker }
import:jac from actions.jivas.langchain_model_action.langchain_model_action { LangChainModelAction }


node HandoffInteractAction :InteractAction: {
    has directive: str = "Your goal is to let the user know that you are unable to answer the request and will get back to them later.";
    has select_handoff_prompt:str = """
Select the most relevant query from the worksheet based on the user_message.  
- If a relevant query exists, return a JSON object containing 'id'.  
- If no relevant query is found, return an empty object.  

worksheet:  
{worksheet}  

user_message:  
{user_message}  

Return only a JSON object containing 'id'.  

""";
    has ask_confirmation_prompt: str = """
Present the query answer and ask the user to confirm its accuracy. Use markdown to make response readable.

query:  
{query}  

query_answer:  
{query_answer}  

Ask a single confirmation question.  

""";
    has request_correct_info_directive: str = "Your goal is ask the user to provide the correct information.";
    has query_reply_prompt:str = """
Acknowledge the user's patience, summarize the query, and provide the final answer in a single, polite, and concise paragraph.  

user_name: {user_name}  

query: {query}  

query_answer: {query_answer}  

""";
    has extract_answer_prompt:str = """
Review the query and its history, then compose a comprehensive paragraph of the answer, including additional context.

- Return a JSON object with a single key, 'answer'.
- Ensure that all relevant content is captured, preserving all related context.
- If no relevant details are discovered, set 'answer' to an empty string.

Query: {query}
""";

    has history: bool = True;
    has history_size: int = 3;
    has max_statement_length: int = 1000;
    has model_op: str = "chatopenai";
    has model_name: str = "gpt-4o";
    has model_action: str = "LangChainModelAction";
    has model_temperature: float = 0.2;
    has model_max_tokens:int = 4000;
    

    has experts_numbers: list = [];
    has update_store: bool = True;
    has google_sheet_enabled: bool = True;
    has worksheet_title:str = "Sheet1";
    has vector_store_action:str = "TypesenseVectorStoreAction";
    

    has confirm_function: list = [
        {
            "type": "function",
            "function": {
                "name": "status_of_confirmation",
                "description": "Validate if the user confirms the provided information or requests corrections.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "is_confirmed": {
                            "type": "string",
                            "enum": ["true", "false", "correct_info_was_provided"],
                            "description": "Indicates whether the user confirms the provided information is correct. Set to 'true' if confirmed, or 'false' if not. If user give the updated information, return 'correct_info_was_provided'. If user confirm the updated information, return 'true'."
                        },
                        "closing_response": {
                            "description": "Thank the user for providing the information once it has been confirmed.",
                            "type": "string"
                        }
                    },
                    "required": ["is_confirmed"]
                }
            }
        }
    ];

    has handoff_functions: list = [
        {
            "type": "function",
            "function": {
                "name": "evaluate_agent_response",
                "description": "Evaluates whether the agent has provided the correct answer to the user's most recent query and offers a detailed summary of that query. This function is automatically triggered after every agent response.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query_summary": {
                            "type": "string",
                            "description": "A detailed and concise summary of the user's query. eg (an query about the process or implications if someone is missing a few contributions to reach the 750 target for pension in Guyana.)"
                        },
                        "response_evaluation": {
                            "type": "string",
                            "enum": ["correct", "incorrect", "uncertain", "dont_have_information", "unable_to_answer_due_to_restrictions"],
                            "description": "An evaluation of whether the agent's response adequately addressed the user's query."
                        }
                    },
                    "required": ["query_summary", "response_evaluation"]
                }
            }
        }

    ];



    can touch(visitor: interact_graph_walker) -> bool {
        if (visitor.utterance) {
            return True;
        }
        return False;
    }


    can execute(visitor: interact_graph_walker) -> dict {

        if(visitor.session_id in self.experts_numbers) {
            self.handle_expert_response(visitor=visitor);
        }else{
            self.handle_user_response(visitor=visitor);
        }

        return visitor.export();
    }

    can get_query(visitor: interact_graph_walker) -> dict {
        queries = [];

        # get and update sheet 
        if( self.google_sheet_enabled ) {
            google_sheet_action = self.get_agent().get_actions().get(action_label = "GoogleSheetAction");
            worksheet = google_sheet_action.open_worksheet(worksheet_title=self.worksheet_title);
            # get all the pending queries
            for i in range(len(worksheet)){
                if(worksheet[i]['status'] == 'pending'){
                    worksheet[i]['row'] = i;
                    queries.append(worksheet[i]);
                }
            }
        }elif( vector_store_action := self.get_agent().get_actions().get(action_label = self.vector_store_action) ) {
            if(documents := vector_store_action.list_documents(page = 1, per_page = 10)) {
                # iterate through result set and return top-ranked texts
                documents = documents.get("documents");
                for doc in documents {
                    metadata = doc.get("metadata");
                    knode_index = metadata.get("knode_index");
                    if(knode_index == "handoff_query") {
                        queries.append(doc);
                    }
                }
            }
        }
        formatted_queries = [];
        for query in queries {
            if 'query' in query{
                q = query['query'];
                session_id = query['session_id'];
            }else{
                q = query['metadata']['query'];
                session_id = query['metadata']['created_by'];
            }

            formatted_queries.append({
                "id": query["id"],
                "query": q,
                "session_id": session_id
            });
        }

        return {
            "queries": queries,
            "formatted_queries": formatted_queries
        };
    }


    can update_query(visitor: interact_graph_walker, query:str, session_id:str, query_answer:str, query_status:str) -> dict {
        if(query_status == "resolved") {
            query_result = self.get_query(visitor=visitor);
            last_query_id = visitor.frame_node.variable_get(key="last_query_id");
            current_query = {};

            for q in query_result['queries'] {
                if(q['id'] == last_query_id) {
                    current_query = q;
                }
            }
            query_id = current_query['id'];
        }else{
            query_id = str(uuid.uuid4());
        }
        
        if(self.google_sheet_enabled) {
            # update sheet 
            google_sheet_action = visitor.agent_node.get_actions().get(action_label='GoogleSheetAction');
            if(query_status == "resolved" and query_answer) {
                row = current_query['row'] + 2;
                cell = f"A{row}:F{row}";
                value = [query_id, str(session_id), str(current_query['query']), str(query_answer), str(query_status), str(visitor.session_id) ];
                
                google_sheet_action.update_cell(cell=cell, value=[value]);   
            }else{
                worksheet = google_sheet_action.open_worksheet(worksheet_title=self.worksheet_title);
                row = len(worksheet) + 2;
                cell = f"A{row}:E{row}";
                value = [query_id, str(visitor.session_id), str(query), "", str(query_status)];
                
                google_sheet_action.update_cell(cell=cell, value=[value]);
            }
        }

        if(self.update_store or not self.google_sheet_enabled){
            typesense_vector_store_action = visitor.agent_node.get_actions().get(action_label=self.vector_store_action);
            if(query_status == "resolved" and query_answer) {
                if(type(query) == str){
                    query = [query];
                }
                metadatas = [{"knode_index": "handoff_query_resolved", "created_by": str(visitor.session_id), "anchors": query}];
                texts = "## Example Questions:\n- " + str(query[0]) + "\n\n## Answer:\n" + query_answer;
                typesense_vector_store_action.add_texts(texts=[str(texts)],metadatas=metadatas, ids=[query_id]);
            }else{
                metadatas = [{"knode_index": "handoff_query", "created_by": str(visitor.session_id), "query": [str(query)]}];
                typesense_vector_store_action.add_texts(texts=[""],metadatas=metadatas, ids=[query_id]);
            }            
        }
    }


    can select_query(visitor: interact_graph_walker) -> dict {

        whatsapp_chat = visitor.interaction_node.get_data_item(label = "whatsapp_chat");
        replied_message = "";
        if(whatsapp_chat){
            replied_message = whatsapp_chat.content.get('parent_message').get('body');
        }


        # get and update sheet or store
        query_result = self.get_query(visitor=visitor);
        filtered_worksheet = query_result.get("formatted_queries");

        # selecting query id
        result = None;
        if(model_action := self.get_agent().get_actions().get(action_label=self.model_action)) {
            
            # get the selected query and generate response 
            prompt_messages = (visitor.frame_node.get_transcript_statements(interactions=self.history_size,max_statement_length=self.max_statement_length));
            prompt_messages = prompt_messages[:-1];
            if(replied_message){
                prompt_messages.append({"human": f"Selected query: {replied_message}"});
            }
            prompt_messages.append({"system": self.select_handoff_prompt});
            prompt_variables = {
                "worksheet": filtered_worksheet,
                "user_message": visitor.utterance
            };
            if( model_action_result := model_action.call_model(
                prompt_messages = prompt_messages,
                prompt_variables = prompt_variables,
                interaction_node = visitor.interaction_node,
                kwargs = {
                    "model_name": self.model_name,
                    "model_temperature": self.model_temperature,
                    "model_max_tokens": self.model_max_tokens
                },
                logging = False
            )) {
                result = model_action_result.get_json_result();
            }
        }


        query="";
        if(result) {
            query_id = result.get("id");
            visitor.frame_node.variable_set(key="last_query_id", value=query_id);

        }else{
            query_id = visitor.frame_node.variable_get(key="last_query_id");
        }

        for q in filtered_worksheet{
            if(q['id']==query_id){
                query = q;
            }
        }
        return query;
    }


    can extract_answer(visitor: interact_graph_walker, query:str) -> str {
        # extract query answer 
        result = {};
        if(model_action := self.get_agent().get_actions().get(action_label=self.model_action)) {
            
            prompt_messages  = (visitor.frame_node.get_transcript_statements(interactions=self.history_size, max_statement_length=self.max_statement_length));
            prompt_messages = prompt_messages[:-1];
            prompt_messages.append({"system": self.extract_answer_prompt});

            prompt_variables = {
                "query": query
            };

            if( model_action_result := model_action.call_model(
                prompt_messages = prompt_messages,
                prompt_variables = prompt_variables,
                interaction_node = visitor.interaction_node,
                kwargs = {
                    "model_name": self.model_name,
                    "model_temperature": self.model_temperature,
                    "model_max_tokens": self.model_max_tokens
                },
                logging = False
            )) {
                result = model_action_result.get_json_result();
                result.get("answer");
            }
        }
        return result;
    }


    can handle_expert_response(visitor: interact_graph_walker) -> bool {
        
        query = self.select_query(visitor=visitor);
        if(query){
            query_answer = self.extract_answer(visitor=visitor, query=query['query']);
            if(query_answer) {
                data = {
                    "query": query['query'],
                    "query_answer": query_answer["answer"]
                };
                confirmation_status = self.confirm_info(visitor=visitor, data=data);

                if(confirmation_status){

                    # get frame_node and interaction 
                    session_id = str(query['session_id']);
                    agent_id = str(visitor.agent_node.id);
                    frame_node = visitor.agent_node.get_memory().get_frame(agent_id=agent_id, session_id=session_id);
                    interaction_node = frame_node.get_last_interaction();
                    
                    # update query  
                    self.update_query(visitor=visitor, query=query['query'], session_id=session_id, query_answer=query_answer["answer"], query_status="resolved");
                    
                    # sending message 
                    result = None;
                    if(model_action := self.get_agent().get_actions().get(action_label=self.model_action)) {
                        user = frame_node.get_user_name();
                        prompt_messages = [{"system": self.query_reply_prompt}];
                        prompt_variables = {
                            "query": str(query['query']),
                            "query_answer": query_answer,
                            "user_name": user
                        };
                        if( model_action_result := model_action.call_model(
                            prompt_messages = prompt_messages,
                            prompt_variables = prompt_variables,
                            interaction_node = visitor.interaction_node,
                            kwargs = {
                                "model_name": self.model_name,
                                "model_temperature": self.model_temperature,
                                "model_max_tokens": self.model_max_tokens
                            },
                            logging = False
                        )) {

                            # set the interaction message+
                            result = model_action_result.get_result();
                            if(interaction_node.channel in ['whatsapp'] and result) {
                                if(whatsapp_action_node:=visitor.agent_node.get_actions().get(action_label='UltramsgAction')) {
                                    whatsapp_action_node.send_message(session_id=session_id, message=TextInteractionMessage(content=result));
                                }elif(whatsapp_action_node:=visitor.agent_node.get_actions().get(action_label='WppconnectAction')) {
                                    whatsapp_action_node.send_message(session_id=session_id, message=TextInteractionMessage(content=result));
                                }
                                frame_node.add_unprompted_interaction(channel = "whatsapp", message = result);
                            }
                        }
                    }


                    # reset action
                    self.reset_action(visitor);
                }
            }
        }
    }


    can confirm_info(visitor: interact_graph_walker, data:dict) -> bool {
        entities = list(self.confirm_function[0]['function']['parameters']['properties'].keys());
        agent_status = visitor.frame_node.variable_get(key=f"{self.label}_confirmation");
        confirmation_status = False;

        if (not agent_status) {
            # ask first confirmaiton question
            self.ask_confirmation_question(visitor, data);
        } else {

            # check confirmation
            function_result = {};
            if(model_action := self.get_agent().get_actions().get(action_label=self.model_action)) {
                entities = list(self.confirm_function[0]['function']['parameters']['properties'].keys());
                prompt_messages  = (visitor.frame_node.get_transcript_statements(interactions=self.history_size, max_statement_length=self.max_statement_length));
                prompt_messages = prompt_messages[:-1];
                
                if (model_action_result := model_action.call_model(
                    prompt_messages = prompt_messages,
                    prompt_variables = {},
                    kwargs = {
                        "functions": self.confirm_function,
                        "model_name": self.model_name,
                        "model_temperature": self.model_temperature,
                        "model_max_tokens": self.model_max_tokens
                    },
                    interaction_node = visitor.interaction_node,
                    logging = False
                )) {

                    if(tools := model_action_result.get_result()) {
                        if tools {
                            function_result = tools[-1]["args"];
                            confirmation_status = function_result["is_confirmed"];
                            # set closing message 
                            if(function_result.get("closing_response")){
                                visitor.interaction_node.set_message( TextInteractionMessage(content = function_result.get("closing_response")) );
                            }
                        }
                    }
                }
            }


            if(function_result) {


                if(confirmation_status == "correct_info_was_provided"){
                    # correct info was provided and ask for confirmation
                    self.ask_confirmation_question(visitor, data);
                    confirmation_status = False;
                }elif (confirmation_status in ["true", "True", True]) {
                    # confirmation is correct
                    confirmation_status = True;
                } else {
                    # confirmation is incorrect and ask for correct info
                    visitor.frame_node.variable_set(key=f"{self.label}_confirmation",value="request_correct_info_directive");

                    prompt_messages = (visitor.frame_node.get_transcript_statements(interactions=self.history_size,max_statement_length=self.max_statement_length));
                    prompt_messages = prompt_messages[:-1];
                    prompt_messages.append({"system": self.request_correct_info_directive});
                    prompt_variables = {};

                    if( model_action_result := model_action.call_model(
                        prompt_messages = prompt_messages,
                        prompt_variables = prompt_variables,
                        interaction_node = visitor.interaction_node,
                        kwargs = {
                            "model_name": self.model_name,
                            "model_temperature": self.model_temperature,
                            "model_max_tokens": self.model_max_tokens
                        },
                        logging = False
                    )) {
                        result = model_action_result.get_result();
                        if(result) {
                            visitor.interaction_node.set_message( TextInteractionMessage(content=result));
                        }
                    }
                    confirmation_status = False;
                }
            }else{
                self.ask_confirmation_question(visitor, data);
            }
        }

        return confirmation_status;
    }


    can ask_confirmation_question(visitor: interact_graph_walker, data:dict) -> bool {

        # ask first confirmaiton question
        visitor.frame_node.variable_set(key=f"{self.label}_confirmation",value="ask_confirmation_prompt");

        # selecting id
        result = None;
        if(model_action := self.get_agent().get_actions().get(action_label=self.model_action)) {
            
            # generate response to ask confirmation question
            prompt_messages  = (visitor.frame_node.get_transcript_statements(interactions=self.history_size, max_statement_length=self.max_statement_length));
            prompt_messages.append({"system": self.ask_confirmation_prompt});

            prompt_variables = {
                "query": data['query'],
                "query_answer": data['query_answer']
            };

            if( model_action_result := model_action.call_model(
                prompt_messages = prompt_messages,
                prompt_variables = prompt_variables,
                interaction_node = visitor.interaction_node,
                kwargs = {
                    "model_name": self.model_name,
                    "model_temperature": self.model_temperature,
                    "model_max_tokens": self.model_max_tokens
                },
                logging = False
            )) {

                # set the interaction message+
                result = model_action_result.get_result();

                if(result) {
                    visitor.interaction_node.set_message( TextInteractionMessage(content = result) );                    
                }
            }
        }

    }


    can reset_action(visitor: interact_graph_walker) -> bool {

        if(not self.update_store){
            last_query_id = visitor.frame_node.variable_get(key="last_query_id");
            typesense_vector_store_action = visitor.agent_node.get_actions().get(action_label=self.vector_store_action);
            typesense_vector_store_action.delete_document(last_query_id);
        }

        visitor.frame_node.variable_set(key=f"{self.label}_confirmation",value="");
        visitor.frame_node.variable_set(key="last_query_id", value="");

        return True;
    }


    can handle_user_response(visitor: interact_graph_walker) -> dict {
        extracted_info = {};

        if(model_action := self.get_agent().get_actions().get(action_label=self.model_action)) {
            entities = list(self.handoff_functions[0]['function']['parameters']['properties'].keys());

            prompt_messages  = (visitor.frame_node.get_transcript_statements(interactions=self.history_size, max_statement_length=self.max_statement_length));
            
            if (model_action_result := model_action.call_model(
                prompt_messages = prompt_messages,
                prompt_variables = {},
                kwargs = {
                    "functions": self.handoff_functions,
                    "model_name": self.model_name,
                    "model_temperature": self.model_temperature,
                    "model_max_tokens": self.model_max_tokens
                },
                interaction_node = visitor.interaction_node,
                logging = False
            )) {

                if(tools := model_action_result.get_result()) {
                    if tools {
                        extracted_info = tools[-1]['args'];
                    }
                }
            }
        }



        if (extracted_info.get("response_evaluation") not in ["correct", ""] and extracted_info.get("query_summary")) {

            # process prompt 
            result = None;
            if(model_action := self.get_agent().get_actions().get(action_label=self.model_action)) {
                
                prompt_messages = (visitor.frame_node.get_transcript_statements(interactions=self.history_size,max_statement_length=self.max_statement_length));
                prompt_messages = prompt_messages[:-1];
                prompt_messages.append({"system": self.directive});
                prompt_variables = {};

                if( model_action_result := model_action.call_model(
                    prompt_messages = prompt_messages,
                    prompt_variables = prompt_variables,
                    interaction_node = visitor.interaction_node,
                    kwargs = {
                        "model_name": self.model_name,
                        "model_temperature": self.model_temperature,
                        "model_max_tokens": self.model_max_tokens
                    },
                    logging = False
                )) {
                    result = model_action_result.get_result();
                    if(result) {
                        visitor.interaction_node.set_message( TextInteractionMessage(content=result));
                    }
                }
            }


            # get and update sheet or store
            self.update_query(visitor=visitor, query=extracted_info.get("query_summary"), session_id=visitor.session_id, query_answer="", query_status="pending");

            # get frame_node and interaction 
            session_id = str(random.choice(self.experts_numbers));
            agent_id = str(visitor.agent_node.id);
            frame_node = visitor.agent_node.get_memory().get_frame(agent_id=agent_id, session_id=session_id);
            
            # sending message 
            if(ultramsg_action_node:=visitor.agent_node.get_actions().get(action_label='UltramsgAction')) {
                ultramsg_action_node.send_message(session_id=session_id, message=TextInteractionMessage(content=extracted_info.get("query_summary")));
                frame_node.add_unprompted_interaction(channel = "whatsapp", message = extracted_info.get("query_summary"));
            }
        }
    }

    
    can healthcheck() -> bool {
        try {
            if(
                self.directive and
                self.select_handoff_prompt and
                self.ask_confirmation_prompt and
                self.request_correct_info_directive and
                self.query_reply_prompt and
                self.extract_answer_prompt and
                self.model_op and 
                self.model_name and 
                self.model_action and 
                self.model_temperature and 
                self.model_max_tokens and 
                self.experts_numbers and
                self.worksheet_title and
                self.vector_store_action and
                self.confirm_function and
                self.handoff_functions and 
                self.max_statement_length > 0
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
