"""This module provides utilities for email operations using SMTP and IMAP protocols."""

import base64
import contextlib
import email
import imaplib
import logging
import os
import re
import smtplib
import time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

import requests


class EmailAPI:
    """A utility class for performing email operations."""

    logger = logging.getLogger(__name__)

    @staticmethod
    def send_email(
        host: str,
        sender_email: str,
        sender_password: str,
        recipient_email: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        html: bool = False,
    ) -> bool:
        """
        Send an email with the given parameters.

        Args:
            host (str): SMTP server host.
            sender_email (str): Email address of the sender.
            sender_password (str): Password for authentication.
            recipient_email (str): Email address of the recipient.
            subject (str): Subject of the email.
            body (str): Body of the email.
            cc (Optional[List[str]]): List of CC email addresses.
            bcc (Optional[List[str]]): List of BCC email addresses.
            attachments (Optional[List[str]]): List of file paths for attachments.
            html (bool): Whether the email body is in HTML format.

        Returns:
            bool: True if the email is sent successfully, False otherwise.
        """
        try:
            # Create a multipart message
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = recipient_email
            msg["Subject"] = subject

            if cc:
                msg["Cc"] = ", ".join(cc)
            if bcc:
                msg["Bcc"] = ", ".join(bcc)

            if html:
                body_with_space = body + "<br><br>"  # Add extra space for HTML format
                msg.attach(MIMEText(body_with_space, "html"))
            else:
                body_with_space = body + "\n\n"  # Add extra space for plain text format
                msg.attach(MIMEText(body_with_space, "plain"))

            # Add attachments
            if attachments:
                for attachment in attachments:
                    if attachment.startswith("http://") or attachment.startswith(
                        "https://"
                    ):
                        # Handle URL attachments
                        try:
                            response = requests.get(attachment, stream=True)
                            response.raise_for_status()
                            filename = attachment.split("/")[
                                -1
                            ]  # Extract file name from URL
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(response.content)
                            encoders.encode_base64(part)
                            part.add_header(
                                "Content-Disposition",
                                f"attachment; filename={filename}",
                            )
                            msg.attach(part)
                        except Exception as e:
                            print(
                                f"Error downloading attachment from URL: {attachment} - {e}"
                            )
                    else:
                        # Handle local file attachments
                        try:
                            with open(attachment, "rb") as file:
                                part = MIMEBase("application", "octet-stream")
                                part.set_payload(file.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                "Content-Disposition",
                                f"attachment; filename={os.path.basename(attachment)}",
                            )
                            msg.attach(part)
                        except Exception as e:
                            print(f"Error attaching local file: {attachment} - {e}")

            # Connect to the SMTP server
            server = smtplib.SMTP(host)
            server.starttls()
            server.login(sender_email, sender_password)

            # Send email
            server.sendmail(
                sender_email,
                [recipient_email] + (cc or []) + (bcc or []),
                msg.as_string(),
            )

            # Quit the server
            server.quit()
            return True
        except Exception as e:
            EmailAPI.logger.error(f"Unable to send email: {e}")
            return False

    @staticmethod
    def save_to_drafts(
        host: str,
        sender_email: str,
        sender_password: str,
        recipient_email: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: bool = False,
        attachments: Optional[List[str]] = None,
    ) -> bool:
        """
        Save an email as a draft.

        Args:
            host (str): The IMAP server host (e.g., 'imap.outlook.com', 'imap.gmail.com').
            sender_email (str): The email address of the sender.
            sender_password (str): The password for the sender's email account.
            recipient_email (str): The email address of the recipient.
            subject (str): The subject of the email.
            body (str): The body content of the email.
            cc (Optional[List[str]]): A list of email addresses to send a carbon copy (CC).
            bcc (Optional[List[str]]): A list of email addresses to send a blind carbon copy (BCC).
            html (bool): Indicates if the email body is in HTML format. Defaults to False.
            attachments (Optional[List[str]]): A list of file paths for attachments. Defaults to None.

        Returns:
            bool: True if the email is saved to drafts successfully, False otherwise.
        """
        try:
            if host == "imap.outlook.com":
                default_list = {
                    "inbox": "Inbox",
                    "sent": "Sent",
                    "drafts": "Drafts",
                    "junk": "Junk",
                    "trash": "Deleted",
                    "notes": "Notes",
                    "archive": "Archive",
                }
            elif host == "imap.gmail.com":
                default_list = {
                    "inbox": "inbox",
                    "sent": '"[Gmail]/Sent Mail"',
                    "drafts": '"[Gmail]/Drafts"',
                    "junk": '"[Gmail]/Spam"',
                    "trash": '"[Gmail]/Trash"',
                    "important": '"[Gmail]/Important"',
                    "all": '"[Gmail]/All Mail"',
                }
            else:
                return False
            # Connect to the IMAP server
            mail = imaplib.IMAP4_SSL(host)
            mail.login(sender_email, sender_password)

            # Create the email message
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = recipient_email
            msg["Subject"] = subject

            if cc:
                msg["Cc"] = ", ".join(cc)
            if bcc:
                msg["Bcc"] = ", ".join(bcc)

            # Add body to email
            if html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))

            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase("application", "octet-stream")
                    try:
                        with open(attachment, "rb") as file:
                            part.set_payload(file.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition", f"attachment; filename={attachment}"
                        )
                        msg.attach(part)
                    except Exception as e:
                        EmailAPI.logger.error(f"unable to attachments to draft: {e}")

            # Save message to Drafts
            mail.append(
                default_list["drafts"],
                "",
                imaplib.Time2Internaldate(time.time()),
                msg.as_string().encode("utf-8"),
            )

            # Logout from the server
            mail.logout()
            return True
        except Exception as e:
            EmailAPI.logger.error(f"unable to save drafts: {e}")
            return False

    @staticmethod
    def convert_emoji(encoded_subject: str) -> str:
        """
        Convert an email subject with encoded emojis to a string with the decoded emojis.

        Args:
            encoded_subject (str): The email subject with encoded emojis.

        Returns:
            str: The decoded subject string with emojis.

        Raises:
            ValueError: If no valid encoded emoji pattern is found in the subject.
        """
        try:
            # Search for the encoded part
            match = re.search(r"=\?UTF-8\?B\?(.*?)\?=", encoded_subject)
            if match:
                encoded_part = match.group(1)  # Extract base64 part
                decoded_emoji = base64.b64decode(encoded_part).decode("utf-8")
                # Replace the encoded part with the decoded emoji in the subject
                decoded_sentence = re.sub(
                    r"=\?UTF-8\?B\?(.*?)\?=", decoded_emoji, encoded_subject
                )
                return decoded_sentence
            else:
                return encoded_subject
        except Exception as e:
            EmailAPI.logger.error(f"Unable to convert emoji: {e}")
            return ""

    @staticmethod
    def get_email_content(email_message: email.message.Message) -> str:
        """
        Extract the email content (HTML or plain text) from the email message.

        Args:
            email_message (email.message.Message): The email message object.

        Returns:
            str: The extracted email content.
        """
        content = ""
        if email_message.is_multipart():
            # Iterate over email parts
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                # Ignore any attachments
                if content_disposition.startswith("attachment"):
                    continue

                try:
                    if content_type in ["text/plain", "text/html"]:
                        payload = part.get_payload(decode=True)
                        if isinstance(payload, bytes):
                            content += payload.decode(
                                part.get_content_charset() or "utf-8"
                            )
                        else:
                            EmailAPI.logger.error(
                                "Unexpected payload type, expected bytes."
                            )
                except Exception as e:
                    EmailAPI.logger.error(f"Unable to decode payload: {e}")

        else:
            # Single part - just extract the content
            content_type = email_message.get_content_type()
            try:
                if content_type in ["text/plain", "text/html"]:
                    payload = email_message.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        content += payload.decode(
                            email_message.get_content_charset() or "utf-8"
                        )
                    else:
                        EmailAPI.logger.error(
                            "Unexpected payload type, expected bytes."
                        )
            except Exception as e:
                EmailAPI.logger.error(f"Unable to decode single payload: {e}")

        return content

    @staticmethod
    def forward_email(
        host: str,
        sender_email: str,
        sender_password: str,
        recipient_email: str,
        mailbox: str,
        message_type: str,
        email_id: str,
    ) -> bool:
        """
        Forward an email from a specified mailbox to a recipient email address.

        Args:
            host (str): The IMAP server host.
            sender_email (str): The sender's email address for authentication.
            sender_password (str): The password for the sender's email account.
            recipient_email (str): The email address to forward the email to.
            mailbox (str): The name of the mailbox to select.
            message_type (str): The criteria to search for emails.
            email_id (str): The ID of the email to forward.

        Returns:
            bool: True if the email is forwarded successfully, False otherwise.
        """
        try:
            # Connect to the IMAP server
            mail = imaplib.IMAP4_SSL(host)
            mail.login(sender_email, sender_password)

            if host == "imap.outlook.com":
                default_list = {
                    "inbox": "Inbox",
                    "sent": "Sent",
                    "drafts": "Drafts",
                    "junk": "Junk",
                    "trash": "Deleted",
                    "notes": "Notes",
                    "archive": "Archive",
                }
            elif host == "imap.gmail.com":
                default_list = {
                    "inbox": "inbox",
                    "sent": '"[Gmail]/Sent Mail"',
                    "drafts": '"[Gmail]/Drafts"',
                    "junk": '"[Gmail]/Spam"',
                    "trash": '"[Gmail]/Trash"',
                    "important": '"[Gmail]/Important"',
                    "all": '"[Gmail]/All Mail"',
                }
            else:
                return False

            # Select the inbox
            mail.select(default_list[mailbox.lower()])

            # Retrieve the email with the given UID
            _, email_ids = mail.search(None, message_type)

            # Ensure email_ids is a list and not None
            if email_ids:
                email_ids_str = [
                    item.decode("utf-8") if isinstance(item, bytes) else str(item)
                    for item in email_ids
                ][0]

                if str(email_id) in email_ids_str:
                    result, data = mail.fetch(str(email_id), "(RFC822)")
                    raw_email = (
                        data[0][1]
                        if isinstance(data[0], tuple) and data[0][1] is not None
                        else b""
                    )
                    email_message = email.message_from_bytes(raw_email)

                # Create a new email message
                forward_msg = MIMEMultipart("alternative")
                forward_msg["From"] = sender_email
                forward_msg["To"] = recipient_email
                forward_msg["Subject"] = "Fwd: " + str(email_message["Subject"])

                forward_template = f"""
                ---------- Forwarded message ----------<br>
                From: {email_message['From']}<br>
                Date: {email_message['Date']}<br>
                Subject: {email_message['Subject']}<br>
                To: {email_message['To']}
                """

                html_email_content = ""

                html_email_content = EmailAPI.get_email_content(email_message)
                html_splitter = "<html "
                parts = html_email_content.split(html_splitter)
                html_email_content = html_splitter + parts[1]

                html_content = forward_template + html_email_content

                html_content = EmailAPI.convert_emoji(html_content)
                html_part = MIMEText(html_content, "html")
                forward_msg.attach(html_part)

                # Connect to the SMTP server
                smtp_server = smtplib.SMTP(host)
                smtp_server.starttls()
                smtp_server.login(sender_email, sender_password)
                smtp_server.sendmail(
                    sender_email, recipient_email, forward_msg.as_string()
                )
                smtp_server.quit()
                mail.logout()
                return True
            else:
                print(f"Failed to fetch email with UID {email_id}")
                mail.logout()
                return False
        except Exception as e:
            EmailAPI.logger.error(f"unable to forward email: {e}")
            return False

    @staticmethod
    def reply_to_email(
        host: str,
        sender_email: str,
        sender_password: str,
        recipient_email: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        html: bool = False,
        reply_to: Optional[str] = None,
    ) -> bool:
        """
        Reply to an email with the given parameters.

        Args:
            host (str): SMTP server host.
            sender_email (str): Email address of the sender.
            sender_password (str): Password for authentication.
            recipient_email (str): Email address of the recipient.
            subject (str): Subject of the email.
            body (str): Body of the email.
            cc (Optional[List[str]]): List of CC email addresses.
            bcc (Optional[List[str]]): List of BCC email addresses.
            attachments (Optional[List[str]]): List of file paths for attachments.
            html (bool): Whether the email body is in HTML format.
            reply_to (Optional[str]): Message ID of the email to reply to.

        Returns:
            bool: True if the email is replied successfully, False otherwise.
        """
        try:
            # Create a multipart message
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = recipient_email
            msg["Subject"] = subject
            if reply_to:
                msg["In-Reply-To"] = reply_to

            if cc:
                msg["Cc"] = ", ".join(cc)
            if bcc:
                msg["Bcc"] = ", ".join(bcc)

            # Add body to email
            if html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))

            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase("application", "octet-stream")
                    try:
                        with open(attachment, "rb") as file:
                            part.set_payload(file.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition", f"attachment; filename= {attachment}"
                        )
                        msg.attach(part)
                    except Exception as e:
                        print(f"Error sending attachment {attachment}: {e}")

            # Connect to the SMTP server
            server = smtplib.SMTP(host)
            server.starttls()
            server.login(sender_email, sender_password)

            # Send email
            server.sendmail(
                sender_email,
                [recipient_email] + (cc or []) + (bcc or []),
                msg.as_string(),
            )

            # Quit the server
            server.quit()
            return True

        except Exception as e:
            EmailAPI.logger.error(f"unable to reply to email: {e}")
            return False

    @staticmethod
    def delete_email(
        host: str, sender_email: str, sender_password: str, mailbox: str, email_id: str
    ) -> bool:
        """
        Delete an email by its ID.

        Args:
            host (str): IMAP server host.
            sender_email (str): Email address of the sender.
            sender_password (str): Password for authentication.
            mailbox (str): Mailbox name.
            email_id (str): Email ID to delete.

        Returns:
            bool: True if the email is deleted successfully, False otherwise.
        """
        try:
            imap_connection = imaplib.IMAP4_SSL(host)
            imap_connection.login(sender_email, sender_password)
            imap_connection.select(mailbox)
            imap_connection.store(str(email_id), "+FLAGS", "\\Deleted")
            imap_connection.expunge()
            imap_connection.logout()
            return True
        except Exception as e:
            EmailAPI.logger.error(f"unable to delete email: {e}")
            return False

    @staticmethod
    def move_email(
        host: str,
        sender_email: str,
        sender_password: str,
        email_id: str,
        mailbox: str,
        destination_folder: str,
    ) -> bool:
        """
        Move an email from one mailbox to another.

        Args:
            host (str): The host of the IMAP server.
            sender_email (str): The username for authentication.
            sender_password (str): The password for authentication.
            email_id (str): The ID of the email to move.
            mailbox (str): The name of the mailbox to select (INBOX, SENT, DRAFTS, JUNK, TRASH, NOTES, ARCHIVE).
            destination_folder (str): The name of the mailbox to move the email to.

        Returns:
            bool: True if the email is successfully moved, False otherwise.
        """
        try:
            # Connect to the IMAP server
            imap_connection = imaplib.IMAP4_SSL(host)
            imap_connection.login(sender_email, sender_password)

            # Select the source mailbox (INBOX)
            try:
                if host == "imap.outlook.com":
                    default_list = {
                        "inbox": "Inbox",
                        "sent": "Sent",
                        "drafts": "Drafts",
                        "junk": "Junk",
                        "trash": "Deleted",
                        "notes": "Notes",
                        "archive": "Archive",
                    }
                    destination_folder = default_list[destination_folder]
                elif host == "imap.gmail.com":
                    default_list = {
                        "inbox": "inbox",
                        "sent": '"[Gmail]/Sent Mail"',
                        "drafts": '"[Gmail]/Drafts"',
                        "junk": '"[Gmail]/Spam"',
                        "trash": '"[Gmail]/Trash"',
                        "important": '"[Gmail]/Important"',
                        "all": '"[Gmail]/All Mail"',
                    }
                    destination_folder = default_list[destination_folder]
            except KeyError:
                status, folder_list = imap_connection.list()
                if destination_folder not in str(folder_list):
                    EmailAPI.create_folder(
                        host, sender_email, sender_password, destination_folder
                    )
            imap_connection.select(default_list[mailbox.lower()])
            imap_connection.copy(str(email_id), destination_folder)

            imap_connection.logout()
            return True

        except Exception as e:
            EmailAPI.logger.error(f"unable to move email: {e}")
            return False

    @staticmethod
    def exclude_emails_by_sender(emails_data: list, filter_list: list) -> list:
        """
        Exclude emails from the provided list of emails based on specified senders.

        Args:
            emails_data (list): List of email data dictionaries, each containing an email's details.
            filter_list (list): List of sender identifiers to exclude from the result.

        Returns:
            list: A list of emails that do not have senders matching any item in the filter list.
        """
        emails = []
        for e in emails_data:
            append_email = True
            for item in filter_list:
                if item in e["from"]:
                    append_email = False
                    break

            if append_email:
                emails.append(e)
        return emails

    @staticmethod
    def include_emails_by_sender(emails_data: list, filter_list: list) -> list:
        """
        Include emails from the provided list of emails based on specified senders.

        Args:
            emails_data (list): List of email data dictionaries, each containing an email's details.
            filter_list (list): List of sender identifiers to include in the result.

        Returns:
            list: A list of emails that have senders matching any item in the filter list.
        """
        emails = []
        for e in emails_data:
            append_email = False
            for item in filter_list:
                if item in e["from"]:
                    append_email = True
                    break

            if append_email:
                emails.append(e)
        return emails

    @staticmethod
    def auto_emails(
        host: str,
        sender_email: str,
        sender_password: str,
        mailbox: str = "INBOX",
        message_type: str = "ALL",
        delete_ids: Optional[List[str]] = None,
        auto_delete: bool = False,
        filter_list: Optional[List[str]] = None,
        get_filter: Optional[List[str]] = None,
        mark_as_read: bool = False,
    ) -> dict:
        """
        Connect to an IMAP server and retrieve emails based on the specified criteria.

        Args:
            host (str): The host of the IMAP server. imap.gmail.com, imap.outlook.com.
            user (str): The username for authentication.
            password (str): The app password for authentication.
            mailbox (str, optional): The mailbox to select.
                Defaults to "INBOX". Possible values: ['INBOX', 'SENT', 'DRAFTS', 'JUNK', 'TRASH'].
            message_type (str, optional): The criteria to search for emails.
                Defaults to "ALL". Possible values: ['ALL', 'UNSEEN', 'SEEN'].
            delete_ids (List[str], optional): The IDs of emails to delete. Defaults to [].
            auto_delete (bool, optional): Whether to automatically delete emails. Defaults to False.
            filter_list (List[str], optional): The list of items to filter emails by. Defaults to [].
            get_filter (List[str], optional): The list of items to get emails by. Defaults to [].
            mark_as_read (bool, optional): Whether to mark emails as read. Defaults to False.

        Returns:
            dict: A dictionary containing the emails and the sender email.
                - emails (List[dict]): A list of email details.
                    - id (str): The ID of the email.
                    - from (str): The sender of the email.
                    - to (str): The recipient of the email.
                    - cc (str): The carbon copy recipient of the email.
                    - bcc (str): The blind carbon copy recipient of the email.
                    - subject (str): The subject of the email.
                    - date (str): The date of the email.
                    - reply_to (str): The reply-to address of the email.
                    - message_id (str): The message ID of the email.
                    - body (str): The body of the email.
                    - attachments (List[str]): The list of attachments of the email.
                - sender_email (List[str]): A list of sender email.
        """
        try:

            if host == "imap.outlook.com":
                default_list = {
                    "inbox": "Inbox",
                    "sent": "Sent",
                    "drafts": "Drafts",
                    "junk": "Junk",
                    "trash": "Deleted",
                    "notes": "Notes",
                    "archive": "Archive",
                }
            elif host == "imap.gmail.com":
                default_list = {
                    "inbox": "inbox",
                    "sent": '"[Gmail]/Sent Mail"',
                    "drafts": '"[Gmail]/Drafts"',
                    "junk": '"[Gmail]/Spam"',
                    "trash": '"[Gmail]/Trash"',
                    "important": '"[Gmail]/Important"',
                    "all": '"[Gmail]/All Mail"',
                }
            else:
                return {}

            mailbox = default_list[mailbox.lower()]
            # Connect to the IMAP server
            mail = imaplib.IMAP4_SSL(host)
            mail.login(sender_email, sender_password)

            mail.select(mailbox)

            _, email_ids = mail.search(None, message_type)
            email_ids = email_ids[0].split()

            emails = []

            # Iterate through email ids
            for email_id in email_ids:
                result, data = mail.fetch(email_id, "(RFC822)")
                if isinstance(data[0], tuple) and isinstance(data[0][1], bytes):
                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)

                email_id_str = email_id.decode("utf-8")

                # Extract email details
                email_details = {
                    "id": email_id_str,
                    "from": msg["From"],
                    "to": msg["To"],
                    "cc": msg["Cc"],
                    "bcc": msg["Bcc"],
                    "subject": msg["Subject"],
                    "date": msg["Date"],
                    "reply_to": msg["Reply-To"],
                    "message_id": msg["Message-ID"],
                    "body": "",
                    "attachments": [],
                }

                # Extract body
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if isinstance(payload, bytes):
                                with contextlib.suppress(UnicodeDecodeError):
                                    email_details["body"] = payload.decode(
                                        "utf-8", errors="ignore"
                                    )
                        elif (
                            part.get_content_maintype() == "multipart"
                            and part.get("Content-Disposition") is None
                        ):
                            continue
                        else:
                            # Extract attachment
                            attachment_payload = part.get_payload(decode=True)
                            if isinstance(attachment_payload, (bytes, str)):
                                if isinstance(attachment_payload, str):
                                    attachment_payload = attachment_payload.encode(
                                        "utf-8"
                                    )
                                attachment = {
                                    "filename": part.get_filename(),
                                    "content_type": part.get_content_type(),
                                    "content": base64.b64encode(
                                        attachment_payload
                                    ).decode("utf-8"),
                                }
                                email_details["attachments"].append(attachment)
                else:
                    with contextlib.suppress(UnicodeDecodeError, AttributeError):
                        if isinstance(msg.get_payload(decode=True), bytes):
                            body = msg.get_payload(decode=True)
                            if hasattr(body, "decode"):
                                email_details["body"] = body.decode(
                                    "utf-8", errors="ignore"
                                )

                emails.append(email_details)

                if message_type == "UNSEEN" and not mark_as_read:
                    mail.store(email_id, "-FLAGS", "\\Seen")

            if get_filter:
                emails = EmailAPI.include_emails_by_sender(emails, get_filter)
            elif filter_list:
                emails = EmailAPI.exclude_emails_by_sender(emails, filter_list)

            if auto_delete:
                for item in emails:
                    id = item["id"]
                    mail.store(id.encode("utf-8"), "+FLAGS", "\\Deleted")
            elif delete_ids:
                for item in emails:
                    id = item["id"]
                    if id in delete_ids:
                        mail.store(id.encode("utf-8"), "+FLAGS", "\\Deleted")

            sender_email_list = []
            for item in emails:
                if "<" in item["from"] and ">" in item["from"]:
                    _from = item["from"].split("<")[1].split(">")[0]
                else:
                    _from = item["from"]

                if _from not in sender_email_list:
                    sender_email_list.append(_from)
            sender_email = ",".join(sender_email_list)

            mail.close()
            mail.logout()

            return {"emails": emails, "sender_email": sender_email}
        except Exception as e:
            EmailAPI.logger.error(f"unable to get emails: {e}")
            return {"emails": [], "sender_email": []}

    @staticmethod
    def get_new_emails(
        host: str,
        sender_email: str,
        sender_password: str,
        mailbox: str = "INBOX",
        message_type: str = "UNSEEN",
        mark_as_read: bool = True,
        max_emails: int = 5,
    ) -> list:
        """
        Connect to an IMAP server and retrieve emails based on the specified criteria.

        Args:
            host (str): The host of the IMAP server. imap.gmail.com, imap.outlook.com.
            sender_email (str): The username for authentication.
            sender_password (str): The app password for authentication.
            mailbox (str, optional): The mailbox to select. Defaults to "INBOX".
                Possible values: ['INBOX', 'SENT', 'DRAFTS', 'JUNK', 'TRASH'].
            message_type (str, optional): The criteria to search for emails. Defaults to "UNSEEN".
                Possible values: ['ALL', 'UNSEEN', 'SEEN'].
            mark_as_read (bool, optional): Whether to mark emails as read. Defaults to True.
            max_emails (int, optional): The maximum number of emails to retrieve. Defaults to 5.

        Returns:
            list: A list of dictionaries containing the email details.
                - id (str): The ID of the email.
                - from (str): The sender of the email.
                - to (str): The recipient of the email.
                - cc (str): The carbon copy recipient of the email.
                - bcc (str): The blind carbon copy recipient of the email.
                - subject (str): The subject of the email.
                - date (str): The date of the email.
                - reply_to (str): The reply-to address of the email.
                - message_id (str): The message ID of the email.
                - body (str): The body of the email.
                - attachments (List[str]): The list of attachments of the email.
        """
        try:

            if host == "imap.outlook.com":
                default_list = {
                    "inbox": "Inbox",
                    "sent": "Sent",
                    "drafts": "Drafts",
                    "junk": "Junk",
                    "trash": "Deleted",
                    "notes": "Notes",
                    "archive": "Archive",
                }
            elif host == "imap.gmail.com":
                default_list = {
                    "inbox": "inbox",
                    "sent": '"[Gmail]/Sent Mail"',
                    "drafts": '"[Gmail]/Drafts"',
                    "junk": '"[Gmail]/Spam"',
                    "trash": '"[Gmail]/Trash"',
                    "important": '"[Gmail]/Important"',
                    "all": '"[Gmail]/All Mail"',
                }
            else:
                return []

            mailbox = default_list[mailbox.lower()]
            # Connect to the IMAP server
            mail = imaplib.IMAP4_SSL(host)
            mail.login(sender_email, sender_password)
            mail.select(mailbox)
            _, email_ids = mail.search(None, message_type)

            new_emails = []
            email_ids_list = email_ids[0].decode().split()  # Decode and split the IDs

            for email_count, email_id in enumerate(email_ids_list):

                if email_count < max_emails:
                    email_details = {}

                    result, data = mail.fetch(email_id, "(RFC822)")
                    raw_email = (
                        data[0][1] if data and isinstance(data[0], tuple) else b""
                    )
                    msg = email.message_from_bytes(raw_email)
                    email_id_str = email_id

                    # Extract email details
                    email_details = {
                        "id": email_id_str,
                        "from": msg["From"],
                        "to": msg["To"],
                        "cc": msg["Cc"],
                        "bcc": msg["Bcc"],
                        "subject": msg["Subject"],
                        "date": msg["Date"],
                        "reply_to": msg["Reply-To"],
                        "message_id": msg["Message-ID"],
                        "body": "",
                        "attachments": [],
                    }

                    # Extract body
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                payload = part.get_payload(decode=True)
                                if isinstance(payload, bytes):
                                    with contextlib.suppress(UnicodeDecodeError):
                                        email_details["body"] = payload.decode(
                                            "utf-8", errors="ignore"
                                        )
                            elif (
                                part.get_content_maintype() == "multipart"
                                and part.get("Content-Disposition") is None
                            ):
                                continue
                            else:
                                # Extract attachment
                                payload = part.get_payload(decode=True)
                                if isinstance(payload, bytes):
                                    attachment = {
                                        "filename": part.get_filename(),
                                        "content_type": part.get_content_type(),
                                        "content": base64.b64encode(payload).decode(
                                            "utf-8"
                                        ),
                                    }
                                email_details["attachments"].append(attachment)
                    else:
                        with contextlib.suppress(Exception):
                            payload = msg.get_payload(decode=True)
                            if isinstance(payload, bytes):
                                email_details["body"] = payload.decode(
                                    "utf-8", errors="ignore"
                                )
                            else:
                                EmailAPI.logger.error(
                                    "Unexpected payload type, expected bytes."
                                )

                    if message_type == "UNSEEN" and not mark_as_read:
                        mail.store(email_id, "-FLAGS", "\\Seen")

                    new_emails.append(email_details)
                else:
                    mail.store(email_id, "-FLAGS", "\\Seen")

            mail.close()
            mail.logout()

            return new_emails

        except Exception as e:
            EmailAPI.logger.error(f"unable to get new emails: {e}")
            return []

    @staticmethod
    def set_email_type(
        host: str,
        sender_email: str,
        sender_password: str,
        mailbox: str = "INBOX",
        message_type: str = "UNSEEN",
        email_id: Optional[str] = None,
    ) -> bool:
        """
        Set the email type (seen or unseen) for a specific email ID in a mailbox.

        Args:
            host (str): The IMAP server host.
            sender_email (str): The sender's email address for authentication.
            sender_password (str): The password for the sender's email account.
            mailbox (str, optional): The name of the mailbox to select. Defaults to "INBOX".
            message_type (str, optional): The type of message to look for ("UNSEEN" or "SEEN"). Defaults to "UNSEEN".
            email_id (str, optional): The ID of the email to modify. Defaults to None.

        Returns:
            bool: True if the email type is successfully set, False otherwise.
        """
        try:
            if host == "imap.outlook.com":
                default_list = {
                    "inbox": "Inbox",
                    "sent": "Sent",
                    "drafts": "Drafts",
                    "junk": "Junk",
                    "trash": "Deleted",
                    "notes": "Notes",
                    "archive": "Archive",
                }
            elif host == "imap.gmail.com":
                default_list = {
                    "inbox": "inbox",
                    "sent": '"[Gmail]/Sent Mail"',
                    "drafts": '"[Gmail]/Drafts"',
                    "junk": '"[Gmail]/Spam"',
                    "trash": '"[Gmail]/Trash"',
                    "important": '"[Gmail]/Important"',
                    "all": '"[Gmail]/All Mail"',
                }
            else:
                return False

            mailbox = default_list[mailbox.lower()]
            # Connect to the IMAP server
            mail = imaplib.IMAP4_SSL(host)
            mail.login(sender_email, sender_password)
            mail.select(mailbox)
            _, email_ids = mail.search(None, message_type)
            email_ids_str = []
            if email_ids:
                email_ids_str = [item.decode("utf-8") for item in email_ids][0]
            if str(email_id) in email_ids_str:
                if message_type.lower() == "UNSEEN".lower():
                    mail.store(str(email_id), "+FLAGS", "\\Seen")
                elif message_type.lower() == "SEEN".lower():
                    mail.store(str(email_id), "-FLAGS", "\\Seen")

            mail.close()
            mail.logout()
            return True
        except Exception as e:
            EmailAPI.logger.error(f"unable to email type: {e}")
            return False

    @staticmethod
    def create_folder(
        host: str, sender_email: str, sender_password: str, folder_name: str
    ) -> bool:
        """
        Create a folder in the IMAP server.

        Args:
            host (str): IMAP server host.
            sender_email (str): Email address of the sender.
            sender_password (str): Password for authentication.
            folder_name (str): Name of the folder to be created.

        Returns:
            bool: True if the folder is created successfully, False otherwise.
        """
        try:
            # Connect to the IMAP server
            imap_connection = imaplib.IMAP4_SSL(host)
            imap_connection.login(sender_email, sender_password)

            # Create the folder
            imap_connection.create(folder_name)

            imap_connection.logout()
            return True
        except Exception as e:
            EmailAPI.logger.error(f"unable to create folder: {e}")
            return False
