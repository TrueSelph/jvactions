"""This module contains the WppconnectAPI class for handling requests to the WhatsApp API."""

import base64
import logging
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()


class WppconnectAPI:
    """Class for handling requests to the WhatsApp API."""

    logger = logging.getLogger(__name__)

    @staticmethod
    def send_request(
        url: str,
        data: Optional[dict] = None,
        method: str = "POST",
        headers: Optional[dict] = None,
    ) -> dict:
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
            response = requests.request(
                method=method, url=url, json=data, headers=headers
            )
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
    def parse_inbound_message(request: dict) -> dict:
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
                "sender_number": data.get("from", "").replace(
                    "@c.us", ""
                ),  # Extract sender's number
                "message_id": data.get("id", ""),  # Extract message ID
                "event_type": data.get(
                    "dataType", data.get("event", "")
                ),  # Identify the event type
                "message_type": data.get("type", ""),  # Identify the media type
                "fromMe": False,  # Determine if the message is sent by the agent
                "author": data.get("author", "").replace(
                    "@c.us", ""
                ),  # Extract author of the message
                "agent_number": data.get("to", "").replace(
                    "@c.us", ""
                ),  # Extract the agent's number
                "caption": data.get("caption", ""),  # Extract caption for media
                "location": data.get(
                    "location", {}
                ),  # Extract location details if provided
                "isGroup": False,  # Default group flag
            }

            # fromeMe
            if isinstance(payload["fromMe"], dict):
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
                payload.update(
                    {
                        "media": data.get("content", ""),
                        "filename": data.get("filename", ""),
                        "mime_type": data.get("mimetype", ""),
                    }
                )
            elif payload["message_type"] == "location":
                payload["location"] = data.get("location", {})
            elif payload["message_type"] in ["audio", "ptt", "sticker"]:
                payload["media"] = data.get("body", "")
            elif payload["message_type"] in ["contacts", "vcard"]:
                payload["contact"] = data.get("body", {})
            elif payload["event_type"] == "onpollresponse":
                payload.update(
                    {
                        "poll_id": data.get("msgId", {}).get("_serialized", ""),
                        "selectedOptions": data.get("selectedOptions", ""),
                    }
                )

            # Add additional sender details if available
            sender_name = data.get("notifyName", "")
            if sender_name:
                payload["sender_name"] = sender_name

                return payload
            return {}

        except Exception as e:
            # Log the error for debugging purposes
            WppconnectAPI.logger.error(f"Error parsing inbound message: {str(e)}")
            return {}

    @staticmethod
    def send_text_message(
        phone_number: str,
        message: str,
        api_url: str,
        api_key: str,
        session_id: str,
        is_group: bool = False,
        msg_id: str = "",
        options: Optional[dict] = None,
        is_newsletter: bool = False,
    ) -> dict:
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
            response = WppconnectAPI.reply_text_message(
                phone_number=phone_number,
                message=message,
                api_url=api_url,
                api_key=api_key,
                session_id=session_id,
                is_group=is_group,
                msg_id=msg_id,
            )
            return response

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        data = {
            "phone": phone_number,
            "isGroup": is_group,
            "isNewsletter": is_newsletter,
            "message": message,
            "options": options,
        }

        return WppconnectAPI.send_request(
            f"{api_url}/api/{session_id}/send-message", data=data, headers=headers
        )

    @staticmethod
    def send_media(
        phone_number: str,
        media_url: str,
        api_url: str,
        api_key: str,
        session_id: str,
        caption: str = "",
        file_name: str = "",
        is_group: bool = False,
        options: Optional[dict] = None,
        is_newsletter: bool = False,
    ) -> dict:
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
            "Authorization": f"Bearer {api_key}",
        }
        data = {
            "phone": phone_number,
            "isGroup": is_group,
            "isNewsletter": is_newsletter,
            "filename": file_name,
            "caption": caption,
            "path": media_url,
        }
        return WppconnectAPI.send_request(
            f"{api_url}/api/{session_id}/send-file", data=data, headers=headers
        )

    @staticmethod
    def send_poll(
        phone_number: str,
        content: dict,
        api_url: str,
        api_key: str,
        session_id: str,
        is_group: bool = False,
        options: Optional[dict] = None,
    ) -> dict:
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
            "Authorization": f"Bearer {api_key}",
        }
        data = {
            "phone": phone_number,
            "isGroup": is_group,
            "name": content.get("name", ""),
            "choices": content.get("choices", []),
            "options": options,
        }
        return WppconnectAPI.send_request(
            f"{api_url}/api/{session_id}/send-poll-message", data=data, headers=headers
        )

    @staticmethod
    def download_media(media_url: str, filename: str) -> dict:
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
    def encode_media_base64(file_path: str) -> str:
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
            return ""

    @staticmethod
    def send_audio_base64(
        phone_number: str,
        base64_encoded: str,
        api_url: str,
        api_key: str,
        session_id: str,
        is_group: bool = False,
        caption: str = "",
        file_name: str = "",
    ) -> dict:
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
            "Authorization": f"Bearer {api_key}",
        }
        data = {"phone": phone_number, "isGroup": is_group, "base64Ptt": base64_encoded}
        return WppconnectAPI.send_request(
            f"{api_url}/api/{session_id}/send-voice-base64", data=data, headers=headers
        )

    @staticmethod
    def reply_text_message(
        phone_number: str,
        message: str,
        api_url: str,
        api_key: str,
        session_id: str,
        msg_id: str,
        is_group: bool = False,
    ) -> dict:
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
            "Authorization": f"Bearer {api_key}",
        }
        data = {
            "phone": phone_number,
            "isGroup": is_group,
            "message": message,
            "messageId": msg_id,
        }
        return WppconnectAPI.send_request(
            f"{api_url}/api/{session_id}/send-reply", data=data, headers=headers
        )

    @staticmethod
    def send_voicenote(
        phone_number: str,
        media_url: str,
        api_url: str,
        api_key: str,
        session_id: str,
        is_group: bool = False,
        quoted_message_id: str = "",
    ) -> dict:
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
            "Authorization": f"Bearer {api_key}",
        }
        data = {
            "phone": phone_number,
            "isGroup": is_group,
            "path": media_url,
            "quotedMessageId": quoted_message_id,
        }
        return WppconnectAPI.send_request(
            f"{api_url}/api/{session_id}/send-voice", data=data, headers=headers
        )

    @staticmethod
    def get_media(encoded_data: str, file_path: str) -> dict:
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

    @staticmethod
    def update_webhookurl(
        webhook_url: str,
        api_url: str,
        api_key: str,
        session_id: str,
        wait_qr_code: bool = False,
    ) -> dict:
        """
        Updates the webhook URL and restarts the session.

        Parameters:
        - webhook_url (str): The new webhook URL.
        - api_url (str): Base API URL.
        - api_key (str): API authentication key.
        - session_id (str): Session ID for the WhatsApp API.
        - wait_qr_code (bool): Whether to wait for a QR code. Defaults to False.

        Returns:
        - dict: Status of the operation.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        try:
            # Close the current session
            close_session_url = f"{api_url}/api/{session_id}/close-session"
            close_response = WppconnectAPI.send_request(
                url=close_session_url, method="POST", headers=headers, data={}
            )

            if close_response.get("error"):
                WppconnectAPI.logger.warning(
                    f"Failed to close session: {close_response.get('error')}"
                )

            # Start a new session with the updated webhook
            start_session_url = f"{api_url}/api/{session_id}/start-session"
            data = {"webhook": webhook_url, "waitQrCode": wait_qr_code}

            # log the start session request
            start_response = WppconnectAPI.send_request(
                url=start_session_url, data=data, method="POST", headers=headers
            )

            # log the start session response
            # WppconnectAPI.logger.warning(f"Start session response: {start_response}")
            if start_response.get("error"):
                error = f"Failed to update webhook URL: {start_response.get('error')}"
                WppconnectAPI.logger.error(error)
                return {"status": "error", "message": error}

            return {"status": "success", "message": "Webhook URL updated successfully"}

        except Exception as e:
            error = f"An error occurred while updating the webhook URL: {str(e)}"
            WppconnectAPI.logger.error(error)
            return {"status": "error", "message": error}
