import requests
import traceback
import os
import uuid
import logging

class UltramsgAPI: 
    
    logger = logging.getLogger(__name__)
    
    @staticmethod
    def parse_inbound_message(request: dict):
        """ parses message request payload and returns extracted values """

        """ payload structure
        
        {'event_type': 'message_received', 'instanceId': '81156', 'id': '', 'referenceId': '', 'hash': '8eef972cf4d25d894ad84089fee51c6a', 
        'data': {
            'id': 'false_5926415808@c.us_3AE3F1500842604C05B1', 
            'from': '5926415808@c.us', 
            'to': '5927231648@c.us', 
            'author': '', 
            'pushname': 'Eldon Marks', 
            'ack': '', 
            'type': 'chat', 
            'body': 'How are you?', 
            'media': '', 
            'fromMe': False, 
            'self': False, 
            'isForwarded': False, 
            'isMentioned': False, 
            'quotedMsg': {}, 
            'mentionedIds': [], 
            'time': 1729463879
            }
        }
        
        """
        
        data = {}
        
        if request:
   
            data['message_id'] = request["data"]["id"]
            data['instance_id'] = request['instanceId']
            data['event_type'] = request['event_type']
            data['time'] = request['data']['time']
            data['author'] = request['data']['author']
            data['from_self'] = request['data']['fromMe']
            data['sender_name'] = request.get('data', {}).get('pushname', '')         
            data['sender_number'] = str(request['data']['from'].replace('@c.us', ''))
            data['agent_number'] = str(request['data']['to'].replace('@c.us', ''))
            data['parent_message'] = request['data'].get('quotedMsg', '')
            data['message_type'] = request['data'].get('type', 'unknown')
            data['body'] = request["data"]["body"]            
            data['media'] = request.get('data', {}).get('media', '')
            data['location'] = request.get('data', {}).get('location', '')
            # add caption to media messages if present
            if data['message_type'] != 'chat':
                data['caption'] = data['body']
         
        return data
    
        
    @staticmethod
    def send_rest_request(url: str, 
                          data: dict = None, 
                          method: str="POST", 
                          headers: dict = None, 
                          params: dict = None
                          ):
        
        """
        Sends a REST API request and returns a structured response if successful, None otherwise.

        Parameters:
        - method (str): HTTP method to use (e.g., 'GET', 'POST', 'PUT', 'DELETE').
        - url (str): The URL endpoint for the request.
        - headers (dict): Optional headers to include in the request. Defaults to JSON content type.
        - data (dict): Optional data payload for requests (typically POST/PUT). Sent in the request body.
        - params (dict): Optional query parameters for GET requests. Appended to the URL.

        Returns:
        - dict: A dictionary containing either the response data if successful, or None if failed.
        """
        
        if headers is None:
            headers = {"Content-Type": "application/json"}

        try:
            # Support for GET, POST, PUT, DELETE, etc.
            response = requests.request(method=method, url=url, headers=headers, json=data, params=params)

            # Check if the response is successful
            if response.status_code // 100 == 2:  # Status codes 200-299
                result = response.json()
                
                if(result and result.get('error', False)):
                    UltramsgAPI.logger.error(f'Ultramsg request error: {result.get('error', False)}')
                    
                return result
            else:
                error = f"Request failed with status code {response.status_code}, response: {response.text}"
                UltramsgAPI.logger.error(error)
                return {'error': error}

        except requests.exceptions.RequestException as e:
            # Handle broader request exceptions
            error = f"error while executing ultramsg call: {str(e)}"
            UltramsgAPI.logger.error(error)
            return {'error': error}


    @staticmethod
    def send_text_message(phone_number: str, message: str, api_url: str, api_key: str, msg_id=""):
        # send text based message to phone number
               
        data = {
            "token": api_key,
            "to": phone_number,
            "body": message,
            "msgId": msg_id
        }
        
        return UltramsgAPI.send_rest_request(url = f"{api_url}/messages/chat", data = data)

        

    @staticmethod
    def send_image(phone_number: str, media_url: str, api_url: str, api_key: str, caption="", msg_id=""):
        # send image based message to phone number and image url
            
        data = {
            "token": api_key,
            "to": phone_number,
            "image": media_url,
            "caption": caption,
            "msgId": msg_id
        }

        return UltramsgAPI.send_rest_request(url = f"{api_url}/messages/image", data = data)



    @staticmethod
    def send_sticker(phone_number: str, media_url: str, api_url: str, api_key: str, msg_id=""):
        # send sticker based message to phone number and sticker url

        data = {
            "token": api_key,
            "to": phone_number,
            "sticker": media_url,
            "msgId": msg_id
        }
        
        return UltramsgAPI.send_rest_request(url = f"{api_url}/messages/sticker", data = data)


    @staticmethod
    def send_document(phone_number: str, media_url: str, api_url: str, api_key: str, filename: str, caption="", msg_id=""):
        # send document based message to phone number and document url

        data = {
            "token": api_key,
            "to": phone_number,
            "filename": filename,
            "document": media_url,
            "caption": caption,
            "msgId": msg_id
        }
        
        return UltramsgAPI.send_rest_request(url = f"{api_url}/messages/document", data = data)


    @staticmethod
    def send_audio(phone_number: str, media: str, api_url: str, api_key: str, msg_id=""):
        # send audio based message to phone number and audio 

        data = {
            "token": api_key,
            "to": phone_number,
            "audio": media,
            "msgId": msg_id
        }
        
        return UltramsgAPI.send_rest_request(url = f"{api_url}/messages/audio", data = data)


    @staticmethod
    def send_voice(phone_number: str, media: str, api_url: str, api_key: str, msg_id=""):
        # send voice note based message to phone number and voice note url
        
        data = {
            "token": api_key,
            "to": phone_number,
            "audio": media,
            "msgId": msg_id
        }
        
        return UltramsgAPI.send_rest_request(url = f"{api_url}/messages/voice", data = data)


    @staticmethod
    def send_video(phone_number: str, media_url: str, api_url: str, api_key: str, caption="", msg_id=""):
        # send video based message to phone number based on video url

        data = {
            "token": api_key,
            "to": phone_number,
            "video": media_url,
            "caption": caption,
            "msgId": msg_id
        }
        
        return UltramsgAPI.send_rest_request(url = f"{api_url}/messages/video", data = data)


    @staticmethod
    def send_contact(phone_number: str, contact: str, api_url: str, api_key: str, msg_id=""):
        # send contact based message to phone number using vcard. vcard must be generated first check uktramsg for more details

        data = {
            "token": api_key,
            "to": phone_number,
            "contact": contact,
            "msgId": msg_id
        }

        return UltramsgAPI.send_rest_request(url = f"{api_url}/messages/contact", data = data)


    @staticmethod
    def send_location(phone_number: str, address: str, lat: float, lng: float, api_url: str, api_key: str, msg_id=""):
        # send location based message to phone number based address and lcation coordinates received

        data = {
            "token": api_key,
            "to": phone_number,
            "address": address,
            "lat": lat,
            "lng": lng,
            "msgId": msg_id
        }

        return UltramsgAPI.send_rest_request(url = f"{api_url}/messages/location", data = data)


    @staticmethod
    def send_vcard(phone_number: str, vcard: str, api_url: str, api_key: str, msg_id=""):
        # send contact (vcard) based message to phone number well based on the vcard you created

        data = {
            "token": api_key,
            "to": phone_number,
            "vcard": vcard,
            "msgId": msg_id
        }

        return UltramsgAPI.send_rest_request(url = f"{api_url}/messages/vcard", data = data)


    @staticmethod
    def send_reaction(msgId: str, reaction: str, api_url: str, api_key: str):
        # send reaction based message to phone number based on reaction

        data = {
            "token": api_key,
            "msgId": msgId,
            "emoji": reaction
        }

        return UltramsgAPI.send_rest_request(url = f"{api_url}/messages/reaction", data = data)


    @staticmethod
    def delete_message(phone_number: str, msgId: str, api_url: str, api_key: str):
        # delete message based on message id

        data = {
            "token": api_key,
            "msgId": msgId
        }

        return UltramsgAPI.send_rest_request(url = f"{api_url}/messages/delete", data = data)


    @staticmethod
    def send_by_status(phone_number: str, status: str, api_url: str, api_key: str):
        # send message based on the staus of the message or mesages

        data = {
            "token": api_key,
            "status": status
        }
        
        return UltramsgAPI.send_rest_request(url = f"{api_url}/messages/resendByStatus", data = data)


    @staticmethod
    def send_by_id(phone_number: str, id: str, api_url: str, api_key: str):
        # send message based on message id

        data = {
            "token": api_key,
            "id": id
        }
        
        return UltramsgAPI.send_rest_request(url = f"{api_url}/messages/resendById", data = data)


    @staticmethod
    def clear_messages(phone_number: str, status: str, api_url: str, api_key: str):
        # clear all messages based on status

        data = {
            "token": api_key,
            "status": status
        }
        
        return UltramsgAPI.send_rest_request(url = f"{api_url}/messages/clear", data = data)


    @staticmethod
    def get_messages(phone_number: str, page: int, limit: int, status: str, sort: str, api_url: str, api_key: str):
        # get all messages based on status

        data = {
            "token": api_key,
            "page": page,
            "limit": limit,
            "status": status,
            "sort": sort
        }
        
        return UltramsgAPI.send_rest_request(url = f"{api_url}/messages", data = data)


    @staticmethod
    def get_statistics(phone_number: str, api_url: str, api_key: str):
        # get account statistics
        
        data = {
            "token": api_key
        }
        
        return UltramsgAPI.send_rest_request(url = f"{api_url}/messages/statistics", data = data)


    @staticmethod
    def get_instance_status(phone_number: str, api_url: str, api_key: str):
        # get the status of the instance

        data = {
            "token": api_key
        }
        
        return UltramsgAPI.send_rest_request(url = f"{api_url}/instance/status", data = data)


    @staticmethod
    def get_qr_image(phone_number: str, api_url: str, api_key: str):
        # get qr image

        data = {
            "token": api_key
        }
        
        return UltramsgAPI.send_rest_request(url = f"{api_url}/instance/qr", data = data)


    @staticmethod
    def get_authentication_qr(phone_number: str, api_url: str, api_key: str):
        # get qr image for authentication

        data = {
            "token": api_key
        }
        
        return UltramsgAPI.send_rest_request(url = f"{api_url}/instance/qrCode", data = data)


    @staticmethod
    def get_connected_phones(phone_number: str, api_url: str, api_key: str):
        # get all connected phones

        data = {
            "token": api_key
        }
        
        return UltramsgAPI.send_rest_request(url = f"{api_url}/instance/me", data = data)


    @staticmethod
    def get_instance_settings(phone_number: str, api_url: str, api_key: str):
        # get the current instance settings

        data = {
            "token": api_key
        }
        
        return UltramsgAPI.send_rest_request(url = f"{api_url}/instance/settings", params = data, method = "GET")


    @staticmethod
    def logout(phone_number: str, api_url: str, api_key: str):
        # logout out of whatsapp

        data = {
            "token": api_key
        }
        
        return UltramsgAPI.send_rest_request(url = f"{api_url}/instance/logout", data = data)

        
    @staticmethod
    def restart_instance(phone_number: str, api_url: str, api_key: str):
        # restart the instance

        data = {
            "token": api_key
        }
        
        return UltramsgAPI.send_rest_request(url = f"{api_url}/instance/restart", data = data)

        
    @staticmethod
    def update_instance_settings(
        webhook_url: str, 
        send_delay: int, 
        webhook_message_received: str, 
        webhook_message_create: str, 
        webhook_message_ack: str, 
        webhook_message_download_media: str, 
        api_url: str, 
        api_key: str):
        
        # update instance setings

        data = {
            "token": api_key,
            "sendDelay": send_delay,
            "webhook_url": webhook_url,
            "webhook_message_received": webhook_message_received,
            "webhook_message_create": webhook_message_create,
            "webhook_message_ack": webhook_message_ack,
            "webhook_message_download_media": webhook_message_download_media
        }
        
        return UltramsgAPI.send_rest_request(url = f"{api_url}/instance/settings", data = data)


    @staticmethod
    def clear_settings(phone_number: str, api_url: str, api_key: str):
        # clear all instance settings

        data = {
            "token": api_key
        }

        return UltramsgAPI.send_rest_request(url = f"{api_url}/instance/clear", data = data)


    @staticmethod
    def download_media(media_url: str, filename: str=""):
        """
        Downloads media from a given URL and saves it to a specified filename.

        Args:
            media_url (str): The URL of the media to download.
            filename (str): The local path where the media will be saved.

        Returns:
            dict: A dictionary with the status code of the operation.
        """
        try:
            response = requests.get(media_url)
            response.raise_for_status()  # Raise an exception if the response status is not 200 OK

            # Get the content type from the response headers
            mime_type = response.headers.get('Content-Type', '')
            
            if filename:
                # utiilse the filename if provided               
                with open(filename, "wb") as file:
                    file.write(response.content)

                if os.path.exists(filename):
                    message = f"media saved to {filename} successfully"
                    UltramsgAPI.logger.debug(message)
                    return {"success": message}
                else:
                    message = f"unable to save media to {filename}"
                    UltramsgAPI.logger.error(message)
                    return {"error": message}
                
            else:
                # otherwise return the data directly
                UltramsgAPI.logger.debug('returned media binary')
                return {'success': {'mime_type': mime_type, 'content': response.content}}

        except requests.exceptions.RequestException as e:
            UltramsgAPI.logger.error(f"an exception occurred, {traceback.format_exc()}")
            return {"error": str(e)}


    @staticmethod
    def mark_as_read(phone_number: str, instance_id: str, api_key: str):
        # mark message as read

        data = {
            "token": api_key,
            "chatId": phone_number
        }
        
        return UltramsgAPI.send_rest_request(url = f"https://api.ultramsg.com/{instance_id}/chats/read", data = data)
    
    
    @staticmethod
    def api_transcribe_audio_url(audio_url:str, api_url: str = "", data: dict = {}):
        """
        Transcribes audio file using TS Platform.

        Args:
            audio_file_path (str): The path to the audio file to transcribe.
            api_token (str): The API token for accessing the Jivas API.
            api_url (str): The URL of the Jivas API endpoint.

        Returns:
            dict: A dictionary containing the status, transcription result, and transcript.
        """
        
        
        # initialise variables
        transcript = None
        status = None
        response= None
        result = None
        
        # download the audio file
        filename = str(uuid.uuid4())
        UltramsgAPI.download_media(audio_url, filename)

        try:
            # Define the headers for the HTTP request
            headers = {}

            # prep the audio file
            files=[
                ('audio',(filename, open(filename,'rb'),'audio/mp3'))
            ]
            
            # delete the audio file
            if os.path.exists(filename):
                os.remove(filename)
            
            response = requests.request("POST", api_url, headers=headers, data=data, files=files)

            # Check if request was successful
            if response.status_code == 201:
                result = response.json()
                status = "success"
            else:
                result = {"message": f"Error: {response.status_code} - {response.reason}"}
                status = "error"
        except Exception as e:
            UltramsgAPI.logger.error(f"an exception occurred, {traceback.format_exc()}")
            result = {"message": f"Error: {str(e)}"}
            status = "error"

        return {status: result}
