import:py logging;
import:py re;
import:py from logging { Logger }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.action.interact { interact }
import:jac from jivas.agent.action.interact_graph_walker { interact_graph_walker }
import:jac from jivas.agent.core.agent { Agent }
import:jac from jivas.agent.memory.frame { Frame }
import:jac from jivas.agent.memory.memory { Memory }
import:py from modules.facebook_api { FacebookAPI }


walker facebook_interact :interact_graph_walker: {
    # called via a webhook whenever there are verification requests or inbound messages 
    # when activated, it will trigger the facebook interact action to communicate

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
        

        if( action_node:=(here.get_actions().get(action_label='FacebookAction')) ) {
            if(not action_node.enabled and not action_node.messenger_enabled) {
                Jac.get_context().status = 200;
                disengage;
            }

            if('hub.challenge' in self.params and 'hub.verify_token' in self.params) {
                challenge = action_node.verify_request(request = self.params);
                self.response = challenge;
                disengage;
            }


            # parse data if we've gotten this far..
            data = FacebookAPI.parse_inbound_message(request = self.params);
            if(not data) {
                Jac.get_context().status = 200;
                disengage;
            }

            # determine if phone number has access
            access_control_action_node = here.get_actions().get(action_label='AccessControlAction');
            if(access_control_action_node) {
                access = access_control_action_node.has_action_access(
                    session_id=data['sender_id'], 
                    action_label='FacebookAction', 
                    channel='facebook'
                );

                if not access {
                    Jac.get_context().status = 200;
                    disengage;
                }
            }
            
            # ignore loopback messages i.e. messages where sender and receiver are the 
            if(data['sender_id'] == data['page_id']) {
                Jac.get_context().status = 200;
                disengage;
            }

            # init the frame here so we can have it all set up to add the sender info from data
            # we have to force session to get frame to use the session_id we supply, so we can track facebook user by number
            frame_node = here.get_memory().get_frame(agent_id = here.id, session_id = data["sender_id"], force_session=True);
            
            if(action_node.use_pushname) {
                # grab and save the sender name in a frame variable
                frame_node.set_user_name(data['sender_name']);
            }


            # handle voicenote requests
            if(data['attachments'] and data['attachments'][0]['type'] in ['audio']) {
                self.handle_voicenote_message(
                    data = data, 
                    agent_node = here,
                    frame_node = frame_node, 
                    action_node = action_node
                );
            }

            # handle media requests
            if(data['attachments'] and data['attachments'][0]['type'] in ['document', 'image', 'video']) {
                self.handle_media_message(
                    data = data, 
                    agent_node = here,
                    frame_node = frame_node, 
                    action_node = action_node
                );
            }

            # handle chat message requests
            if(data['message_type'] == 'message' and not data['attachments']) {
                self.handle_chat_message(
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

        if('author' in data and data['author']) {
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
                utterance = data['message'], 
                agent_id = agent_node.id, 
                session_id = frame_node.session_id,
                verbose = False,
                reporting = False,
                channel = "facebook"
            )).message;

            action_node.send_message(session_id=frame_node.session_id, message=message);
        }
    }

    can handle_voicenote_message(data:dict, agent_node:Agent, frame_node:Frame, action_node:Action) {
        # This action downloads the voicenote audio transcribes it and passes it to interact walker as text to be processed
        

        data_media = data['attachments'][0]['payload']['url'];
        attachment_type = data['attachments'][0]['type'];
        
        response = None;
        transcription = None;

        # load stt action                       
        if(stt_action := agent_node.get_stt_action()) {
            transcription = stt_action.invoke(
                audio_url = data_media
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
                channel = "facebook",
                data = {"label": "facebook_voicenote", "data_type": attachment_type, "content": data_media}
            )).message;
        }
        
        
        # now we grab the response and send it
        if(message) {
            has_tts_response = False;
            parent_message_id = message.get_meta('parent_message_id');

            if(tts_action := agent_node.get_tts_action()) {
                
                # synthesize an audio for the user, cater to phoneme_message, if available
                content = message.get_meta('phoneme_content') or message.get_content();
                
                
                # perform TTS 
                audio = tts_action.invoke(text = content, as_base64=False, as_url=True);
                                                        
                if(audio and "localhost" not in audio) {
                    # sends audio via facebook message using base64 encoded string
                    action_node.send_media(session_id= frame_node.session_id, media_type='audio', media_url=audio);
                    has_tts_response = True;
                }
            }

            if(not has_tts_response) {
                # fall back on text reply if no tts response generated
                action_node.send_message(session_id=frame_node.session_id, message=message);
            }

        }
    }

    can handle_media_message(data:dict, agent_node:Agent, frame_node:Frame, action_node:Action) {
        # add document resource to data node in interaction  

        if(self.is_directed_message(data)) { 
            message = (root spawn interact(
                utterance = data['caption'], 
                agent_id = agent_node.id, 
                session_id = frame_node.session_id,
                verbose = False,
                reporting = False,
                channel = "facebook",
                data = {"label": "facebook_media", "data_type": "json", "content": data['attachments']}
            )).message;
            

            action_node.send_message(session_id=frame_node.session_id, message=message);

        }
    }
}