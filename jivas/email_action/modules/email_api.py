import logging
import time
import traceback
import base64
import re
import imaplib
import smtplib
import email
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


class EmailAPI:

    logger = logging.getLogger(__name__)
    @staticmethod
    def send_email(host, sender_email, sender_password, recipient_email, subject, body,
               cc=None, bcc=None, attachments=None, html=False):
        try:
            # Create a multipart message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject

            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)


            if html:
                body_with_space = body + "<br><br>"  # Add extra space for HTML format
                msg.attach(MIMEText(body_with_space, 'html'))
            else:
                body_with_space = body + "\n\n"  # Add extra space for plain text format
                msg.attach(MIMEText(body_with_space, 'plain'))

            # Add attachments
            if attachments:
                for attachment in attachments:
                    if attachment.startswith("http://") or attachment.startswith("https://"):
                        # Handle URL attachments
                        try:
                            response = requests.get(attachment, stream=True)
                            response.raise_for_status()
                            filename = attachment.split("/")[-1]  # Extract file name from URL
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(response.content)
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition', f'attachment; filename={filename}')
                            msg.attach(part)
                        except Exception as e:
                            print(f"Error downloading attachment from URL: {attachment} - {e}")
                    else:
                        # Handle local file attachments
                        try:
                            with open(attachment, 'rb') as file:
                                part = MIMEBase('application', 'octet-stream')
                                part.set_payload(file.read())
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment)}')
                            msg.attach(part)
                        except Exception as e:
                            print(f"Error attaching local file: {attachment} - {e}")

            # Connect to the SMTP server
            server = smtplib.SMTP(host)
            server.starttls()
            server.login(sender_email, sender_password)

            # Send email
            server.sendmail(sender_email, [recipient_email] + (cc or []) + (bcc or []), msg.as_string())

            # Quit the server
            server.quit()
            return True
        except Exception as e:
            EmailAPI.logger.error(f"Unable to send email: {traceback.format_exc()}")
            return {'error': str(e)}
    
        
    # @staticmethod
    # def send_email(host, sender_email, sender_password, recipient_email, subject, body,
    #                cc=None, bcc=None, attachments=None, html=False):
    #     try:
    #         # Create a multipart message
    #         msg = MIMEMultipart()
    #         msg['From'] = sender_email
    #         msg['To'] = recipient_email
    #         msg['Subject'] = subject

    #         if cc:
    #             msg['Cc'] = ', '.join(cc)
    #         if bcc:
    #             msg['Bcc'] = ', '.join(bcc)

    #         # Add body to email
    #         if html:
    #             msg.attach(MIMEText(body, 'html'))
    #         else:
    #             msg.attach(MIMEText(body, 'plain'))

    #         # Add attachments
    #         if attachments:
    #             for attachment in attachments:
    #                 part = MIMEBase('application', 'octet-stream')
    #                 try:
    #                     with open(attachment, 'rb') as file:
    #                         part.set_payload(file.read())
    #                     encoders.encode_base64(part)
    #                     part.add_header('Content-Disposition', f'attachment; filename= {attachment}')
    #                     msg.attach(part)
    #                 except:
    #                     print(f'Error sending attachment: {attachment}')
    #         # Connect to the SMTP server
    #         server = smtplib.SMTP(host)

    #         server.starttls()
    #         server.login(sender_email, sender_password)
    #         print("send_email data")
    #         print({
    #             "sender_email": sender_email,
    #             "sender_password": sender_password,
    #             "recipient_email": recipient_email,
    #             "subject": subject,
    #             "body": body,
    #             "cc": cc,
    #             "bcc": bcc,
    #             "attachments": attachments,
    #             "html": html
    #         })

    #         # Send email
    #         server.sendmail(sender_email, [recipient_email] + (cc or []) + (bcc or []), msg.as_string())

    #         # Quit the server
    #         server.quit()
    #         return True
    #     except Exception as e:
    #         EmailAPI.logger.error(f"unable to send email: {traceback.format_exc()}")
    #         return {'error': e}


    @staticmethod
    def save_to_drafts(host, sender_email, sender_password, recipient_email, subject, body, cc=None, bcc=None, html=False, attachments=None):
        try:
            if host == "imap.outlook.com":
                default_list = {'inbox': 'Inbox', "sent": 'Sent', 'drafts': 'Drafts', "junk": 'Junk', 'trash': 'Deleted', "notes": 'Notes', 'archive': 'Archive'}
            elif host == "imap.gmail.com":
                default_list = {'inbox': 'inbox', 'sent': '"[Gmail]/Sent Mail"', 'drafts': '"[Gmail]/Drafts"', 'junk': '"[Gmail]/Spam"', 'trash': '"[Gmail]/Trash"', 'important': '"[Gmail]/Important"', 'all': '"[Gmail]/All Mail"'}
            else:
                return None
            # Connect to the IMAP server
            mail = imaplib.IMAP4_SSL(host)
            mail.login(sender_email, sender_password)

            # Create the email message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject

            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)

            # Add body to email
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    try:
                        with open(attachment, 'rb') as file:
                            part.set_payload(file.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename={attachment}')
                        msg.attach(part)
                    except Exception as e:
                        EmailAPI.logger.error(f"unable to attachments to draft: {traceback.format_exc()}")


            # Save message to Drafts
            mail.append(default_list['drafts'], '', imaplib.Time2Internaldate(time.time()), msg.as_string().encode('utf-8'))

            # Logout from the server
            mail.logout()
            return True
        except Exception as e:
            EmailAPI.logger.error(f"unable to save drafts: {traceback.format_exc()}")
            return {'error': e}

    @staticmethod
    def convert_emoji(encoded_subject):
        try:
            # Search for the encoded part
            match = re.search(r'=\?UTF-8\?B\?(.*?)\?=', encoded_subject)
            if match:
                encoded_part = match.group(1)  # Extract base64 part
                decoded_emoji = base64.b64decode(encoded_part).decode('utf-8')
                # Replace the encoded part with the decoded emoji in the subject
                decoded_sentence = re.sub(r'=\?UTF-8\?B\?(.*?)\?=', decoded_emoji, encoded_subject)
                return decoded_sentence
            else:
                return encoded_subject
                # raise ValueError("No valid encoded emoji pattern found in subject.")
        except Exception as e:
            EmailAPI.logger.error(f"Unable to convert emoji: {traceback.format_exc()}")  
            return {'error': str(e)}
    
        
    @staticmethod
    def get_email_content(email_message):
        """Extracts the email content (HTML or plain text) from the email message."""
        content = ""
        if email_message.is_multipart():
            # Iterate over email parts
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                # Ignore any attachments
                if content_disposition.startswith("attachment"):
                    continue

                # Get the email content
                try:
                    if content_type == 'text/plain':
                        content += part.get_payload(decode=True).decode(part.get_content_charset())
                    elif content_type == 'text/html':
                        content += part.get_payload(decode=True).decode(part.get_content_charset())
                except Exception as e:
                    EmailAPI.logger.error(f"unable to decode payload: {traceback.format_exc()}")

        else:
            # Single part - just extract the content
            content_type = email_message.get_content_type()
            try:
                if content_type == 'text/plain':
                    content += email_message.get_payload(decode=True).decode(email_message.get_content_charset())
                elif content_type == 'text/html':
                    content += email_message.get_payload(decode=True).decode(email_message.get_content_charset())
            except Exception as e:
                EmailAPI.logger.error(f"unable to decode single payload: {traceback.format_exc()}")

        return content
        

    @staticmethod
    def forward_email(host, sender_email, sender_password, recipient_email, mailbox, message_type, email_id):
        try:
            # Connect to the IMAP server
            mail = imaplib.IMAP4_SSL(host)
            mail.login(sender_email, sender_password)

            if host == "imap.outlook.com":
                default_list = {'inbox': 'Inbox', "sent": 'Sent', 'drafts': 'Drafts', "junk": 'Junk', 'trash': 'Deleted', "notes": 'Notes', 'archive': 'Archive'}
            elif host == "imap.gmail.com":
                default_list = {'inbox': 'inbox', 'sent': '"[Gmail]/Sent Mail"', 'drafts': '"[Gmail]/Drafts"', 'junk': '"[Gmail]/Spam"', 'trash': '"[Gmail]/Trash"', 'important': '"[Gmail]/Important"', 'all': '"[Gmail]/All Mail"'}
            else:
                return None

            # Select the inbox
            mail.select(default_list[mailbox.lower()])

            # Retrieve the email with the given UID
            _, email_ids = mail.search(None, message_type)
            email_ids_str = [item.decode('utf-8') for item in email_ids][0]

            if str(email_id) in email_ids_str:
                result, data = mail.fetch(str(email_id).encode('utf-8'), '(RFC822)')
                raw_email = data[0][1]
                email_message = email.message_from_bytes(raw_email)

                # Create a new email message
                forward_msg = MIMEMultipart('alternative')
                forward_msg['From'] = sender_email
                forward_msg['To'] = recipient_email
                forward_msg['Subject'] = "Fwd: " + str(email_message['Subject'])

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
                html_part = MIMEText(html_content, 'html')
                forward_msg.attach(html_part)

                # Connect to the SMTP server
                smtp_server = smtplib.SMTP(host)
                smtp_server.starttls()
                smtp_server.login(sender_email, sender_password)
                smtp_server.sendmail(sender_email, recipient_email, forward_msg.as_string())
                smtp_server.quit()
                mail.logout()
                return True
            else:
                print(f'Failed to fetch email with UID {email_id}')
                mail.logout()
                return False
        except Exception as e:
            EmailAPI.logger.error(f"unable to forward email: {traceback.format_exc()}")
            return {'error': e}
            
            
    @staticmethod
    def reply_to_email(host, sender_email, sender_password, recipient_email, subject, body,
                    cc=None, bcc=None, attachments=None, html=False, reply_to=None):
        """
        Connects to the SMTP server, creates a reply email message, and sends it.
        """
        try:
            # Create a multipart message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            if reply_to:
                msg['In-Reply-To'] = reply_to

            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)

            # Add body to email
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    try:
                        with open(attachment, 'rb') as file:
                            part.set_payload(file.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename= {attachment}')
                        msg.attach(part)
                    except:
                        print(f'Error sending attachment: {attachment}')

            # Connect to the SMTP server
            server = smtplib.SMTP(host)
            server.starttls()
            server.login(sender_email, sender_password)

            # Send email
            server.sendmail(sender_email, [recipient_email] + (cc or []) + (bcc or []), msg.as_string())

            # Quit the server
            server.quit()
            return True

        except Exception as e:
            EmailAPI.logger.error(f"unable to reply to email: {traceback.format_exc()}")
            return {'error': e}
        

    @staticmethod
    def delete_email(host, sender_email, sender_password, mailbox, email_id):
        try:
            imap_connection = imaplib.IMAP4_SSL(host)
            imap_connection.login(sender_email, sender_password)
            imap_connection.select(mailbox)
            imap_connection.store(str(email_id).encode('utf-8'), '+FLAGS', '\\Deleted')
            imap_connection.expunge()
            imap_connection.logout()
            return True
        except Exception as e:
            EmailAPI.logger.error(f"unable to delete email: {traceback.format_exc()}")
            return {'error': e}


    @staticmethod
    def move_email(host, sender_email, sender_password, email_id, mailbox, destination_folder):
        try:
            # Connect to the IMAP server
            imap_connection = imaplib.IMAP4_SSL(host)
            imap_connection.login(sender_email, sender_password)

            # Select the source mailbox (INBOX)
            try:
                if host == "imap.outlook.com":
                    default_list = {'inbox': 'Inbox', "sent": 'Sent', 'drafts': 'Drafts', "junk": 'Junk', 'trash': 'Deleted', "notes": 'Notes', 'archive': 'Archive'}
                    destination_folder = default_list[destination_folder]
                elif host == "imap.gmail.com":
                    default_list = {'inbox': 'inbox', 'sent': '"[Gmail]/Sent Mail"', 'drafts': '"[Gmail]/Drafts"', 'junk': '"[Gmail]/Spam"', 'trash': '"[Gmail]/Trash"', 'important': '"[Gmail]/Important"', 'all': '"[Gmail]/All Mail"'}
                    destination_folder = default_list[destination_folder]
            except:
                status, folder_list = imap_connection.list()
                if destination_folder not in str(folder_list):
                    EmailAPI.create_folder(host, sender_email, sender_password, destination_folder)
            imap_connection.select(default_list[mailbox.lower()])
            imap_connection.copy(str(email_id), destination_folder)

            imap_connection.logout()
            return True

        except Exception as e:
            EmailAPI.logger.error(f"unable to move email: {traceback.format_exc()}")
            return {'error': e}

    @staticmethod
    def filter_email(emails_data, filter_list):
        emails = []
        for e in emails_data:
            append_email = True
            for item in filter_list:
                if (item in e['from']):
                    append_email = False
                    break

            if append_email:
                emails.append(e)
        return emails

    @staticmethod
    def get_emails(emails_data, filter_list):
        emails = []
        for e in emails_data:
            append_email = False
            for item in filter_list:
                if (item in e['from']):
                    append_email = True
                    break

            if append_email:
                emails.append(e)
        return emails


    @staticmethod
    def auto_emails(host, sender_email, sender_password, mailbox="INBOX", message_type="ALL",
                    delete_ids=[], auto_delete=False, filter_list=[], get_filter=[], mark_as_read=False):
        """
        Connects to an IMAP server and retrieves emails based on the specified criteria.

        Args:
            host (str): The host of the IMAP server. imap.gmail.com, imap.outlook.com
            user (str): The username for authentication.
            password (str): The app password for authentication.
            mailbox (str, optional): The mailbox to select. Defaults to "INBOX". Possible values: ['INBOX', 'SENT', 'DRAFTS', 'JUNK', 'TRASH']
            message_type (str, optional): The criteria to search for emails. Defaults to "ALL". Possible values: ['ALL', 'UNSEEN', 'SEEN']
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
                default_list = {'inbox': 'Inbox', "sent": 'Sent', 'drafts': 'Drafts', "junk": 'Junk', 'trash': 'Deleted', "notes": 'Notes', 'archive': 'Archive'}
            elif host == "imap.gmail.com":
                default_list = {'inbox': 'inbox', 'sent': '"[Gmail]/Sent Mail"', 'drafts': '"[Gmail]/Drafts"', 'junk': '"[Gmail]/Spam"', 'trash': '"[Gmail]/Trash"', 'important': '"[Gmail]/Important"', 'all': '"[Gmail]/All Mail"'}
            else:
                return None

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
                result, data = mail.fetch(email_id, '(RFC822)')
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)

                email_id_str = email_id.decode('utf-8')

                # Extract email details
                email_details = {
                    'id': email_id_str,
                    'from': msg['From'],
                    'to': msg['To'],
                    'cc': msg['Cc'],
                    'bcc': msg['Bcc'],
                    'subject': msg['Subject'],
                    'date': msg['Date'],
                    'reply_to': msg['Reply-To'],
                    'message_id': msg['Message-ID'],
                    'body': '',
                    'attachments': []
                }

                # Extract body
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                email_details['body'] = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                            except UnicodeDecodeError:
                                # Handle decoding errors by skipping problematic characters
                                pass
                        elif part.get_content_maintype() == 'multipart' and part.get('Content-Disposition') is None:
                            continue
                        else:
                            # Extract attachment
                            attachment = {
                                'filename': part.get_filename(),
                                'content_type': part.get_content_type(),
                                'content': base64.b64encode(part.get_payload(decode=True)).decode('utf-8')

                            }
                            email_details['attachments'].append(attachment)
                else:
                    try:
                        email_details['body'] = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                    except UnicodeDecodeError:
                        # Handle decoding errors by skipping problematic characters
                        pass

                emails.append(email_details)

                if message_type == "UNSEEN" and mark_as_read == False:
                    mail.store(email_id, '-FLAGS', '\\Seen')

            if get_filter:
                emails = EmailAPI.get_emails(emails, get_filter)
            elif filter_list:
                emails = EmailAPI.filter_email(emails, filter_list)

            if auto_delete:
                for item in emails:
                    id = item['id']
                    mail.store(id.encode('utf-8'), '+FLAGS', '\\Deleted')
            elif delete_ids:
                for item in emails:
                    id = item['id']
                    if id in delete_ids:
                        mail.store(id.encode('utf-8'), '+FLAGS', '\\Deleted')

            sender_email = []
            for item in emails:
                if '<' in item['from'] and '>' in item['from']:
                    _from = item['from'].split('<')[1].split('>')[0]
                else:
                    _from = item['from']

                if _from not in sender_email:
                    sender_email.append(_from)

            mail.close()
            mail.logout()

            return {"emails": emails, "sender_email": sender_email}
        except Exception as e:
            EmailAPI.logger.error(f"unable to get emails: {traceback.format_exc()}")
            return {'error': e}


    @staticmethod
    def get_new_emails(host, sender_email, sender_password, mailbox="INBOX", message_type="UNSEEN", mark_as_read=True, max_emails=5):
        """
        Connects to an IMAP server and retrieves emails based on the specified criteria.

        Args:
            host (str): The host of the IMAP server. imap.gmail.com, imap.outlook.com
            user (str): The username for authentication.
            password (str): The app password for authentication.
            mailbox (str, optional): The mailbox to select. Defaults to "INBOX". Possible values: ['INBOX', 'SENT', 'DRAFTS', 'JUNK', 'TRASH']
            message_type (str, optional): The criteria to search for emails. Defaults to "ALL". Possible values: ['ALL', 'UNSEEN', 'SEEN']
            mark_as_read (bool, optional): Whether to mark emails as read. Defaults to False.

        Returns:
            list: A list of dictionary containing the email details.
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
                default_list = {'inbox': 'Inbox', "sent": 'Sent', 'drafts': 'Drafts', "junk": 'Junk', 'trash': 'Deleted', "notes": 'Notes', 'archive': 'Archive'}
            elif host == "imap.gmail.com":
                default_list = {'inbox': 'inbox', 'sent': '"[Gmail]/Sent Mail"', 'drafts': '"[Gmail]/Drafts"', 'junk': '"[Gmail]/Spam"', 'trash': '"[Gmail]/Trash"', 'important': '"[Gmail]/Important"', 'all': '"[Gmail]/All Mail"'}
            else:
                return None

            mailbox = default_list[mailbox.lower()]
            # Connect to the IMAP server
            mail = imaplib.IMAP4_SSL(host)
            mail.login(sender_email, sender_password)
            mail.select(mailbox)
            _, email_ids = mail.search(None, message_type)

            new_emails = []
            email_ids_list = email_ids[0].decode().split()  # Decode and split the IDs
            # email_ids_list = email_ids_list[-max_emails:]
            email_count = 0
            
            for email_id in email_ids_list:
                
                if email_count < max_emails:
                    email_details = {}

                    result, data = mail.fetch(email_id, '(RFC822)')
                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    email_id_str = email_id

                    # Extract email details
                    email_details = {
                        'id': email_id_str,
                        'from': msg['From'],
                        'to': msg['To'],
                        'cc': msg['Cc'],
                        'bcc': msg['Bcc'],
                        'subject': msg['Subject'],
                        'date': msg['Date'],
                        'reply_to': msg['Reply-To'],
                        'message_id': msg['Message-ID'],
                        'body': '',
                        'attachments': []
                    }

                    # Extract body
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                try:
                                    email_details['body'] = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                except UnicodeDecodeError:
                                    # Handle decoding errors by skipping problematic characters
                                    pass
                            elif part.get_content_maintype() == 'multipart' and part.get('Content-Disposition') is None:
                                continue
                            else:
                                # Extract attachment
                                attachment = {
                                    'filename': part.get_filename(),
                                    'content_type': part.get_content_type(),
                                    'content': base64.b64encode(part.get_payload(decode=True)).decode('utf-8')

                                }
                                email_details['attachments'].append(attachment)
                    else:
                        try:
                            email_details['body'] = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                        except UnicodeDecodeError:
                            # Handle decoding errors by skipping problematic characters
                            pass

                    if message_type == "UNSEEN" and mark_as_read == False:
                        mail.store(email_id, '-FLAGS', '\\Seen')
                        
                    new_emails.append(email_details)
                else:
                    mail.store(email_id, '-FLAGS', '\\Seen')
                email_count += 1
                    

            mail.close()
            mail.logout()

            return new_emails

        except Exception as e:
            EmailAPI.logger.error(f"unable to get new emails: {traceback.format_exc()}")
            return {'error': e}


    @staticmethod
    def set_email_type(host, sender_email, sender_password, mailbox="INBOX", message_type="UNSEEN", email_id=None):
        try:
            if host == "imap.outlook.com":
                default_list = {'inbox': 'Inbox', "sent": 'Sent', 'drafts': 'Drafts', "junk": 'Junk', 'trash': 'Deleted', "notes": 'Notes', 'archive': 'Archive'}
            elif host == "imap.gmail.com":
                default_list = {'inbox': 'inbox', 'sent': '"[Gmail]/Sent Mail"', 'drafts': '"[Gmail]/Drafts"', 'junk': '"[Gmail]/Spam"', 'trash': '"[Gmail]/Trash"', 'important': '"[Gmail]/Important"', 'all': '"[Gmail]/All Mail"'}
            else:
                return None

            mailbox = default_list[mailbox.lower()]
            # Connect to the IMAP server
            mail = imaplib.IMAP4_SSL(host)
            mail.login(sender_email, sender_password)
            mail.select(mailbox)
            _, email_ids = mail.search(None, message_type)
            email_ids_str = []
            if email_ids:
                email_ids_str = [item.decode('utf-8') for item in email_ids][0]
            if str(email_id) in email_ids_str:
                if message_type.lower() == "UNSEEN".lower():
                    mail.store(str(email_id).encode('utf-8'), '+FLAGS', '\\Seen')
                elif message_type.lower() == "SEEN".lower():
                    mail.store(str(email_id).encode('utf-8'), '-FLAGS', '\\Seen')

            mail.close()
            mail.logout()
            return True
        except Exception as e:
                EmailAPI.logger.error(f"unable to email type: {traceback.format_exc()}")
                return {'error': e}


    @staticmethod
    def create_folder(host, sender_email, sender_password, folder_name):
        try:
            # Connect to the IMAP server
            imap_connection = imaplib.IMAP4_SSL(host)
            imap_connection.login(sender_email, sender_password)

            # Create the folder
            imap_connection.create(folder_name)

            imap_connection.logout()
            return True
        except Exception as e:
            EmailAPI.logger.error(f"unable to create folder: {traceback.format_exc()}")
            return {'error': e}

