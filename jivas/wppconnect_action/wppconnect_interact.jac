import:py logging;
import:py os;
import:py mimetypes;
import:py from logging { Logger }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.action.interact { interact }
import:jac from jivas.agent.action.interact_graph_walker { interact_graph_walker }
import:jac from jivas.agent.core.agent { Agent }
import:jac from jivas.agent.memory.frame { Frame }
import:jac from jivas.agent.memory.memory { Memory }
import:py from .modules.wppconnect_api { WppconnectAPI }

walker wppconnect_interact :interact_graph_walker: {
    # called via a webhook whenever there are verification requests or inbound messages 
    # when activated, it will trigger the whatsapp interact action to communicate

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has headers:dict = {};
    # main param for incoming webhook data
    has params:dict = {};
    # main param for outgoing webhook data
    has response:dict = {};

    can on_agent with Agent entry {
        
        # handle request here to ensure it's worth the walk
        if(not self.params) {
            Jac.get_context().status = 200;
            disengage;
        }

        # parse data if we've gotten this far..
        data = WppconnectAPI.parse_inbound_message(request = self.params);
        if(not data) {
            Jac.get_context().status = 200;
            disengage;
        }

        # determine if phone number has access
        if(access_control_action_node := here.get_actions().get(action_label='AccessControlAction')) {

            access = access_control_action_node.has_action_access(
                session_id=data['sender_number'], 
                action_label='WppconnectAction', 
                channel='whatsapp'
            );

            if not access {
                Jac.get_context().status = 200;
                disengage;
            }
        }

        # ignore loopback messages i.e. messages where sender and receiver are the same
        if(data['sender_number'] == data['agent_number']) {
            disengage;
        }

        if( action_node := (here.get_actions().get(action_label='WppconnectAction')) ) {
            if(not action_node.enabled) {
                Jac.get_context().status = 200;
                disengage;
            }

            if(action_node.ignore_newsletters and "@newsletter" in data["sender_number"]) {
                Jac.get_context().status = 200;
                disengage;
            }

            # let's handle onack types here...
            if(data['fromMe']) {
                # if this is a human sending a message via AI's whatsapp, handle it differently here
                if((data['event_type'] == "onack") and data["author"]) {
                    frame_node = here.get_memory().get_frame(agent_id = here.id, session_id = data["agent_number"], force_session=True);
                    frame_node.add_unprompted_interaction(agent_id=here.id, message = data["body"], channel = "whatsapp");
                }
                disengage;
            }

            # init the frame here so we can have it all set up to add the sender info from data
            # we have to force session to get frame to use the session_id we supply, so we can track whatsapp user by number
            frame_node = here.get_memory().get_frame(agent_id = here.id, session_id = data["sender_number"], force_session=True);
            
            if(action_node.use_pushname) {
                # grab and save the sender name in a frame variable
                frame_node.set_user_name(data['sender_name']);
            }

            # handle chat message requests
            if(data['message_type'] == 'chat') {
                self.handle_chat_message(
                    data = data, 
                    agent_node = here,
                    frame_node = frame_node, 
                    action_node = action_node
                );
            }

            # handle voicenote requests
            if(data['message_type'] in ['ptt']) {
                self.handle_voicenote_message(
                    data = data, 
                    agent_node = here,
                    frame_node = frame_node, 
                    action_node = action_node
                );
            }

            # handle voicenote requests
            if(data['message_type'] in ['audio', 'document', 'image', 'video']) {
                self.handle_media_message(
                    data = data, 
                    agent_node = here,
                    frame_node = frame_node, 
                    action_node = action_node
                );
            }
        }
    }

    can is_directed_message(data:dict) -> bool {
        # interprets the data to determine whether it's a direct group reply or valid direct chat with content

        if(data['author']) {
            # this means we are in a group..only respond if the message starts with @[agent name]
            callout = ( ("@"+data['agent_number']).replace("@c.us", "") ).lower();
            callout_index = ((data['body']).lower()).find(callout);
            if( callout_index == -1 ) {
                # then we ignore unless they are directly calling us out in the group...
                return False;
            } else {
                # remove the callout from the message...
                data['body'] = (data['body']).replace(callout, "");
                return True;
            }
        }

        return True;
    }

    can handle_chat_message(data:dict, agent_node:Agent, frame_node:Frame, action_node:Action) {
        if(self.is_directed_message(data)) {
            # only respond if we have a message and if we are messaged with @ in groups

            message = (root spawn interact(
                utterance = data['body'], 
                agent_id = agent_node.id, 
                session_id = frame_node.session_id,
                verbose = False,
                reporting = False,
                channel = "whatsapp",
                data = {"label": "whatsapp_chat", "data_type": "dict", "content": data}
            )).message;

            # handle reply
            parent_message_id = "";
            if(data.get("parent_message")){
                parent_message_id = data.get("message_id");
            }

            action_node.send_message(session_id=frame_node.session_id, message=message, is_group=data["isGroup"], parent_message_id=parent_message_id);
        }
    }

    can handle_voicenote_message(data:dict, agent_node:Agent, frame_node:Frame, action_node:Action) {
        # This action downloads the voicenote audio transcribes it and passes it to interact walker as text to be processed
        
        if(not data['author']) { # sidestep voicenotes in group chats
            
            message = None;
            transcription = None;
            
            # load stt action                       
            if(stt_action := agent_node.get_stt_action()) {
                transcription = stt_action.invoke_base64(
                    audio_base64 = data['media']
                );
            } else {
                self.logger.error('unable to load speech-to-text action');
            }

            if(transcription) {
                message = (root spawn interact(
                    utterance = transcription, 
                    agent_id = agent_node.id, 
                    session_id = frame_node.session_id,
                    verbose = False,
                    reporting = False,
                    tts = True,
                    channel = "whatsapp",
                    data = {"label": "whatsapp_voicenote", "data_type": data['message_type'], "content": data['media']}
                )).message;
            }
            
            # now we grab the response and send it
            if(message) {
                
                # dereference response for convenience
                has_tts_response = False;
                parent_message_id = message.get_meta('parent_message_id');

                if(tts_action := agent_node.get_tts_action()) {
                    
                    # synthesize an audio for the user, cater to phoneme_message, if available
                    content = message.get_meta('phoneme_content') or message.get_content();
                    
                    # perform TTS 
                    audio = tts_action.invoke(text=content, as_base64=True);
                                                            
                    if(audio) {
                        # sends audio via wppconnect message using url
                        response = WppconnectAPI.send_audio_base64(phone_number=frame_node.session_id, session_id=action_node.instance_id, base64_encoded = audio, api_url = action_node.api_url, api_key = action_node.api_key, is_group=data["isGroup"]);
                        has_tts_response = True;
                    }
                }

                if(not has_tts_response) {
                    # fall back on text reply if no tts response generated
                    action_node.send_message(session_id=frame_node.session_id, message=message, is_group=data["isGroup"]);
                }

            }
        }  
    }

    can handle_media_message(data:dict, agent_node:Agent, frame_node:Frame, action_node:Action) {
        # add document resource to data node in interaction  
        if(self.is_directed_message(data)) { 

            encoded_data = data['media'];
            name = data["message_id"].split(".")[1];
            extension = mimetypes.guess_extension(data['mime_type']);
            file_path = f".files/{name}{extension}";
            url_path = f"{os.environ.get('JIVAS_FILES_URL','http://localhost:9000/files')}/{name}{extension}";
            oo=WppconnectAPI.get_media(encoded_data, file_path);
            data['media'] = url_path;


            message = (root spawn interact(
                utterance = data['caption'] if data['caption'] else f'sent {data['message_type']} file in the chat', 
                agent_id = agent_node.id, 
                session_id = frame_node.session_id,
                verbose = False,
                reporting = False,
                channel = "whatsapp",
                data = {"label": "whatsapp_media", "data_type": "dict", "content": data}
            )).message;

            # handle reply
            parent_message_id = "";
            if(data.get("parent_message")){
                parent_message_id = data.get("message_id");
            }

            action_node.send_message(session_id=frame_node.session_id, message=message, is_group=data["isGroup"], parent_message_id=parent_message_id);
        }
    }
}
