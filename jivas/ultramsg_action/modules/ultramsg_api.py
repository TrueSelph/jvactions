"""API module for interacting with the Ultramsg API."""

import logging
import os
import traceback
import uuid
from typing import Optional

import requests


class UltramsgAPI:
    """Class for interacting with the Ultramsg API."""

    logger = logging.getLogger(__name__)

    @staticmethod
    def parse_inbound_message(request: dict) -> dict:
        """Parses message request payload and returns extracted values"""

        """ payload structure

        {'event_type': 'message_received', 'instanceId': '', 'id': '', 'referenceId': '', 'hash': '',
        'data': {
            'id': '',
            'from': '',
            'to': '',
            'author': '',
            'pushname': '',
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
            'time': 1234567890,
            }
        }

        """

        data = {}

        if request:

            data["message_id"] = request["data"]["id"]
            data["instance_id"] = request["instanceId"]
            data["event_type"] = request["event_type"]
            data["time"] = request["data"]["time"]
            data["author"] = request["data"]["author"]
            data["from_self"] = request["data"]["fromMe"]
            data["sender_name"] = request.get("data", {}).get("pushname", "")
            data["sender_number"] = str(request["data"]["from"].replace("@c.us", ""))
            data["agent_number"] = str(request["data"]["to"].replace("@c.us", ""))
            data["parent_message"] = request["data"].get("quotedMsg", "")
            data["message_type"] = request["data"].get("type", "unknown")
            data["body"] = request["data"]["body"]
            data["media"] = request.get("data", {}).get("media", "")
            data["location"] = request.get("data", {}).get("location", "")
            # add caption to media messages if present
            if data["message_type"] != "chat":
                data["caption"] = data["body"]

        return data

    @staticmethod
    def send_rest_request(
        url: str,
        data: Optional[dict] = None,
        method: str = "POST",
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict:
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
            response = requests.request(
                method=method, url=url, headers=headers, json=data, params=params
            )

            # Check if the response is successful
            if response.status_code // 100 == 2:  # Status codes 200-299
                result = response.json()

                if result and result.get("error", False):
                    UltramsgAPI.logger.error(
                        f"Ultramsg request error: {result.get('error', False)}"
                    )

                return result
            else:
                error = f"Request failed with status code {response.status_code}, response: {response.text}"
                UltramsgAPI.logger.error(error)
                return {"error": error}

        except requests.exceptions.RequestException as e:
            # Handle broader request exceptions
            error = f"error while executing ultramsg call: {str(e)}"
            UltramsgAPI.logger.error(error)
            return {"error": error}

    @staticmethod
    def send_text_message(
        phone_number: str, message: str, api_url: str, api_key: str, msg_id: str = ""
    ) -> dict:
        """
        Sends a text message to a phone number using the Ultramsg API.

        :param phone_number: The phone number to send the message to.
        :param message: The message to send.
        :param api_url: The URL of the Ultramsg API.
        :param api_key: The API key for accessing the Ultramsg API.
        :param msg_id: The message ID to associate with the message.
        """

        data = {"token": api_key, "to": phone_number, "body": message, "msgId": msg_id}

        return UltramsgAPI.send_rest_request(url=f"{api_url}/messages/chat", data=data)

    @staticmethod
    def send_image(
        phone_number: str,
        media_url: str,
        api_url: str,
        api_key: str,
        caption: str = "",
        msg_id: str = "",
    ) -> dict:
        """
        Sends an image message to a phone number using the Ultramsg API.

        :param phone_number: The phone number to send the message to.
        :param media_url: The URL of the image to send.
        :param api_url: The URL of the Ultramsg API.
        :param api_key: The API key for accessing the Ultramsg API.
        :param caption: The caption to include with the image.
        :param msg_id: The message ID to associate with the message.
        """

        data = {
            "token": api_key,
            "to": phone_number,
            "image": media_url,
            "caption": caption,
            "msgId": msg_id,
        }

        return UltramsgAPI.send_rest_request(url=f"{api_url}/messages/image", data=data)

    @staticmethod
    def send_sticker(
        phone_number: str, media_url: str, api_url: str, api_key: str, msg_id: str = ""
    ) -> dict:
        """
        Sends a sticker message to a phone number using the Ultramsg API.

        :param phone_number: The phone number to send the message to.
        :param media_url: The URL of the sticker to send.
        :param api_url: The URL of the Ultramsg API.
        :param api_key: The API key for accessing the Ultramsg API.
        :param msg_id: The message ID to associate with the message.
        """

        data = {
            "token": api_key,
            "to": phone_number,
            "sticker": media_url,
            "msgId": msg_id,
        }

        return UltramsgAPI.send_rest_request(
            url=f"{api_url}/messages/sticker", data=data
        )

    @staticmethod
    def send_document(
        phone_number: str,
        media_url: str,
        api_url: str,
        api_key: str,
        filename: str,
        caption: str = "",
        msg_id: str = "",
    ) -> dict:
        """
        Sends a document message to a phone number using the Ultramsg API.

        :param phone_number: The phone number to send the message to.
        :param media_url: The URL of the document to send.
        :param api_url: The URL of the Ultramsg API.
        :param api_key: The API key for accessing the Ultramsg API.
        :param filename: The name of the document file.
        :param caption: The caption to include with the document.
        :param msg_id: The message ID to associate with the message.
        """

        data = {
            "token": api_key,
            "to": phone_number,
            "filename": filename,
            "document": media_url,
            "caption": caption,
            "msgId": msg_id,
        }

        return UltramsgAPI.send_rest_request(
            url=f"{api_url}/messages/document", data=data
        )

    @staticmethod
    def send_audio(
        phone_number: str, media: str, api_url: str, api_key: str, msg_id: str = ""
    ) -> dict:
        """
        Sends an audio message to a phone number using the Ultramsg API.

        :param phone_number: The phone number to send the message to.
        :param media: The URL of the audio file to send.
        :param api_url: The URL of the Ultramsg API.
        :param api_key: The API key for accessing the Ultramsg API.
        :param msg_id: The message ID to associate with the message.
        """

        data = {"token": api_key, "to": phone_number, "audio": media, "msgId": msg_id}

        return UltramsgAPI.send_rest_request(url=f"{api_url}/messages/audio", data=data)

    @staticmethod
    def send_voice(
        phone_number: str, media: str, api_url: str, api_key: str, msg_id: str = ""
    ) -> dict:
        """
        Sends a voice message to a phone number using the Ultramsg API.

        :param phone_number: The phone number to send the message to.
        :param media: The URL of the voice message to send.
        :param api_url: The URL of the Ultramsg API.
        :param api_key: The API key for accessing the Ultramsg API.
        :param msg_id: The message ID to associate with the message.
        """

        data = {"token": api_key, "to": phone_number, "audio": media, "msgId": msg_id}

        return UltramsgAPI.send_rest_request(url=f"{api_url}/messages/voice", data=data)

    @staticmethod
    def send_video(
        phone_number: str,
        media_url: str,
        api_url: str,
        api_key: str,
        caption: str = "",
        msg_id: str = "",
    ) -> dict:
        """
        Sends a video message to a phone number using the Ultramsg API.

        :param phone_number: The phone number to send the message to.
        :param media_url: The URL of the video to send.
        :param api_url: The URL of the Ultramsg API.
        :param api_key: The API key for accessing the Ultramsg API.
        :param caption: The caption to include with the video.
        :param msg_id: The message ID to associate with the message.
        """

        data = {
            "token": api_key,
            "to": phone_number,
            "video": media_url,
            "caption": caption,
            "msgId": msg_id,
        }

        return UltramsgAPI.send_rest_request(url=f"{api_url}/messages/video", data=data)

    @staticmethod
    def send_contact(
        phone_number: str, contact: str, api_url: str, api_key: str, msg_id: str = ""
    ) -> dict:
        """
        Sends a contact message to a phone number using the Ultramsg API.

        :param phone_number: The phone number to send the message to.
        :param contact: The contact information to send.
        :param api_url: The URL of the Ultramsg API.
        :param api_key: The API key for accessing the Ultramsg API.
        :param msg_id: The message ID to associate with the message.
        """

        data = {
            "token": api_key,
            "to": phone_number,
            "contact": contact,
            "msgId": msg_id,
        }

        return UltramsgAPI.send_rest_request(
            url=f"{api_url}/messages/contact", data=data
        )

    @staticmethod
    def send_location(
        phone_number: str,
        address: str,
        lat: float,
        lng: float,
        api_url: str,
        api_key: str,
        msg_id: str = "",
    ) -> dict:
        """
        Sends a location message to a phone number using the Ultramsg API.

        :param phone_number: The phone number to send the message to.
        :param address: The address of the location to send.
        :param lat: The latitude of the location.
        :param lng: The longitude of the location.
        :param api_url: The URL of the Ultramsg API.
        :param api_key: The API key for accessing the Ultramsg API.
        :param msg_id: The message ID to associate with the message.
        """

        data = {
            "token": api_key,
            "to": phone_number,
            "address": address,
            "lat": lat,
            "lng": lng,
            "msgId": msg_id,
        }

        return UltramsgAPI.send_rest_request(
            url=f"{api_url}/messages/location", data=data
        )

    @staticmethod
    def send_vcard(
        phone_number: str, vcard: str, api_url: str, api_key: str, msg_id: str = ""
    ) -> dict:
        """
        Sends a vcard message to a phone number using the Ultramsg API.

        :param phone_number: The phone number to send the message to.
        :param vcard: The vcard information to send.
        :param api_url: The URL of the Ultramsg API.
        :param api_key: The API key for accessing the Ultramsg API.
        :param msg_id: The message ID to associate with the message.
        """

        data = {"token": api_key, "to": phone_number, "vcard": vcard, "msgId": msg_id}

        return UltramsgAPI.send_rest_request(url=f"{api_url}/messages/vcard", data=data)

    @staticmethod
    def send_reaction(msg_id: str, reaction: str, api_url: str, api_key: str) -> dict:
        """
        Sends a reaction to a message using the Ultramsg API.

        :param msg_id: The ID of the message to react to.
        :param reaction: The reaction to send.
        :param api_url: The URL of the Ultramsg API.
        :param api_key: The API key for accessing the Ultramsg API.
        """

        data = {"token": api_key, "msgId": msg_id, "emoji": reaction}

        return UltramsgAPI.send_rest_request(
            url=f"{api_url}/messages/reaction", data=data
        )

    @staticmethod
    def delete_message(
        phone_number: str, msg_id: str, api_url: str, api_key: str
    ) -> dict:
        """
        Deletes a message using the Ultramsg API.

        :param msg_id: The ID of the message to delete.
        :param api_url: The URL of the Ultramsg API.
        :param api_key: The API key for accessing the Ultramsg API.
        """

        data = {"token": api_key, "msgId": msg_id}

        return UltramsgAPI.send_rest_request(
            url=f"{api_url}/messages/delete", data=data
        )

    @staticmethod
    def send_by_status(
        phone_number: str, status: str, api_url: str, api_key: str
    ) -> dict:
        """
        Sends messages based on status using the Ultramsg API.

        :param status: The status of the messages to resend.
        :param api_url: The URL of the Ultramsg API.
        :param api_key: The API key for accessing the Ultramsg API.
        """

        data = {"token": api_key, "status": status}

        return UltramsgAPI.send_rest_request(
            url=f"{api_url}/messages/resendByStatus", data=data
        )

    @staticmethod
    def send_by_id(phone_number: str, id: str, api_url: str, api_key: str) -> dict:
        """
        Resends a message based on ID using the Ultramsg API.

        :param id: The ID of the message to resend.
        :param api_url: The URL of the Ultramsg API.
        :param api_key: The API key for accessing the Ultramsg API.
        """

        data = {"token": api_key, "id": id}

        return UltramsgAPI.send_rest_request(
            url=f"{api_url}/messages/resendById", data=data
        )

    @staticmethod
    def clear_messages(
        phone_number: str, status: str, api_url: str, api_key: str
    ) -> dict:
        """
        Clears messages based on status using the Ultramsg API.

        :param status: The status of the messages to clear.
        :param api_url: The URL of the Ultramsg API.
        :param api_key: The API key for accessing the Ultramsg API.
        """

        data = {"token": api_key, "status": status}

        return UltramsgAPI.send_rest_request(url=f"{api_url}/messages/clear", data=data)

    @staticmethod
    def get_messages(
        phone_number: str,
        page: int,
        limit: int,
        status: str,
        sort: str,
        api_url: str,
        api_key: str,
    ) -> dict:
        """
        Gets messages based on status using the Ultramsg API.

        :param page: The page number to get messages from.
        :param limit: The number of messages to get per page.
        :param status: The status of the messages to get.
        :param sort: The order in which to sort the messages.
        :param api_url: The URL of the Ultramsg API.
        :param api_key: The API key for accessing the Ultramsg API.
        """

        data = {
            "token": api_key,
            "page": page,
            "limit": limit,
            "status": status,
            "sort": sort,
        }

        return UltramsgAPI.send_rest_request(url=f"{api_url}/messages", data=data)

    @staticmethod
    def get_statistics(phone_number: str, api_url: str, api_key: str) -> dict:
        """
        Gets message statistics using the Ultramsg API.

        :param phone_number: The phone number to get statistics for.
        :param api_url: The URL of the Ultramsg API.
        :param api_key: The API key for accessing the Ultramsg API.
        """

        data = {"token": api_key}

        return UltramsgAPI.send_rest_request(
            url=f"{api_url}/messages/statistics", data=data
        )

    @staticmethod
    def get_instance_status(phone_number: str, api_url: str, api_key: str) -> dict:
        """Gets the status of the instance."""
        data = {"token": api_key}

        return UltramsgAPI.send_rest_request(
            url=f"{api_url}/instance/status", data=data
        )

    @staticmethod
    def get_qr_image(phone_number: str, api_url: str, api_key: str) -> dict:
        """Gets the QR image."""
        data = {"token": api_key}

        return UltramsgAPI.send_rest_request(url=f"{api_url}/instance/qr", data=data)

    @staticmethod
    def get_authentication_qr(phone_number: str, api_url: str, api_key: str) -> dict:
        """Gets the QR image for authentication."""
        data = {"token": api_key}

        return UltramsgAPI.send_rest_request(
            url=f"{api_url}/instance/qrCode", data=data
        )

    @staticmethod
    def get_connected_phones(phone_number: str, api_url: str, api_key: str) -> dict:
        """Gets all connected phones."""
        data = {"token": api_key}

        return UltramsgAPI.send_rest_request(url=f"{api_url}/instance/me", data=data)

    @staticmethod
    def get_instance_settings(phone_number: str, api_url: str, api_key: str) -> dict:
        """Gets the current instance settings."""
        data = {"token": api_key}

        return UltramsgAPI.send_rest_request(
            url=f"{api_url}/instance/settings", params=data, method="GET"
        )

    @staticmethod
    def logout(phone_number: str, api_url: str, api_key: str) -> dict:
        """Logs out of WhatsApp."""
        data = {"token": api_key}

        return UltramsgAPI.send_rest_request(
            url=f"{api_url}/instance/logout", data=data
        )

    @staticmethod
    def restart_instance(phone_number: str, api_url: str, api_key: str) -> dict:
        """Restarts the instance."""
        data = {"token": api_key}

        return UltramsgAPI.send_rest_request(
            url=f"{api_url}/instance/restart", data=data
        )

    @staticmethod
    def update_instance_settings(
        webhook_url: str,
        send_delay: int,
        webhook_message_received: str,
        webhook_message_create: str,
        webhook_message_ack: str,
        webhook_message_download_media: str,
        api_url: str,
        api_key: str,
    ) -> dict:
        """Updates the instance settings.

        :param webhook_url: The URL of the webhook.
        :param send_delay: The delay between sending messages.
        :param webhook_message_received: The webhook message received.
        :param webhook_message_create: The webhook message create.
        :param webhook_message_ack: The webhook message ack.
        :param webhook_message_download_media: The webhook message download media.
        :param api_url: The URL of the Ultramsg API.
        :param api_key: The API key for accessing the Ultramsg API.
        """

        data = {
            "token": api_key,
            "sendDelay": send_delay,
            "webhook_url": webhook_url,
            "webhook_message_received": webhook_message_received,
            "webhook_message_create": webhook_message_create,
            "webhook_message_ack": webhook_message_ack,
            "webhook_message_download_media": webhook_message_download_media,
        }

        return UltramsgAPI.send_rest_request(
            url=f"{api_url}/instance/settings", data=data
        )

    @staticmethod
    def clear_settings(phone_number: str, api_url: str, api_key: str) -> dict:
        """Clears all instance settings."""
        data = {"token": api_key}

        return UltramsgAPI.send_rest_request(url=f"{api_url}/instance/clear", data=data)

    @staticmethod
    def download_media(media_url: str, filename: str = "") -> dict:
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
            mime_type = response.headers.get("Content-Type", "")

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
                UltramsgAPI.logger.debug("returned media binary")
                return {
                    "success": {"mime_type": mime_type, "content": response.content}
                }

        except requests.exceptions.RequestException as e:
            UltramsgAPI.logger.error(f"an exception occurred, {traceback.format_exc()}")
            return {"error": str(e)}

    @staticmethod
    def mark_as_read(phone_number: str, instance_id: str, api_key: str) -> dict:
        """Marks message as read."""
        data = {"token": api_key, "chatId": phone_number}

        return UltramsgAPI.send_rest_request(
            url=f"https://api.ultramsg.com/{instance_id}/chats/read", data=data
        )

    @staticmethod
    def api_transcribe_audio_url(
        audio_url: str, api_url: str = "", data: Optional[dict] = None
    ) -> dict:
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
        status = None
        response = None
        result = None

        # download the audio file
        filename = str(uuid.uuid4())
        UltramsgAPI.download_media(audio_url, filename)

        try:
            # Define the headers for the HTTP request
            headers: dict = {}

            # prep the audio file
            with open(filename, "rb") as audio_file:
                files = [("audio", (filename, audio_file, "audio/mp3"))]

            # delete the audio file
            if os.path.exists(filename):
                os.remove(filename)

            response = requests.request(
                "POST", api_url, headers=headers, data=data, files=files
            )

            # Check if request was successful
            if response.status_code == 201:
                result = response.json()
                status = "success"
            else:
                result = {
                    "message": f"Error: {response.status_code} - {response.reason}"
                }
                status = "error"
        except Exception as e:
            UltramsgAPI.logger.error(f"an exception occurred, {traceback.format_exc()}")
            result = {"message": f"Error: {str(e)}"}
            status = "error"

        return {status: result}
