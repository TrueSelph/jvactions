import:py logging;
import:py from logging { Logger }
import:py from jvserve.lib.agent_interface { AgentInterface }
import:py from agent.modules.agentlib.utils { Utils }
import:jac from agent.action.action { Action }
import:jac from agent.memory.frame { Frame }
import:jac from agent.memory.memory { Memory }
import:jac from agent.memory.interaction_response { MessageType }
import:py from .modules.ultramsg_api { UltramsgAPI }

node UltramsgAction :Action: {
    # houses configurations per agent for whatsapp api communications provided by ultramsg api

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has enabled:bool = true;
    has base_url:str = "";
    has api_key:str = "";
    has api_url:str = "";
    has instance_id:str = ""; # the ultramsg instance ID
    has phone_number:str = ""; # the whatsapp phone number
    has webhook_url:str = "";
    has webhook_properties:dict = {"send_delay": 3, "webhook_message_received": "True", "webhook_message_create": "False", "webhook_message_ack": "True", "webhook_message_download_media": "True"};
    has chunk_length:int = 1024;
    # when set, the wa push name value is used as the user name
    has use_pushname:bool = True;
    has ignore_newsletters:bool = True;


    can on_register {
        if(self.enabled) {
            self.enabled = self.register_ultramsg_webhook();
        }
    }

    can on_enable {
        self.enabled = self.register_ultramsg_webhook();
    }

    can register_ultramsg_webhook() {
        # setup procedure for webhook registration on ultramsg api

        success = True;

        agent_id = self.get_agent().id;
        module_root = self.get_module_root();
        # generate webhook key
        webhook_key = AgentInterface.encrypt_webhook_key(agent_id=agent_id, module_root=module_root, walker="ultramsg_interact");

        if(self.base_url and webhook_key) {
            # complete the full webhook url
            self.webhook_url = f'{self.base_url}/webhook/{webhook_key}';
            self.logger.debug(f'ultramsg webhook url: {self.webhook_url}');

            result = UltramsgAPI.update_instance_settings(
                webhook_url=self.webhook_url,
                send_delay=self.webhook_properties["send_delay"],
                webhook_message_received=self.webhook_properties["webhook_message_received"],
                webhook_message_create=self.webhook_properties["webhook_message_create"],
                webhook_message_ack=self.webhook_properties["webhook_message_ack"],
                webhook_message_download_media=self.webhook_properties["webhook_message_download_media"],
                api_url=self.api_url,
                api_key=self.api_key
            );

            if('error' in result) {
                success = False;
            }

        } else {
            success = False;
            self.logger.error('unable to generate webhook url for Ultramsg, missing required parameters');
        }

        return success;
    }

    can sanitize_message(message:str) {
        return message.replace("**", "*").replace("<br/>", "\n").replace("<b>", "*").replace("</b>", "*");
    }

    can send_message(session_id:str, message:InteractionMessage, parent_message_id:str = "") {
        # processes an agent response payload format and sends an ultramsg message to a specified session_id via the action

        if(message and session_id) {
            if(not parent_message_id){
                parent_message_id = message.get_meta('parent_message_id');
            }

            if (message.get_type() == MessageType.SILENCE.value) {}
            elif(message.get_type() == MessageType.TEXT.value) {
                content = self.sanitize_message(message = message.get_content());
                outgoing = Utils.chunk_long_message(message=content, max_length = self.chunk_length, chunk_length = self.chunk_length);

                for chunk in outgoing {
                    UltramsgAPI.send_text_message(phone_number=session_id, message=chunk, api_url=self.api_url, api_key=self.api_key, msg_id=parent_message_id);
                }
            } elif(message.get_type() == MessageType.MEDIA.value) {
                mime_type = Utils.get_mime_type(mime_type=message.mime);
                if(mime_type['file_type'] == "document") {
                    content = self.sanitize_message(message = message.get_content());
                    UltramsgAPI.send_document(phone_number= session_id, media_url=message.data.get('url'), api_url=self.api_url, api_key=self.api_key, file_name=message.data.get('file_name'), caption = content);
                } elif(mime_type['file_type'] == "image") {
                    content = self.sanitize_message(message = message.get_content());
                    UltramsgAPI.send_image(phone_number=session_id, media_url=message.data.get('url'), api_url=self.api_url, api_key=self.api_key, caption = content);
                } elif(mime_type['file_type'] == "video") {
                    content = self.sanitize_message(message = message.get_content());
                    UltramsgAPI.send_video(phone_number=session_id, media_url=message.data.get('url'), api_url=self.api_url, api_key=self.api_key, caption = content);
                }
            } elif(message.get_type() == MessageType.MULTI.value) {
                for message_item in message.get_content_items() {
                    if(message_item.get_type() == MessageType.TEXT.value) {
                        content = self.sanitize_message(message = message_item.get_content());
                        outgoing = Utils.chunk_long_message(message=content, max_length = self.chunk_length, chunk_length = self.chunk_length);

                        for chunk in outgoing {
                            UltramsgAPI.send_text_message(phone_number=session_id, message=chunk, api_url=self.api_url, api_key=self.api_key, msg_id=parent_message_id);
                        }
                    } elif(message_item.get_type() == MessageType.MEDIA.value) {
                        mime_type = Utils.get_mime_type(mime_type=message_item.mime);
                        content = self.sanitize_message(message = message_item.get_content());
                        if(mime_type['file_type'] == "document") {
                            UltramsgAPI.send_document(phone_number= session_id, media_url=message_item.data.get('url'), api_url=self.api_url, api_key=self.api_key, file_name=message.data.get('file_name'), caption = content);
                        } elif(mime_type['file_type'] == "image") {
                            UltramsgAPI.send_image(phone_number=session_id, media_url= message_item.data.get('url'), api_url=self.api_url, api_key=self.api_key, caption = content);
                        } elif(mime_type['file_type'] == "video") {
                            UltramsgAPI.send_video(phone_number=session_id, media_url= message_item.data.get('url'), api_url=self.api_url, api_key=self.api_key, caption = content);
                        }
                    }
                }
            }
        }
    }

    can broadcast_message(message:InteractionMessage, ignore_list:list = []) {
        # processes an agent response payload format and sends an ultramsg message to all session_ids via the action

        if(message) {
            agent_node = self.get_agent();

            if(frames := agent_node.get_memory().get_frames() ) {
                # get all frames then proceed to broadcast
                for frame_node in frames {
                    if(frame_node.session_id not in ignore_list) {
                        interaction_node = frame_node.get_interactions()[0];
                        if(interaction_node.channel in ['whatsapp']) {
                            self.send_message(session_id = frame_node.session_id, message=message);
                        }
                    }
                }
            }
        }

    }

}
