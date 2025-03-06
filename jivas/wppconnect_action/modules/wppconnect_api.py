import time
import requests
import os
import json
import base64
import logging
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

class WppconnectAPI:
    logger = logging.getLogger(__name__)

    @staticmethod
    def send_request(url: str, data: dict = None, method: str = "POST", headers: dict = None):
        """
        Handles HTTP requests with centralized logic for the WhatsApp API.

        Parameters:
        - url (str): Endpoint URL.
        - data (dict): Payload for the request.
        - method (str): HTTP method (GET, POST, etc.).
        - headers (dict): Custom headers.

        Returns:
        - dict: Response JSON or error message.
        """
        if headers is None:
            headers = {"Content-Type": "application/json"}

        try:
            response = requests.request(method=method, url=url, json=data, headers=headers)
            if response.status_code // 100 == 2:  # Check for successful status codes
                return response.json()
            else:
                error = f"Request failed with status {response.status_code}: {response.text}"
                WppconnectAPI.logger.error(error)
                return {"error": error}
        except requests.RequestException as e:
            error = f"Request error: {str(e)}"
            WppconnectAPI.logger.error(error)
            return {"error": error}

    @staticmethod
    def parse_inbound_message(request: dict):
        """
        Parses an inbound message payload and extracts relevant details.

        Parameters:
        - request (dict): Incoming message payload.

        Returns:
        - dict: Parsed payload data with extracted information. 
                Returns an empty dictionary if the payload is invalid.
        """
        payload = {}
        try:
            # Extract the body from the request payload
            data = request

            # Validate the event type
            valid_events = ["onmessage", "onpollresponse", "onack"]
            if data.get("event") not in valid_events:
                return {}

            # Initialize the payload with default values
            payload = {
                "sender_number": data.get("from", "").replace("@c.us", ""),  # Extract sender's number
                "message_id": data.get("id", ""),                           # Extract message ID
                "event_type": data.get("dataType", data.get("event", "")),  # Identify the event type
                "message_type": data.get("type", ""),                         # Identify the media type
                "fromMe": False,          # Determine if the message is sent by the agent
                "author": data.get("author", "").replace("@c.us", ""),      # Extract author of the message
                "agent_number": data.get("to", "").replace("@c.us", ""),    # Extract the agent's number
                "caption": data.get("caption", ""),                         # Extract caption for media
                "location": data.get("location", {}),                       # Extract location details if provided
                "isGroup": False,                                           # Default group flag
            }

            # fromeMe
            if (type(payload["fromMe"]) == dict):
                # from me
                payload["fromMe"] = payload["fromMe"].get("fromMe", "")

            # Extract parent message details if available
            if "quotedMsg" in data:
                payload["parent_message"] = data["quotedMsg"]

            # Identify if the message is part of a group
            if (
                payload["author"]
                and payload["sender_number"]
                and payload["author"] != payload["sender_number"]
            ):
                payload["isGroup"] = True

            # Extract additional details based on the media type
            if payload["message_type"] == "chat":
                payload["body"] = data.get("content", "")
            elif payload["message_type"] in ["image", "video", "document"]:
                payload.update({
                    "media": data.get("body", ""),
                    "filename": data.get("filename", ""),
                    "mime_type": data.get("mimetype", ""),
                })
            elif payload["message_type"] == "location":
                payload["location"] = data.get("location", {})
            elif payload["message_type"] == "audio" or payload["message_type"] == "ptt":
                payload["media"] = data.get("body", "")                         
            elif payload["message_type"] == "sticker":
                payload["media"] = data.get("body", "")
            elif payload["message_type"] in ["contacts", "vcard"]:
                payload["contact"] = data.get("body", {})
            elif payload["event_type"] == "onpollresponse":
                payload.update({
                    "poll_id": data.get("msgId", {}).get("_serialized", ""),
                    "selectedOptions": data.get("selectedOptions", ""),
                })

            # Add additional sender details if available
            sender_name = data.get("notifyName", "")
            if sender_name:
                payload["sender_name"] = sender_name

                return payload

        except Exception as e:
            # Log the error for debugging purposes
            WppconnectAPI.logger.error(f"Error parsing inbound message: {str(e)}")
            return {}
    
    @staticmethod
    def send_text_message(phone_number: str, message: str, api_url: str, api_key: str, session_id: str, is_group=False, msg_id="", options: dict = {}, is_newsletter: bool = False):
        """
        Sends a text message using the WhatsApp API.

        Parameters:
        - phone_number (str): Recipient phone number.
        - message (str): Message content.
        - api_url (str): API base URL.
        - api_key (str): API authentication key.
        - session_id (str): Session ID.
        - is_group (bool): Whether the message is for a group.
        - msg_id (str): Optional message ID.

        Returns:
        - dict: API response.
        """
        if msg_id:
            response = WppconnectAPI.reply_text_message(phone_number=phone_number, message=message, api_url=api_url, api_key=api_key, sessionId=session_id, isGroup=is_group, options=options, is_newsletter=is_newsletter, msg_id=msg_id)
            return response
    
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "phone": phone_number,
            "isGroup": is_group,
            "isNewsletter": is_newsletter,
            "message": message,
            "options": options
        }

        return WppconnectAPI.send_request(f"{api_url}/api/{session_id}/send-message", data=data, headers=headers)

    @staticmethod
    def send_media(phone_number: str, media_url: str, api_url: str, api_key: str, session_id: str, caption="", file_name="",is_group=False, options: dict = {}, is_newsletter: bool = False):
        """
        Sends media via the WhatsApp API.

        Parameters:
        - phone_number (str): Recipient phone number.
        - media_url (str): URL of the media file.
        - api_url (str): API base URL.
        - api_key (str): API authentication key.
        - session_id (str): Session ID.
        - caption (str): Optional caption for the media.
        - file_name (str): Optional file name.

        Returns:
        - dict: API response.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "phone": phone_number,
            "isGroup": is_group,
            "isNewsletter": is_newsletter,
            "filename": file_name,
            "caption": caption,
            "path": media_url
        }
        return WppconnectAPI.send_request(f"{api_url}/api/{session_id}/send-file", data=data, headers=headers)

    @staticmethod
    def send_poll(phone_number: str, content: dict, api_url: str, api_key: str, session_id: str, is_group=False, options=None):
        """
        Sends a poll via the WhatsApp API.

        Parameters:
        - phone_number (str): Recipient phone number.
        - content (dict): Poll content with questions and options.
        - api_url (str): API base URL.
        - api_key (str): API authentication key.
        - session_id (str): Session ID.
        - is_group (bool): Whether the message is for a group.
        - options (dict): Additional options for the poll.

        Returns:
        - dict: API response.
        """
        if options is None:
            options = {"selectableCount": 1}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "phone": phone_number,
            "isGroup": is_group,
            "name": content.get("name", ""),
            "choices": content.get("choices", []),
            "options": options
        }
        return WppconnectAPI.send_request(f"{api_url}/api/{session_id}/send-poll-message", data=data, headers=headers)

    @staticmethod
    def download_media(media_url: str, filename: str):
        """
        Downloads media from a given URL.

        Parameters:
        - media_url (str): URL of the media to download.
        - filename (str): Path to save the file.

        Returns:
        - dict: Status of the operation.
        """
        try:
            response = requests.get(media_url)
            response.raise_for_status()
            with open(filename, "wb") as file:
                file.write(response.content)
            return {"status": "success", "file": filename}
        except Exception as e:
            WppconnectAPI.logger.error(f"Error downloading media: {str(e)}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def encode_media_base64(file_path: str):
        """
        Encodes a file into base64 format.

        Parameters:
        - file_path (str): Path to the file.

        Returns:
        - str: Base64-encoded string.
        """
        try:
            with open(file_path, "rb") as file:
                return base64.b64encode(file.read()).decode("utf-8")
        except Exception as e:
            WppconnectAPI.logger.error(f"Error encoding file to base64: {str(e)}")
            return None

    @staticmethod
    def send_audio_base64(phone_number: str, base64_encoded: str, api_url: str, api_key: str, session_id: str, is_group=False, caption="", file_name=""):
        """
        Sends an audio message encoded in base64 format.

        Parameters:
        - phone_number (str): Recipient phone number.
        - media_url (str): URL of the media to send.
        - api_url (str): API base URL.
        - api_key (str): API authentication key.
        - session_id (str): Session ID.
        - is_group (bool): Whether the message is for a group.
        - caption (str): Optional caption for the media.
        - file_name (str): File name for downloading the media.

        Returns:
        - dict: API response.
        """

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "phone": phone_number,
            "isGroup": is_group,
            "base64Ptt": base64_encoded
        }
        return WppconnectAPI.send_request(f"{api_url}/api/{session_id}/send-voice-base64", data=data, headers=headers)

    @staticmethod
    def reply_text_message(phone_number: str, message: str, api_url: str, api_key: str, session_id: str, msg_id: str, is_group=False):
        """
        Sends a reply to a specific message.

        Parameters:
        - phone_number (str): Recipient phone number.
        - message (str): Reply message content.
        - api_url (str): API base URL.
        - api_key (str): API authentication key.
        - session_id (str): Session ID.
        - msg_id (str): Message ID to reply to.
        - is_group (bool): Whether the reply is for a group.

        Returns:
        - dict: API response.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "phone": phone_number,
            "isGroup": is_group,
            "message": message,
            "messageId": msg_id
        }
        return WppconnectAPI.send_request(f"{api_url}/api/{session_id}/send-reply", data=data, headers=headers)
    
    @staticmethod
    def send_voicenote(phone_number: str, media_url: str, api_url: str, api_key: str, session_id: str, is_group=False, quoted_message_id=""):
        """
        Sends a voice note.

        Parameters:
        - phone_number (str): Recipient phone number.
        - media_url (str): URL of the voice note.
        - api_url (str): API base URL.
        - api_key (str): API authentication key.
        - session_id (str): Session ID.
        - is_group (bool): Whether the voice note is for a group.
        - quoted_message_id (str): Quoted message ID.

        Returns:
        - dict: API response.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "phone": phone_number,
            "isGroup": is_group,
            "path": media_url,
            "quotedMessageId": quoted_message_id
        }
        return WppconnectAPI.send_request(f"{api_url}/api/{session_id}/send-voice", data=data, headers=headers)
    
    @staticmethod
    def get_media(encoded_data: str, file_path: str):
        """
        Decodes a base64 string and saves it as a file.

        Parameters:
        - encoded_data (str): Base64-encoded data.
        - file_path (str): Path to save the decoded file.

        Returns:
        - dict: Status of the operation.
        """
        try:
            decoded_data = base64.b64decode(encoded_data)
            with open(file_path, "wb") as file:
                file.write(decoded_data)
            return {"status": "success", "file": file_path}
        except Exception as e:
            WppconnectAPI.logger.error(f"Error saving media: {str(e)}")
            return {"status": "error", "error": str(e)}
        
        
    def get_status(instance_id, api_key, api_url):
        url = f"{api_url}/api/{instance_id}/status-session"
        
        headers = {
            "accept": "*/*",
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)  # Use GET instead of POST
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}


    def start_instance(instance_id, api_key, api_url, webhook="", wait_qr_code=False):
        url = f"{api_url}/api/{instance_id}/start-session"
        headers = {
            "accept": "*/*",
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {"webhook": webhook, "waitQrCode": wait_qr_code}

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}


    def stop_instance(instance_id, api_key, api_url):
        url = f"{api_url}/api/{instance_id}/close-session"
        headers = {
            "accept": "*/*",
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {}

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
        

    def create_instance(api_url, instance_id, api_key):
        url = f"{api_url}/api/{instance_id}/{api_key}/generate-token"
        
        headers = {
            "accept": "*/*",
        }
        payload = ""

        try:
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}


    def get_qrcode(api_url: str, api_key: str, instance_id: str):
        url = f"{api_url}/api/{instance_id}/qrcode-session"
        headers = {
            "accept": "*/*",
            "Authorization": f"Bearer {api_key}"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            # If the response contains raw binary data (e.g., PNG), encode it as Base64
            return {"qrcode": base64.b64encode(response.content).decode('ascii')}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}


    @staticmethod
    def logout(api_url: str, api_key: str, instance_id: str):
        url = f"{api_url}/api/{instance_id}/logout-session"
        headers = {
            "accept": "*/*",
            "Authorization": f"Bearer {api_key}"
        }
        response = requests.post(url, headers=headers)
        
        if response.json()['status'] == 'Disconnected':
            return True
        else:
            return False
    

    @staticmethod
    def register_wppconnect_action(api_url, instance_id, api_key, master_key, webhook="", wait_qr_code=False, timeout = 60):
        create_result = {}
        qr_code = ""
        version = ""
        status = ""

        start_time = time.time()
        can_break = False

        while time.time() - start_time < timeout and not can_break:
            status_result = WppconnectAPI.get_status(instance_id, api_key, api_url)
            status = status_result.get("status")
            error = status_result.get("error")
            version = status_result.get("version")


            if error and "401 Client Error:" in error:
                create_result = WppconnectAPI.create_instance(api_url, instance_id, master_key)
                api_key = create_result.get("token")
                status = "CREATED"
            elif status == "CLOSED":
                WppconnectAPI.start_instance(instance_id, api_key, api_url, webhook, wait_qr_code)
                status = "STARTING"
            elif status == "QRCODE" and status_result.get("qrcode"):
                qr_code_result = WppconnectAPI.get_qrcode(api_url, api_key, instance_id)
                qr_code = qr_code_result["qrcode"]
                can_break = True
            elif status == "CONNECTED":
                WppconnectAPI.stop_instance(instance_id, api_key, api_url)
                WppconnectAPI.start_instance(instance_id, api_key, api_url, webhook, wait_qr_code)
                status = "UPDATING WEBHOOK"
                can_break = True
            else:
                status = "CONNECTING"

            print("WPP STATUS: ", status)
            time.sleep(5)  # Wait before retrying to avoid excessive API calls

        return {
            "qr_code": qr_code,
            "api_key": api_key,
            "instance_id": instance_id,
            "status": status,
            "version": version
        }
