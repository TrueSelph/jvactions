import:py copy;
import:py logging;
import:py traceback;
import:py re;
import:py from logging { Logger }
import:py from modules.email_api { EmailAPI }
import:py from agent.modules.agentlib.utils { Utils }
import:jac from agent.action.action { Action }
import:jac from agent.action.interact { interact }
import:jac from agent.memory.interaction_response { MessageType }
import:jac from agent.action.model_action { ModelAction, ModelActionResult }


node EmailAction :Action: {
    has accounts:list = [];
    has mark_as_read:bool = True;
    has actions:list = ['delete','draft','send','reply','move','forward'];
    has channel:str = "email";
    has functions:list = [
        {
            "type": "function",
            "function": {
                "name": "handle_email_action",
                "description": "Process email actions based on the content and directives. Determine the correct action for the given email.",
                "parameters": {
                    "type": "object",
                    "properties": {
                    "actions": {
                        "type": "array",
                        "items": {
                        "type": "string",
                        "enum": [
                            "delete",
                            "draft",
                            "send",
                            "reply",
                            "move",
                            "forward"
                        ]
                        },
                        "description": "List of actions to be performed on the email. leave blank if there is no action."
                    },
                    "directives": {
                        "type": "array",
                        "items": {
                        "type": "string"
                        },
                        "description": "Select the directives for processing the email. leave blank if there is no directives."
                    }
                    },
                    "required": ["actions"]
                }
            }
        }
    ];
    has max_emails:int = 1;

    has model_name:str = "";
    has history_size:int = 3;
    has max_statement_length:int = 500;
    has model_action:str = "LangChainModelAction";
    has model_op:str = "chatopenai";
    has temperature:float = 0.2;


    can pulse() {
        agent_node = self.get_agent();

        for account in self.accounts{
            # loop thru all configured email accounts and check for new emails
            sender_email = account['sender_email'];
            sender_password = account['sender_password'];
            if account.get('sender_session_id', ''){
                sender_session_id = account['sender_session_id'];
            }else{
                sender_session_id = sender_email;
            }

            new_emails = self.get_new_emails(sender_email=sender_email, sender_password=sender_password, mark_as_read=self.mark_as_read, max_emails=self.max_emails);

            if(type(new_emails) == list){
                for new_email in new_emails{
                    # format email sender
                    try{
                        new_email['from'] = re.findall(r'<(.*?)>', new_email['from'])[0];
                    }except Exception as e {
                        continue;
                    }
                    result_actions=[];

                    try{

                        prompt_messages = [{"human": "Email:\n{email}\n\nDirectives:\n{directives}"}];
                        prompt_variables = {
                            "directives": str(account['directives']),
                            "actions": self.actions,
                            "email": {
                                'from': new_email['from'],
                                'subject': new_email['subject'],
                                'body': new_email['body']
                            }
                        };


                        for function in self.functions {
                            if(function['function']['name'] == 'handle_email_action'){
                                action_function = function;
                                break;
                            }
                        }

                        result_actions = self.call_llm(prompt_messages=prompt_messages, prompt_variables=prompt_variables, functions=[action_function], is_json=False);

                    }except Exception as e {
                        self.logger.warning(f"Fail to return actions and directives from result: {e}");
                        result_actions = {"directives": [], "actions": []};
                    }

                    try{
                        if(result_actions['actions']){
                            action_list = result_actions['actions'];

                            # executing email actions
                            if('send' in action_list) {
                                attachments = [];
                                html = False;
                                try {
                                    message = self.handle_email_interact(
                                        utterance = str(result_actions['directives']),
                                        agent_id = agent_node.id,
                                        session_id = sender_session_id,
                                        verbose = False,
                                        reporting = False,
                                        channel = self.channel,
                                        data = {"label": "email", "data_type": "json", "content": {"email": new_email}}
                                    );

                                    interact_data = self.convert_to_email_data(message=message);

                                    prompt_messages = [{"system": "Using the provided information, create a JSON object representing an email. The JSON object must include the following fields: 'cc', 'body', 'subject', 'to', and 'attachments'. Leave fields blank if not applicable. Format the email body using HTML and append all attachments to the email. Information to use: Objective: {directive}, Sender Email: {email}, Additional Information: {interact_data}."}];
                                    edit_new_email = copy.deepcopy(new_email);
                                    if 'attachments' in edit_new_email{
                                        edit_new_email['attachments']= [];
                                    }

                                    prompt_variables = {
                                        "directive": str(result_actions['directives']),
                                        "email": str(edit_new_email),
                                        "interact_data": interact_data
                                    };


                                    result = self.call_llm(prompt_messages=prompt_messages, prompt_variables=prompt_variables, functions=[], is_json=True);

                                    self.send_email(sender_email=sender_email, sender_password=sender_password, recipient_email=result['to'], subject=result['subject'], body=result['body'],cc=result['cc'], attachments=result['attachments'], html=True);
                                } except Exception as e {
                                    self.logger.warning(f'Error sending email: {e}');
                                    continue;
                                }
                            }

                            if('forward' in action_list) {
                                prompt_messages = [{"system": "Your goal is to create an email using the directive below.\ndirective:{directive}\nReturn a json object containing 'forward_to:string'. leave it blank if not applicable. make sure you return a valid json object."}];
                                prompt_variables = {"directive": str(result_actions['directives'])};
                                result = self.call_llm(prompt_messages=prompt_messages, prompt_variables=prompt_variables, functions=[], is_json=True);

                                try{
                                    self.forward_email(sender_email=sender_email, sender_password=sender_password, recipient_email=result['forward_to'], mailbox='inbox', message_type='seen', email_id=new_email['id']);
                                }except Exception as e {
                                    self.logger.warning(f'Error forwarding email: {e}');
                                    continue;
                                }
                            }

                            if('draft' in action_list) {
                                prompt_messages = [{"system": "Your goal is to create an email using the directive below.\ndirective:{directive}\nReturn a json object containing 'to:string, cc:list, subject:string, body:string'. leave it blank if not applicable. make sure you return a valid json object."}];
                                prompt_variables = {"directive": str(result_actions['directives'])};

                                result = self.call_llm(prompt_messages=prompt_messages, prompt_variables=prompt_variables, functions=[], is_json=True);

                                try{
                                    attachments = [];
                                    html = False;
                                    self.create_draft(sender_email=sender_email, sender_password=sender_password, recipient_email=result['to'], subject=result['subject'], body=result['body'], cc=result['cc'], attachments=attachments, html=html);
                                }except Exception as e {
                                    self.logger.warning(f'Error creating draft: {e}');
                                    continue;
                                }
                            }

                            if('reply' in action_list) {
                                attachments = [];
                                html = False;
                                try {
                                    message = self.handle_email_interact(
                                        utterance = str(result_actions['directives']),
                                        agent_id = agent_node.id,
                                        session_id = sender_session_id,
                                        verbose = False,
                                        reporting = False,
                                        channel = self.channel,
                                        data = {"label": "email", "data_type": "json", "content": {"email": new_email}}
                                    );

                                    interact_data = self.convert_to_email_data(message=message);

                                    prompt_messages = [{"system": "Using the provided information, create a JSON object representing an email. The JSON object must include the following fields: 'cc', 'body', 'subject', 'to', and 'attachments'. Leave fields blank if not applicable. Format the email body using HTML and append all attachments to the email. Information to use: Objective: {directive}, Sender Email: {email}, Additional Information: {interact_data}."}];
                                    edit_new_email = copy.deepcopy(new_email);
                                    if 'attachments' in edit_new_email{
                                        edit_new_email['attachments']= [];
                                    }

                                    prompt_variables = {
                                        "directive": str(result_actions['directives']),
                                        "email": str(edit_new_email),
                                        "interact_data": interact_data
                                    };


                                    result = self.call_llm(prompt_messages=prompt_messages, prompt_variables=prompt_variables, functions=[], is_json=True);

                                    self.reply_to_email(sender_email=sender_email, sender_password=sender_password, recipient_email=new_email['from'], reply_to=new_email['message_id'], cc=result['cc'], subject=result['subject'], attachments=result['attachments'], body=result['body'], html=True);
                                }except Exception as e {
                                    self.logger.warning(f'Error replying to email: {e}');
                                    continue;
                                }
                            }


                            if('move' in action_list) {
                                message = (root spawn interact(
                                    utterance = "[hello]",
                                    agent_id = agent_node.id,
                                    session_id = sender_session_id,
                                    verbose = False,
                                    reporting = False,
                                    channel = self.channel
                                )).message;
                            }

                            if('delete' in action_list) {
                                try {
                                    self.delete_email(sender_email=sender_email, sender_password=sender_password, mailbox='inbox', email_id=new_email['id']);
                                }except Exception as e {
                                    self.logger.warning(f'Error deleting email: {e}');
                                    continue;
                                }
                            }
                        }else{
                            self.move_email(sender_email=sender_email, sender_password=sender_password, mailbox='inbox', email_id=new_email['id'], destination_folder='Ignored');
                        }
                    }except Exception as e {
                        self.move_email(sender_email=sender_email, sender_password=sender_password, mailbox='inbox', email_id=new_email['id'], destination_folder='Ignored');
                        self.logger.warning(f'Error processing email action: {e}');
                        continue;
                    }
                }
            }
        }
    }


    can send_email(sender_email:str, sender_password:str, recipient_email:str, subject:str, body:str, cc:list=None, bcc:list=None, attachments:list=None, html:bool=False) -> bool {
        host = self.get_host(sender_email=sender_email);
        return EmailAPI.send_email(host=host, sender_email=sender_email, sender_password=sender_password, recipient_email=recipient_email, subject=subject, body=body, cc=cc, bcc=bcc, attachments=attachments, html=html);
    }


    can create_draft(sender_email:str, sender_password:str, recipient_email:str, subject:str, body:str, cc:list=None, bcc:list=None, attachments:list=None, html:bool=False) -> bool {
        host = self.get_host(sender_email=sender_email);
        return EmailAPI.save_to_drafts(host=host, sender_email=sender_email, sender_password=sender_password, recipient_email=recipient_email, subject=subject, body=body, cc=cc, bcc=bcc, html=html, attachments=attachments);
    }


    can forward_email(sender_email:str, sender_password:str, recipient_email:str, mailbox:str="INBOX", message_type:str="UNSEEN", email_id:str="") -> bool {
        host = self.get_host(sender_email=sender_email);
        return EmailAPI.forward_email(host=host, sender_email=sender_email, sender_password=sender_password, recipient_email=recipient_email, mailbox=mailbox, message_type=message_type, email_id=email_id);
    }


    can reply_to_email(sender_email:str, sender_password:str, recipient_email:str, reply_to:str, subject:str, body:str, cc:list=None, bcc:list=None, attachments:list=None, html:bool=False) -> bool {
        host = self.get_host(sender_email=sender_email);
        return EmailAPI.reply_to_email(host=host, sender_email=sender_email, sender_password=sender_password, recipient_email=recipient_email, reply_to=reply_to, subject=subject, body=body, cc=cc, bcc=bcc, attachments=attachments, html=html);
    }


    can delete_email(sender_email:str, sender_password:str, mailbox:str="INBOX", email_id:str="") -> bool {
        host = self.get_host(sender_email=sender_email);
        return EmailAPI.delete_email(host=host, sender_email=sender_email, sender_password=sender_password, mailbox=mailbox, email_id=email_id);
    }


    can move_email(sender_email:str, sender_password:str, mailbox:str="INBOX", email_id:str="", destination_folder:str="") -> bool {
        host = self.get_host(sender_email=sender_email);
        return EmailAPI.move_email(host=host, sender_email=sender_email, sender_password=sender_password, mailbox=mailbox, email_id=email_id, destination_folder=destination_folder);
    }


    can automate_emails(sender_email:str, sender_password:str, mailbox:str="INBOX", message_type:str="ALL",
                        delete_ids:list=[], auto_delete:bool=False, filter_list:list=[], get_filter:list=[], mark_as_read:bool=False) -> dict {
        host = self.get_host(sender_email=sender_email);
        return EmailAPI.automate_emails(host=host, sender_email=sender_email, sender_password=sender_password, mailbox=mailbox, message_type=message_type,
                                        delete_ids=delete_ids, auto_delete=auto_delete, filter_list=filter_list, get_filter=get_filter, mark_as_read=mark_as_read);
    }


    can create_folder(sender_email:str, sender_password:str, folder_name:str) -> bool {
        host = self.get_host(sender_email=sender_email);
        return EmailAPI.create_folder(host=host, sender_email=sender_email, sender_password=sender_password, folder_name=folder_name);
    }


    can get_new_emails(sender_email:str, sender_password:str, mark_as_read:bool=True, max_emails:int=5) -> list {
        host = self.get_host(sender_email=sender_email);
        return EmailAPI.get_new_emails(host=host, sender_email=sender_email, sender_password=sender_password, mailbox="INBOX", message_type="UNSEEN", mark_as_read=mark_as_read, max_emails=max_emails);
    }


    can set_email_type(sender_email:str, sender_password:str, mailbox:str="INBOX", message_type:str="UNSEEN", email_id:str="") -> bool {
        host = self.get_host(sender_email=sender_email);
        return EmailAPI.set_email_type(host=host, sender_email=sender_email, sender_password=sender_password, mailbox=mailbox, message_type=message_type, email_id=email_id);
    }


    can get_host(sender_email:str) -> str {
        if('@gmail' in sender_email){
            host = 'imap.gmail.com';
        }elif('@outlook' in sender_email){
            host = 'imap.outlook.com';
        }else{
            host = "";
            self.logger.warning("Error: Host not found" + sender_email);
            disengage;
        }

        return host;
    }


    can call_llm(prompt_messages: list, prompt_variables: dict={}, functions: list=[], is_json: bool=False) -> dict {
        kwargs = {
            "op": self.model_op,
            "temperature": self.temperature
        };

        if(functions){
            kwargs['functions'] = functions;
        }

        agent_node = self.get_agent();
        extracted_info = {};

        if(model_action := agent_node.get_actions().get(action_label=self.model_action)) {

            prompt_messages  = (visitor.frame_node.get_transcript_statements(interactions=self.history_size, max_statement_length=self.max_statement_length));

            if (model_action_result := model_action.call_model(
                prompt_messages = prompt_messages,
                prompt_variables = prompt_variables,
                kwargs = kwargs
            )) {
                result = model_action_result.get_result();

                if(functions and result){
                    entities = list(functions[0]['function']['parameters']['properties'].keys());
                    function_name = functions[0]['function']['name'];

                    for item in result {
                        if (item.get("name") == function_name) {
                            for entity in entities {
                                if (entity in item.get("args")) {
                                    extracted_info[entity] = item.get("args").get(entity);
                                }
                            }
                        }
                    }
                    return extracted_info;
                }else{
                    if is_json {
                        return model_action_result.get_result();
                    }
                    return result;
                }
            }
        }
    }


    can convert_to_email_data(message: InteractionMessage) -> dict {
        email_data = {
            "body": "",
            "attachments": []
        };
        is_html = False;

        # Handle different message types
        if message.get_type() == MessageType.TEXT.value{
            email_data["body"] = message.get_content();
        }elif message.get_type() == MessageType.MEDIA.value{
            mime_type = Utils.get_mime_type(mime_type=message.mime);
            media_url = message.data.get('url');
            is_html = message.data.get('html', False);

            if mime_type["file_type"] in ["document", "image", "video"]{
                email_data["attachments"].append(media_url);
            }

            # Add caption to body if exists
            caption = message.get_content();
            if caption{
                email_data["body"] += f"\n\nCaption: {caption}";
            }

        }elif message.get_type() == MessageType.MULTI.value{
            # Iterate over multiple messages
            for message_item in message.content{
                if message_item.get_type() == MessageType.TEXT.value{
                    email_data["body"] += f"\n{message_item.get_content()}";
                }elif message_item.get_type() == MessageType.MEDIA.value {
                    mime_type = Utils.get_mime_type(mime_type=message_item.mime);
                    media_url = message_item.data.get('url');
                    is_html = message_item.data.get('html', False);
                    if mime_type["file_type"] in ["document", "image", "video"]{
                        email_data["attachments"].append(media_url);
                    }

                    # Add caption to body if exists
                    caption = message_item.get_content();
                    if caption{
                        email_data["body"] += f"\n\nCaption: {caption}";
                    }
                }
            }
        }
        # Sanitize and finalize email body
        email_data["body"] = self.sanitize_message(email_data["body"]);
        email_data["html"] = is_html;
        return email_data;
    }


    can handle_email_interact(utterance:str, agent_id:str, session_id:str, verbose:bool=False, reporting:bool=False, channel:str='email', data:dict={}) -> dict {
        # call interact
        message = (root spawn interact(
            utterance = utterance,
            agent_id = agent_id,
            session_id = session_id,
            verbose = verbose,
            reporting = reporting,
            channel = channel,
            data = data
        )).message;

        return message;
    }


    can sanitize_message(message:str) {
        # return message.replace("**", "*").replace("<br/>", "\n").replace("<b>", "*").replace("</b>", "*");
        return message;
    }
}
