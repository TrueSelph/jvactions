import:py os;
import:py logging;
import:py from logging { Logger }
import:py from jvserve.lib.agent_interface { AgentInterface }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.memory.frame { Frame }
import:jac from jivas.agent.memory.memory { Memory }
import:jac from jivas.agent.memory.interaction_response { MessageType }
import:py from modules.facebook_api { FacebookAPI }

node FacebookAction :Action: {
    # houses configurations per agent for facebook api communications provided by Facebook api

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has enabled:bool = true;
    has base_url:str = "";
    has webhook_url:str = "";
    has chunk_length:int = 1024;
    has app_id:str = '1859038549999';
    has app_secret:str = 'b8f680b8217c805c912bc9999';
    # when set, the wa push name value is used as the user name
    has use_pushname:bool = True;
    has messenger_enabled:bool = False;

    has pages:dict = {
        "main_page":{
            "page_id": "49943648659999",
            "page_access_token": "EAAaaySQTk4IBO9z3i49999"
        }
    };
    has api_url:str = 'https://graph.facebook.com/v21.0/';
    has subscribed_fields: str = "feed, messages";
    has webhook_verify_token:str = '123';


    can on_register {

        if(self.enabled) {
            # setup procedure for webhook registration on Facebook api
            agent_id = self.get_agent().id; 
            module_root = self.get_module_root();

            # generate webhook key
            webhook_key = AgentInterface.encrypt_webhook_key(agent_id=agent_id, module_root=module_root, walker="facebook_interact");

            if(self.base_url and webhook_key) {
                # complete the full webhook url
                self.webhook_url = f'{self.base_url}/webhook/{webhook_key}';
                self.logger.debug(f'Facebook webhook url: {self.webhook_url}');

                result = FacebookAPI.update_webhook(
                    app_secret=self.app_secret,
                    app_id=self.app_id,
                    api_url=self.api_url,
                    webhook=self.webhook_url,
                    verify_token=self.webhook_verify_token
                );      

            } else {
                self.logger.error('unable to generate webhook url for Facebook, missing required parameters');
            }
        } else {
            self.logger.warning('facebook action is disabled');
        }
               
    } 


    can sanitize_message(message:str) {
        return message.replace("**", "*").replace("<br/>", "\n").replace("<b>", "*").replace("</b>", "*");
    }


    can verify_request(request:dict) -> str {
        return FacebookAPI.parse_verification_request(request = request, verify_token=self.webhook_verify_token);
    }


    can send_message(session_id:str, message:InteractionMessage) {
        # processes an agent response payload format and sends an Facebook message to a specified session_id via the action
        if(message and session_id) {
            parent_message_id = message.get_meta('parent_message_id');

            if (message.get_type() == MessageType.SILENCE.value) {}
            elif(message.get_type() == MessageType.TEXT.value) {
                content = self.sanitize_message(message = message.get_content());
                outgoing = Utils.chunk_long_message(message=content, max_length = self.chunk_length, chunk_length = self.chunk_length);

                for chunk in outgoing {
                    FacebookAPI.send_text_message(recipient_id=session_id, message=chunk, api_url=self.api_url, page_id=self.pages.get("main_page").get("page_id"), access_token=self.pages.get("main_page").get("page_access_token"));
                }
            } elif(message.get_type() == MessageType.MEDIA.value) {
                # sending media 
                mime_type = Utils.get_mime_type(mime_type=message.mime);
                if(mime_type['file_type'] == "document") {
                    FacebookAPI.send_media(recipient_id= session_id, media_url=message.data.get('url'), media_type="document", api_url=self.api_url, page_id=self.pages.get("main_page").get("page_id"), access_token=self.pages.get("main_page").get("page_access_token"));
                }elif(mime_type['file_type'] == "image") {
                    FacebookAPI.send_media(recipient_id= session_id, media_url=message.data.get('url'), media_type="image", api_url=self.api_url, page_id=self.pages.get("main_page").get("page_id"), access_token=self.pages.get("main_page").get("page_access_token"));
                }elif(mime_type['file_type'] == "video") {
                    FacebookAPI.send_media(recipient_id= session_id, media_url=message.data.get('url'), media_type="video", api_url=self.api_url, page_id=self.pages.get("main_page").get("page_id"), access_token=self.pages.get("main_page").get("page_access_token"));
                }

                # sending caption 
                caption = self.sanitize_message(message = message.get_content());
                if(caption) {
                    FacebookAPI.send_text_message(recipient_id=session_id, message=caption, api_url=self.api_url, page_id=self.pages.get("main_page").get("page_id"), access_token=self.pages.get("main_page").get("page_access_token"));
                }
            } elif(message.get_type() == MessageType.MULTI.value) {
                for message_item in message.content {
                    if(message_item.get_type() == MessageType.TEXT.value) {
                        message = self.sanitize_message(message = message_item.get_content());
                        outgoing = Utils.chunk_long_message(message=message, max_length = self.chunk_length, chunk_length = self.chunk_length);

                        for chunk in outgoing {
                            FacebookAPI.send_text_message(recipient_id=session_id, message=chunk, api_url=self.api_url, page_id=self.pages.get("main_page").get("page_id"), access_token=self.pages.get("main_page").get("page_access_token"));
                        }
                    } elif(message_item.get_type() == MessageType.MEDIA.value) {
                        # sending media
                        mime_type = Utils.get_mime_type(mime_type=message_item.mime);
                        if(mime_type['file_type'] == "document") {
                            FacebookAPI.send_media(recipient_id= session_id, media_url=message_item.data.get('url'), media_type="document", api_url=self.api_url, page_id=self.pages.get("main_page").get("page_id"), access_token=self.pages.get("main_page").get("page_access_token"));
                        } elif(mime_type['file_type'] == "image") {
                            FacebookAPI.send_media(recipient_id= session_id, media_url=message_item.data.get('url'), media_type="image", api_url=self.api_url, page_id=self.pages.get("main_page").get("page_id"), access_token=self.pages.get("main_page").get("page_access_token"));
                        } elif(mime_type['file_type'] == "video") {
                            FacebookAPI.send_media(recipient_id= session_id, media_url=message_item.data.get('url'), media_type="video", api_url=self.api_url, page_id=self.pages.get("main_page").get("page_id"), access_token=self.pages.get("main_page").get("page_access_token"));
                        }
                        # sendign caption 
                        caption = self.sanitize_message(message = message_item.get_content());
                        if(caption) {
                            FacebookAPI.send_text_message(recipient_id=session_id, message=caption, api_url=self.api_url, page_id=self.pages.get("main_page").get("page_id"), access_token=self.pages.get("main_page").get("page_access_token"));
                        }
                    }
                }
            }
        }
    }


    can broadcast_message(message:InteractionMessage, channels:list, session_id:str) {
        # processes an agent response payload format and sends an ultramsg message to all session_ids via the action

        agent_node = self.get_agent();
        
        if(frames := agent_node.get_memory().get_frames() ) {
            # get all frames then proceed to broadcast
            for frame_node in frames {
                if(frame_node.session_id != session_id) {
                    if(interaction_node := frame_node.get_last_interaction()) {
                        if interaction_node.channel in ['whatsapp'] {
                            self.send_message(session_id = frame_node.session_id, message=message);
                        }
                    }
                }
            }
        }
    }


    can send_media(session_id:str, media_type:str, media_url:str) -> dict {
        result = self.convert_url(media_url);
        media_url = result.get('url');
        return FacebookAPI.send_media(recipient_id= session_id, media_url=media_url, media_type=media_type, api_url=self.api_url, page_id=self.pages.get("main_page").get("page_id"), access_token=self.pages.get("main_page").get("page_access_token"));
    }

    can get_post_link(post_id:str) -> str {
        return FacebookAPI.share_facebook_post(access_token=self.pages['main_page']['page_access_token'], post_id=post_id);
    }


    can post_message(message:str, post_link:bool = True) -> dict {
        post_id = FacebookAPI.post_message_to_page(access_token=self.pages['main_page']['page_access_token'], page_id=self.pages['main_page']['page_id'], api_url=self.api_url, message=message).get('id');
        if (post_link) {
            return self.get_post_link(post_id=post_id);
        }else{
            return post_id;
        }
    }


    can post_images(image_urls:list, caption:str, post_link:bool = True) -> dict {
        media_urls = [];
        for video_url in image_urls {
            result = self.convert_url(video_url);
            media_urls.append(result.get('url'));
        }
        post_id = FacebookAPI.post_images_to_page(access_token=self.pages['main_page']['page_access_token'], page_id=self.pages['main_page']['page_id'], api_url=self.api_url, image_urls=media_urls, caption=caption).get('id');
        if (post_link) {
            return self.get_post_link(post_id=post_id);
        }else{
            return post_id;
        }
    }


    can post_videos(video_urls:list, caption:str, title:str = "") -> dict {
        media_urls = [];
        for video_url in video_urls {
            result = self.convert_url(video_url);
            media_urls.append(result.get('url'));
        }
        post_link = FacebookAPI.post_videos_to_page(access_token=self.pages['main_page']['page_access_token'], page_id=self.pages['main_page']['page_id'], api_url=self.api_url, title=title, caption=caption, video_urls=media_urls).get('id');

        if (post_link) {
            return self.get_post_link(post_id=post_id);
        }else{
            return post_id;
        }
    }


    can get_posts(limit:int = 10) -> dict {
        return FacebookAPI.get_page_posts(access_token=self.pages['main_page']['page_access_token'], page_id=self.pages['main_page']['page_id'], api_url=self.api_url, limit=limit);
    }

    
    can get_post(post_id:str) -> dict {
        return FacebookAPI.get_single_post(access_token=self.pages['main_page']['page_access_token'], post_id=post_id, api_url=self.api_url);
    }


    can get_comments(post_id: str, limit: int = 10) -> dict {
        return FacebookAPI.get_post_comments(access_token=self.pages['main_page']['page_access_token'], post_id=post_id, api_url=self.api_url, limit=limit);
    }


    can comment_on_post(post_id: str, message: str) -> dict {
        return FacebookAPI.comment_on_post(access_token=self.pages['main_page']['page_access_token'], post_id=post_id, api_url=self.api_url, message=message);
    }


    can update_comment(comment_id: str, message: str) -> dict {
        return FacebookAPI.update_comment(access_token=self.pages['main_page']['page_access_token'], comment_id=comment_id, api_url=self.api_url, message=message);
    }


    can like_comment(comment_id: str) -> dict {
        return FacebookAPI.like_comment(access_token=self.pages['main_page']['page_access_token'], comment_id=comment_id, api_url=self.api_url);
    }


    can get_reactions(post_id: str) -> dict {
        return FacebookAPI.get_reactions(access_token=self.pages['main_page']['page_access_token'], post_id=post_id, api_url=self.api_url);
    }


    can reply_to_comment(comment_id: str, message: str) -> dict {
        return FacebookAPI.reply_to_comment(access_token=self.pages['main_page']['page_access_token'], comment_id=comment_id, api_url=self.api_url, message=message);
    }


    can reply_to_comment_with_attachment(comment_id: str, message: str, attachment_url: str) -> dict{
        return FacebookAPI.reply_to_comment_with_attachment(access_token=self.pages['main_page']['page_access_token'], comment_id=comment_id, api_url=self.api_url, message=message, attachment_url=attachment_url);
    }

    can convert_url(url:str, folder:str = "./.files") -> dict {
        Utils.delete_files(directory=folder, days=30);
        name = FacebookAPI.download_file(url, folder);
        url = f"{os.environ.get('JIVAS_FILES_URL','http://localhost:8000/files')}/{name}";
        
        return {
            "name": name,
            "url": url
        };
    }
}