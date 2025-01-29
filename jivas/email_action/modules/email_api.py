"""This module provides utilities for email operations using SMTP and IMAP protocols."""

import base64
import email
import imaplib
import logging
import re
import smtplib
import time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional


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
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = recipient_email
            msg["Subject"] = subject

            if cc:
                msg["Cc"] = ", ".join(cc)
            if bcc:
                msg["Bcc"] = ", ".join(bcc)

            msg.attach(MIMEText(body, "html" if html else "plain"))

            if attachments:
                for attachment in attachments:
                    try:
                        with open(attachment, "rb") as file:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(file.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename={attachment}",
                        )
                        msg.attach(part)
                    except Exception:
                        EmailAPI.logger.error(
                            f"Error attaching file: {attachment}", exc_info=True
                        )

            with smtplib.SMTP(host) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(
                    sender_email,
                    [recipient_email] + (cc or []) + (bcc or []),
                    msg.as_string(),
                )
            return True
        except Exception:
            EmailAPI.logger.error("Error sending email", exc_info=True)
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
            host (str): IMAP server host.
            sender_email (str): Email address of the sender.
            sender_password (str): Password for authentication.
            recipient_email (str): Email address of the recipient.
            subject (str): Subject of the email.
            body (str): Body of the email.
            cc (Optional[List[str]]): List of CC email addresses.
            bcc (Optional[List[str]]): List of BCC email addresses.
            html (bool): Whether the email body is in HTML format.
            attachments (Optional[List[str]]): List of file paths for attachments.

        Returns:
            bool: True if the email is saved as a draft successfully, False otherwise.
        """
        try:
            default_folders = {
                "imap.outlook.com": "Drafts",
                "imap.gmail.com": '"[Gmail]/Drafts"',
            }
            drafts_folder = default_folders.get(host)
            if not drafts_folder:
                raise ValueError("Unsupported host for saving drafts.")

            mail = imaplib.IMAP4_SSL(host)
            mail.login(sender_email, sender_password)

            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = recipient_email
            msg["Subject"] = subject

            if cc:
                msg["Cc"] = ", ".join(cc)
            if bcc:
                msg["Bcc"] = ", ".join(bcc)

            msg.attach(MIMEText(body, "html" if html else "plain"))

            if attachments:
                for attachment in attachments:
                    try:
                        with open(attachment, "rb") as file:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(file.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename={attachment}",
                        )
                        msg.attach(part)
                    except Exception:
                        EmailAPI.logger.error(
                            f"Error attaching file: {attachment}", exc_info=True
                        )

            mail.append(
                drafts_folder,
                "",
                imaplib.Time2Internaldate(time.time()),
                msg.as_string().encode("utf-8"),
            )
            mail.logout()
            return True
        except Exception:
            EmailAPI.logger.error("Error saving to drafts", exc_info=True)
            return False

    @staticmethod
    def convert_emoji(encoded_subject: str) -> str:
        """
        Convert encoded emoji in the subject to its decoded format.

        Args:
            encoded_subject (str): The encoded subject string.

        Returns:
            str: The decoded subject string with emojis.
        """
        try:
            match = re.search(r"=\?UTF-8\?B\?(.*?)\?=", encoded_subject)
            if match:
                encoded_part = match.group(1)
                decoded_emoji = base64.b64decode(encoded_part).decode("utf-8")
                decoded_subject = re.sub(
                    r"=\?UTF-8\?B\?(.*?)\?=", decoded_emoji, encoded_subject
                )
                return decoded_subject
            return encoded_subject
        except Exception:
            EmailAPI.logger.error("Error converting emoji", exc_info=True)
            return encoded_subject

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
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if content_disposition.startswith("attachment"):
                    continue

                try:
                    if content_type == "text/plain" or content_type == "text/html":
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset()
                        if isinstance(payload, bytes) and charset:
                            content += payload.decode(charset)
                except Exception:
                    EmailAPI.logger.error("Error decoding payload", exc_info=True)
        else:
            content_type = email_message.get_content_type()
            try:
                if content_type == "text/plain" or content_type == "text/html":
                    payload = email_message.get_payload(decode=True)
                    charset = email_message.get_content_charset()
                    if isinstance(payload, bytes) and charset:
                        content += payload.decode(charset)
            except Exception:
                EmailAPI.logger.error("Error decoding single payload", exc_info=True)
        return content

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
            mail = imaplib.IMAP4_SSL(host)
            mail.login(sender_email, sender_password)
            mail.select(mailbox)
            mail.store(email_id, "+FLAGS", "\\Deleted")
            mail.expunge()
            mail.logout()
            return True
        except Exception:
            EmailAPI.logger.error("Error deleting email", exc_info=True)
            return False
