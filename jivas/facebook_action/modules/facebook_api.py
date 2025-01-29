"""This module provides the FacebookAPI class for interacting with the Facebook Graph API."""

import logging
import mimetypes
import os
import random
import string
import traceback
from typing import Optional, Union

import requests


class FacebookAPI:
    """
    A class to interact with the Facebook Graph API for various actions such as sending messages,
    updating webhooks, and managing Facebook pages.

    """

    logger = logging.getLogger(__name__)

    # Messenger action

    @staticmethod
    def parse_verification_request(
        request: dict, verify_token: str
    ) -> Union[str, dict[str, Union[str, int]]]:
        """Parses verification request payload and returns the challenge value if the token is valid."""
        try:
            hub_mode = request.get("hub.mode")  # QueryParams acts like a dictionary
            hub_verify_token = request.get("hub.verify_token")
            hub_challenge = request.get("hub.challenge")

            # Check if the 'hub.verify_token' matches the expected token and mode is 'subscribe'
            if hub_verify_token == verify_token and hub_mode == "subscribe":
                return hub_challenge if hub_challenge is not None else ""

            return {"message": "Invalid token or mode", "code": 403}

        except Exception as e:
            FacebookAPI.logger.error(
                f"unable to process verification request {traceback.format_exc()}"
            )
            return {"error": str(e)}

    @staticmethod
    def update_webhook(
        app_secret: str, app_id: str, api_url: str, webhook: str, verify_token: str
    ) -> dict:
        """
        Update Facebook webhook.
        :param app_secret: The app secret for your Facebook app.
        :param app_id: The App ID of your Facebook app.
        :param webhook: The new webhook URL.
        :param verify_token: The token used for verifying the callback URL.
        :return: A dictionary containing the response from the API or an error message.
        """
        url = f"{str(api_url)}{str(app_id)}/subscriptions"
        params = {
            "access_token": str(app_id) + "|" + str(app_secret),
        }
        data = {
            "object": "page",
            "callback_url": webhook,
            "fields": "messages",
            "verify_token": verify_token,
            "include_values": "true",
        }

        response = requests.post(url, params=params, json=data)

        if response.status_code == 200:
            return response.json()
        else:
            FacebookAPI.logger.error(f"Error: {response.status_code} - {response.text}")
            return {
                "error": f"Facebook API: Unexpected status code: {response.status_code}",
                "details": response.json() if response.content else None,
            }

    @staticmethod
    def parse_inbound_message(request: dict) -> dict:
        """Parses message request payload and returns extracted values."""
        payload = {}
        try:
            entry = request["entry"][0]
            page_id = request["entry"][0]["id"]
            sender_id = ""
            message_type = ""
            message = ""
            sender_name = ""
            attachments = []
            caption = ""
            parent_message_id = ""

            if "changes" in entry:
                sender_id = entry["changes"][0]["value"]["from"]["id"]
                sender_name = entry["changes"][0]["value"]["from"]["name"]
                message_type = entry["changes"][0]["value"]["item"]
                message = entry["changes"][0]["value"].get("message")
                if not message:
                    message = entry["changes"][0]["value"].get("reaction_type")
            elif "messaging" in entry:
                sender_id = entry["messaging"][0]["sender"]["id"]
                message_type = "message"
                message = entry["messaging"][0]["message"].get("text")
                attachments = entry["messaging"][0]["message"].get("attachments")

            payload = {
                "sender_name": sender_name,
                "sender_id": sender_id,
                "page_id": page_id,
                "message_type": message_type,
                "message": message,
                "attachments": attachments,
                "caption": caption,
                "data": request,
                "parent_message_id": parent_message_id,
            }

        except Exception as e:
            FacebookAPI.logger.error(f"Error: unable to process inbound message. {e}")

        return payload

    @staticmethod
    def send_text_message(
        recipient_id: str, message: str, api_url: str, page_id: str, access_token: str
    ) -> dict:
        """Send text message to a Facebook user via Messenger."""
        url = f"{api_url}{page_id}/messages"
        headers = {"Content-Type": "application/json"}
        data = {
            "recipient": {"id": str(recipient_id)},
            "messaging_type": "RESPONSE",
            "message": {"text": message},
        }
        params = {"access_token": access_token}

        response = requests.post(url=url, headers=headers, json=data, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            FacebookAPI.logger.error(f"Error: {response.status_code} - {response.text}")
            return {
                "error": f"Facebook API: Unexpected status code: {response.status_code}",
                "details": response.json() if response.content else None,
            }

    @staticmethod
    def send_media(
        recipient_id: str,
        media_url: str,
        media_type: str,
        api_url: str,
        page_id: str,
        access_token: str,
    ) -> dict:
        """
        Send a media message (audio, image, video, or document) to a Facebook user via Messenger.

        Args:
            recipient_id (str): The recipient's Facebook user ID.
            media_url (str): The URL of the media file.
            media_type (MediaType): The type of media to send (audio, image, video, or file).
            api_url (str): The base URL of the Facebook Graph API.
            page_id (str): The Facebook Page ID.
            access_token (str): The Page Access Token.

        Returns:
            dict: The API response as a JSON object or error details.
        """
        url = f"{api_url}{page_id}/messages"
        headers = {"Content-Type": "application/json"}
        data = {
            "recipient": {"id": recipient_id},
            "messaging_type": "RESPONSE",
            "message": {
                "attachment": {
                    "type": media_type,
                    "payload": {"url": media_url, "is_reusable": True},
                }
            },
        }

        params = {"access_token": access_token}

        response = requests.post(url=url, headers=headers, json=data, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            FacebookAPI.logger.error(f"Error: {response.status_code} - {response.text}")
            return {
                "error": f"Facebook API: Unexpected status code: {response.status_code}",
                "details": response.json() if response.content else None,
            }

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

            # Get the content type from the response headers
            mime_type = response.headers.get("Content-Type")

            if filename:
                # utiilse the filename if provided
                with open(filename, "wb") as file:
                    file.write(response.content)

                if os.path.exists(filename):
                    message = f"media saved to {filename} successfully"
                    FacebookAPI.logger.debug(message)
                    return {"success": message}
                else:
                    message = f"unable to save media to {filename}"
                    FacebookAPI.logger.error(message)
                    return {"error": message}

            else:
                # otherwise return the data directly
                FacebookAPI.logger.debug("returned media binary")
                return {
                    "success": {"mime_type": mime_type, "content": response.content}
                }

        except requests.exceptions.RequestException as e:
            FacebookAPI.logger.error(f"an exception occurred, {traceback.format_exc()}")
            return {"error": str(e)}

    # Facebook action

    @staticmethod
    def get_user_info(access_token: str, api_url: str, fields: str = "id,name") -> dict:
        """
        Fetches the user field from the Facebook Graph API.

        :param access_token: The access token for the Facebook Graph API.
        :return: A dictionary containing user information fields, or an error message.
        """
        url = f"{str(api_url)}me"
        params = {"fields": fields, "access_token": access_token}

        response = requests.get(url, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            FacebookAPI.logger.error(f"Error: {response.status_code} - {response.text}")
            return {
                "error": f"Facebook API: Unexpected status code: {response.status_code}",
                "details": response.json() if response.content else None,
            }

    @staticmethod
    def list_all_pages(access_token: str, api_url: str, limit: int = 100) -> list:
        """
        Lists all pages managed by the user.

        :param access_token: The access token for the Facebook Graph API.
        :param limit: The number of pages to retrieve in one call (default is 100).
        :return: A list of dictionaries containing page details, or an error message.
        """
        all_pages = []
        url = f"{api_url}me/accounts"
        params = {"access_token": str(access_token), "limit": str(limit)}

        while True:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                json_data = response.json()
                all_pages.extend(json_data.get("data", []))  # Ensure returning a list

                next_page = json_data.get("paging", {}).get("next")
                if next_page:
                    url = next_page
                    params = {}
                else:
                    break
            else:
                FacebookAPI.logger.error(
                    f"Error: {response.status_code} - {response.text}"
                )
                return []

        return all_pages

    @staticmethod
    def get_page_details(
        access_token: str,
        page_id: str,
        api_url: str,
        fields: str = "id,name,about,fan_count,access_token",
    ) -> dict:
        """
        Fetches details of a Facebook page.

        :param access_token: The access token for the Facebook Graph API.
        :param page_id: The ID of the Facebook page.
        :return: A dictionary containing page details, or an error message.
        """
        url = f"{str(api_url)}{str(page_id)}"
        params = {"access_token": access_token, "fields": fields}

        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            FacebookAPI.logger.error(f"Error: {response.status_code} - {response.text}")
            return {
                "error": f"Facebook API: Unexpected status code: {response.status_code}",
                "details": response.json() if response.content else None,
            }

    @staticmethod
    def post_message_to_page(
        access_token: str, page_id: str, api_url: str, message: str
    ) -> dict:
        """
        Posts a message to a Facebook page.

        :param access_token: The access token for the Facebook page.
        :param page_id: The ID of the Facebook page.
        :param message: The message to be posted.
        :return: A dictionary containing the post ID, or an error message.
        """
        url = f"{api_url}{page_id}/feed"
        params = {"message": message, "access_token": access_token}

        response = requests.post(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            FacebookAPI.logger.error(f"Error: {response.status_code} - {response.text}")
            return {
                "error": f"Facebook API: Unexpected status code: {response.status_code}",
                "details": response.json() if response.content else None,
            }

    @staticmethod
    def get_page_posts(
        access_token: str, page_id: str, api_url: str, limit: int = 10
    ) -> Union[list, dict]:
        """
        Retrieves posts from a Facebook page. Most recent post first.

        :param access_token: The access token for Facebook page.
        :param page_id: The ID of the Facebook page.
        :param limit: The number of posts to retrieve (default is 10).
        :return: A list of posts, or an error message.
        """
        url = f"{api_url}{page_id}/posts"
        params = {"access_token": str(access_token), "limit": str(limit)}

        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            FacebookAPI.logger.error(f"Error: {response.status_code} - {response.text}")
            return {
                "error": f"Facebook API: Unexpected status code: {response.status_code}",
                "details": response.json() if response.content else None,
            }

    @staticmethod
    def get_single_post(access_token: str, post_id: str, api_url: str) -> dict:
        """
        Retrieves a single post from a Facebook page by post ID.

        :param access_token: The access token for Facebook page.
        :param post_id: The ID of the Facebook post.
        :param api_url: The base URL of the Facebook Graph API.
        :return: The post data, or an error message.
        """
        url = f"{api_url}{post_id}"
        params = {"access_token": access_token}

        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            FacebookAPI.logger.error(f"Error: {response.status_code} - {response.text}")
            return {
                "error": f"Facebook API: Unexpected status code: {response.status_code}",
                "details": response.json() if response.content else None,
            }

    @staticmethod
    def comment_on_post(
        access_token: str, post_id: str, api_url: str, message: str
    ) -> dict:
        """
        Comments on a Facebook post.

        :param access_token: The access token for the Facebook page.
        :param post_id: The ID of the post to comment on.
        :param message: The comment message.
        :return: A dictionary containing the comment ID, or an error message.
        """
        url = f"{api_url}{post_id}/comments"
        params = {"message": message, "access_token": access_token}

        response = requests.post(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            FacebookAPI.logger.error(f"Error: {response.status_code} - {response.text}")
            return {
                "error": f"Facebook API: Unexpected status code: {response.status_code}",
                "details": response.json() if response.content else None,
            }

    @staticmethod
    def post_images_to_page(
        access_token: str, page_id: str, api_url: str, image_urls: list, caption: str
    ) -> dict:
        """
        Uploads multiple photos to a Facebook page using URLs with an optional caption.

        :param access_token: The access token for the Facebook page.
        :param page_id: The ID of the Facebook page.
        :param api_url: The base URL of the Facebook Graph API.
        :param image_urls: A list of URLs of the photos.
        :param caption: The caption for the photos.
        :return: A dictionary containing the post ID, or an error message.
        """

        image_ids = []

        for image_url in image_urls:
            url = f"{api_url}{page_id}/photos"
            params = {
                "access_token": access_token,
                "url": image_url,
                "published": "false",  # Delay publishing until all photos are uploaded
            }

            response = requests.post(url, params=params)
            if response.status_code == 200:
                image_ids.append(response.json().get("id"))

        # Create a post with the uploaded images
        post_url = f"{api_url}{page_id}/feed"
        post_params = {
            "access_token": access_token,
            "message": caption,
            "attached_media": [{"media_fbid": image_id} for image_id in image_ids],
        }

        post_response = requests.post(post_url, json=post_params)
        if post_response.status_code == 200:
            return post_response.json()
        else:
            FacebookAPI.logger.error(
                f"Error: {post_response.status_code} - {post_response.text}"
            )
            return {
                "error": f"Facebook API: Unexpected status code: {post_response.status_code}",
                "details": post_response.json() if post_response.content else None,
            }

    @staticmethod
    def post_videos_to_page(
        access_token: str,
        page_id: str,
        api_url: str,
        title: str,
        caption: str,
        video_urls: list,
    ) -> dict:
        """
        Uploads multiple videos to a Facebook page using URLs with an optional caption.

        :param access_token: The access token for the Facebook page.
        :param page_id: The ID of the Facebook page.
        :param api_url: The base URL of the Facebook Graph API.
        :param title: The title of the video.
        :param caption: The caption for the video.
        :param video_urls: A list of URLs of the videos.
        :return: A dictionary containing the post ID, or an error message.
        """

        video_ids = []
        for video_url in video_urls:
            url = f"{api_url}{page_id}/videos"

            params = {
                "access_token": access_token,
                "title": title,
                "file_url": video_url,
            }

            response = requests.post(url, params=params)
            if response.status_code == 200:
                video_ids.append(response.json().get("id"))

        post_url = f"{api_url}{page_id}/feed"
        post_params = {
            "access_token": access_token,
            "message": caption,
            "attached_media": [{"media_fbid": image_id} for image_id in video_ids],
        }

        post_response = requests.post(post_url, json=post_params)
        if post_response.status_code == 200:
            return post_response.json()
        else:
            FacebookAPI.logger.error(
                f"Error: {post_response.status_code} - {post_response.text}"
            )
            return {
                "error": f"Facebook API: Unexpected status code: {post_response.status_code}",
                "details": post_response.json() if post_response.content else None,
            }

    @staticmethod
    def get_mime_type(
        file_path: Optional[str] = None,
        url: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> Optional[dict]:
        """Determine the MIME type of a file or URL and categorize it into common file types."""
        detected_mime_type = None

        if file_path:
            # Use mimetypes to guess MIME type based on file extension
            detected_mime_type, _ = mimetypes.guess_type(file_path)
        elif url:
            # Make a HEAD request to get the Content-Type header
            try:
                response = requests.head(url, allow_redirects=True)
                detected_mime_type = response.headers.get("Content-Type")
            except requests.RequestException as e:
                print(f"Error making HEAD request: {e}")
                return None
        else:
            # Fallback to initial MIME type if provided
            detected_mime_type = mime_type

        # MIME type categories
        image_mime_types = [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/bmp",
            "image/webp",
            "image/tiff",
            "image/svg+xml",
            "image/x-icon",
            "image/heic",
            "image/heif",
            "image/x-raw",
        ]
        document_mime_types = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "text/plain",
            "text/csv",
            "text/html",
            "application/rtf",
            "application/x-tex",
            "application/vnd.oasis.opendocument.text",
            "application/vnd.oasis.opendocument.spreadsheet",
            "application/epub+zip",
            "application/x-mobipocket-ebook",
            "application/x-fictionbook+xml",
            "application/x-abiword",
            "application/vnd.apple.pages",
            "application/vnd.google-apps.document",
        ]
        audio_mime_types = [
            "audio/mpeg",
            "audio/wav",
            "audio/ogg",
            "audio/flac",
            "audio/aac",
            "audio/mp3",
            "audio/webm",
            "audio/amr",
            "audio/midi",
            "audio/x-m4a",
            "audio/x-realaudio",
            "audio/x-aiff",
            "audio/x-wav",
            "audio/x-matroska",
        ]
        video_mime_types = [
            "video/mp4",
            "video/mpeg",
            "video/ogg",
            "video/webm",
            "video/quicktime",
            "video/x-msvideo",
            "video/x-matroska",
            "video/x-flv",
            "video/x-ms-wmv",
            "video/3gpp",
            "video/3gpp2",
            "video/h264",
            "video/h265",
            "video/x-f4v",
            "video/avi",
        ]

        # Handle cases where MIME type cannot be detected
        if detected_mime_type is None or detected_mime_type == "binary/octet-stream":
            if file_path:
                _, file_extension = os.path.splitext(file_path)
            elif url:
                _, file_extension = os.path.splitext(url)
            else:
                file_extension = ""

            detected_mime_type = mimetypes.types_map.get(file_extension.lower())

        # Categorize MIME type
        if detected_mime_type in image_mime_types:
            return {"file_type": "image", "mime": detected_mime_type}
        elif detected_mime_type in document_mime_types:
            return {"file_type": "document", "mime": detected_mime_type}
        elif detected_mime_type in audio_mime_types:
            return {"file_type": "audio", "mime": detected_mime_type}
        elif detected_mime_type in video_mime_types:
            return {"file_type": "video", "mime": detected_mime_type}
        else:
            print(f"Unsupported MIME Type: {detected_mime_type}")
            return {"file_type": "unknown", "mime": detected_mime_type}

    @staticmethod
    def post_media_to_page(
        access_token: str, page_id: str, api_url: str, caption: str, media_urls: list
    ) -> dict:
        """
        Posts media (images or videos) to a Facebook page using URLs with an optional caption.

        :param access_token: The access token for the Facebook page.
        :param page_id: The ID of the Facebook page.
        :param api_url: The base URL of the Facebook Graph API.
        :param caption: The caption for the media.
        :param media_urls: A list of URLs of the media.
        :return: A dictionary containing the post ID, or an error message.
        """

        media_ids = []
        for media_url in media_urls:
            mime_info = FacebookAPI.get_mime_type(url=media_url["url"])
            media_type = mime_info.get("file_type") if mime_info else None
            if media_type == "video":
                url = f"{api_url}{page_id}/videos"

                params = {"access_token": access_token, "file_url": media_url}
            elif media_type == "image":
                url = f"{api_url}{page_id}/photos"
                params = {
                    "access_token": access_token,
                    "url": media_url,
                    "published": "false",  # Delay publishing until all photos are uploaded
                }
            if params and url:
                response = requests.post(url, params=params)
                if response.status_code == 200:
                    media_ids.append(response.json().get("id"))

        post_url = f"{api_url}{page_id}/feed"
        post_params = {
            "access_token": access_token,
            "message": caption,
            "attached_media": [{"media_fbid": media_id} for media_id in media_ids],
        }

        post_response = requests.post(post_url, json=post_params)
        if post_response.status_code == 200:
            return post_response.json()
        else:
            FacebookAPI.logger.error(
                f"Error: {post_response.status_code} - {post_response.text}"
            )
            return {
                "error": f"Facebook API: Unexpected status code: {post_response.status_code}",
                "details": post_response.json() if post_response.content else None,
            }

    @staticmethod
    def get_post_comments(
        access_token: str, post_id: str, api_url: str, limit: int = 10
    ) -> Union[list, dict]:
        """
        Retrieves comments on a Facebook post.

        :param access_token: The access token for the Facebook page.
        :param post_id: The ID of the post to get comments from.
        :param limit: The number of comments to retrieve (default is 10).
        :return: A list of comments, or an error message.
        """

        url = f"{api_url}{post_id}/comments"
        params = {"access_token": access_token, "limit": str(limit)}

        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            FacebookAPI.logger.error(f"Error: {response.status_code} - {response.text}")
            return {
                "error": f"Facebook API: Unexpected status code: {response.status_code}",
                "details": response.json() if response.content else None,
            }

    @staticmethod
    def reply_to_comment(
        access_token: str, comment_id: str, api_url: str, message: str
    ) -> dict:
        """
        Replies to a comment on a Facebook post.

        :param access_token: The access token for the Facebook Graph API.
        :param comment_id: The ID of the comment to reply to.
        :param message: The reply message.
        :return: A dictionary containing the reply ID, or an error message.
        """
        url = f"{api_url}{comment_id}/comments"
        params = {"message": message, "access_token": access_token}

        response = requests.post(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            FacebookAPI.logger.error(f"Error: {response.status_code} - {response.text}")
            return {
                "error": f"Facebook API: Unexpected status code: {response.status_code}",
                "details": response.json() if response.content else None,
            }

    @staticmethod
    def reply_to_comment_with_attachment(
        access_token: str, comment_id: str, api_url: str, attachment_url: str
    ) -> dict:
        """
        Replies to a comment on a Facebook post with an attachment.

        :param access_token: The access token for the Facebook Graph API.
        :param comment_id: The ID of the comment to reply to.
        :param attachment_url: The URL of the attachment to include in the reply.
        :return: A dictionary containing the reply ID, or an error message.
        """

        url = f"{api_url}{comment_id}/comments"
        data = {"attachment_url": attachment_url, "access_token": access_token}

        response = requests.post(url, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            FacebookAPI.logger.error(f"Error: {response.status_code} - {response.text}")
            return {
                "error": f"Facebook API: Unexpected status code: {response.status_code}",
                "details": response.json() if response.content else None,
            }

    @staticmethod
    def update_comment(
        access_token: str, api_url: str, comment_id: str, message: str
    ) -> dict:
        """
        Replies to a comment on a Facebook post.

        :param access_token: The access token for the Facebook Graph API.
        :param comment_id: The ID of the comment to reply to.
        :param message: The reply message.
        :return: A dictionary containing the reply ID, or an error message.
        """
        url = f"{api_url}{comment_id}"
        data = {"message": message, "access_token": access_token}

        response = requests.post(url, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            FacebookAPI.logger.error(f"Error: {response.status_code} - {response.text}")
            return {
                "error": f"Facebook API: Unexpected status code: {response.status_code}",
                "details": response.json() if response.content else None,
            }

    @staticmethod
    def like_comment(access_token: str, comment_id: str, api_url: str) -> dict:
        """
        Likes a comment on a Facebook post.

        :param access_token: The access token for the Facebook page.
        :param comment_id: The ID of the comment to like.
        :return: A dictionary indicating success, or an error message.
        """

        url = f"{api_url}{comment_id}/likes"
        params = {"access_token": access_token}

        response = requests.post(url, params=params)
        if response.status_code == 200:
            return {"success": True}
        else:
            FacebookAPI.logger.error(f"Error: {response.status_code} - {response.text}")
            return {
                "error": f"Facebook API: Unexpected status code: {response.status_code}",
                "details": response.json() if response.content else None,
            }

    @staticmethod
    def get_reactions(
        access_token: str, post_id: str, api_url: str
    ) -> Union[list, dict]:
        """
        Retrieves the number of reactions on a Facebook post.

        :param access_token: The access token for the Facebook Graph API.
        :param post_id: The ID of the post to get reactions count for.
        :return: A dictionary with the count of each reaction type, or an error message.
        """
        url = f"{api_url}{post_id}/reactions"
        params = {
            # "summary": "true",
            "access_token": access_token
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            FacebookAPI.logger.error(f"Error: {response.status_code} - {response.text}")
            return {
                "error": f"Facebook API: Unexpected status code: {response.status_code}",
                "details": response.json() if response.content else None,
            }

    @staticmethod
    def download_file(url: str, download_folder: str) -> Optional[str]:
        """Download a file from a URL and save it to a specified folder."""
        # Send a HEAD request to get metadata about the file
        response = requests.head(url, allow_redirects=True)
        content_type = response.headers.get("Content-Type", "")

        extension = mimetypes.guess_extension(content_type.split(";")[0])
        if not extension:
            print("Could not determine the file extension.")
            return None

        random_filename = (
            "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
            + extension
        )

        os.makedirs(download_folder, exist_ok=True)
        save_path = os.path.join(download_folder, random_filename)

        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            return random_filename
        else:
            print(
                f"Failed to download file from {url}. Status code: {response.status_code}"
            )
            return None
