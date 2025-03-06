import re
from html.parser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []

    def handle_data(self, d):
        self.text.append(d)

    def get_data(self):
        return ''.join(self.text)
    
class PhonemeUtils:
    
    @staticmethod
    def phonetic_format(text, mapping):
        """
        This function accepts text and a mapping of words and related replacements. It
        converts phone numbers, emails, web addresses and supplied strings in mapping
        into a phonetic format so they may be fed through a TTS engine for proper pronunciation.
        """

        # Process phone numbers
        text = PhonemeUtils.process_phone_numbers(text)
        
        # Handle URLs and Emails
        url_pattern = re.compile(r'\b(?:http|https)://[^\s]*\b')
        email_pattern = re.compile(r'\b([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b')
        markdown_pattern = re.compile(r'\[([^\]]*)\]\((http[^\s)]+)\)')

        # Process urls
        text = PhonemeUtils.process_urls(text, url_pattern, markdown_pattern)

        # Process emails
        text = PhonemeUtils.process_emails(text, email_pattern)

        # Handle word replacement
        text = PhonemeUtils.process_word_replacements(text, mapping)
        
        # Handle markdown / HTML
        text = PhonemeUtils.remove_markdown(text)

        return text
    
    
    @staticmethod 
    def process_phone_numbers(text):
        # Handle phone numbers
        phone_patterns = [
            (r'\b(\d)(\d)(\d)[ -](\d)(\d)(\d)[ -](\d)(\d)(\d)(\d)\b', r'\1-\2-\3-\4-\5-\6-\7-\8-\9-\10'),  # Matches 123-456-7890
            (r'\b\((\d)(\d)(\d)\)[ -](\d)(\d)(\d)[ -](\d)(\d)(\d)\b', r'\1-\2-\3-\4-\5-\6-\7-\8-\9'),  # Matches (123) 456 789 and (123)-456-789
            (r'\b(\d)(\d)(\d)[ -](\d)(\d)(\d)(\d)\b', r'\1-\2-\3-\4-\5-\6-\7')  # Matches 456-7890
        ]
        
        for pattern, replacement in phone_patterns:
            if re.search(pattern, text):  # Check if the pattern matches
                text = re.sub(pattern, replacement, text)

        return text

    
    @staticmethod
    def process_urls(text, url_pattern, markdown_pattern):
        
        def process_url(url):
            protocol, remainder = url.split('://', 1)
            parts = remainder.split('/', 1)
            domain = parts[0]
            path = parts[1] if len(parts) > 1 else ''
            return PhonemeUtils.create_url_tts(protocol, domain, path)

        # Process markdown-styled URLs
        markdown_urls = markdown_pattern.findall(text)
        for label, url in markdown_urls:
            if re.match(url_pattern, url):
                tts = process_url(url)
                text = text.replace(f"[{label}]({url})", tts, 1)

        # Process remaining plain URLs
        plain_urls = url_pattern.findall(text)
        for url in plain_urls:
            tts = process_url(url)
            text = text.replace(url, tts, 1)

        return text

    
    @staticmethod
    def create_url_tts(protocol, domain, path):
        protocol = protocol.replace('https', 'h-t-t-p-s').replace('http', 'h-t-t-p')
        tts = protocol + ' colon slash slash '
        tts += PhonemeUtils.create_tts(domain, ' dot ', '.')
        if path:
            tts += ' slash ' + PhonemeUtils.create_tts(path, ' slash ', '/')
        return tts + ' '

    def process_emails(text, email_pattern):
        emails = re.findall(email_pattern, text)
        for email in emails:
            username, domain = email.split('@')
            tts = PhonemeUtils.create_tts(username, ' dot ', '.') + ' at '
            tts += PhonemeUtils.create_tts(domain, ' dot ', '.')
            text = text.replace(email, tts, 1)
        return text

    
    @staticmethod    
    def process_word_replacements(text, mapping):
        # Use regex to replace exact matches accounting for punctuation, spaces, etc.
        # Note: Sorting longest first ensures longer substrings with embedded shorter keys don't get prematurely replaced.
        for key in sorted(mapping, key=len, reverse=True):
            # Escaping the key is crucial as it might contain special regex characters.
            escaped_key = re.escape(key)
            # Using word boundaries or equivalent to make sure we match whole terms
            pattern = r'(?<!\w)(' + escaped_key + r')(?!\w)'
            # Replace case-insensitively
            text = re.sub(pattern, mapping[key], text, flags=re.I)
        return text

    
    @staticmethod    
    def convert_each_char(part):
        """ Converts each character in the part to its phonetic equivalent. """
        mappings = {
            '.': ' dot ',
            '-': ' dash ',
            '/': ' slash '
        }
        return ''.join(mappings.get(char, char) + '-' if char.isalnum() else mappings.get(char, '') for char in part)

    
    @staticmethod
    def create_tts(segment, separator, splitter):
        tts = ''
        parts = segment.split(splitter)
        for part in parts[:-1]:
            tts += PhonemeUtils.convert_each_char(part) + separator
        tts += PhonemeUtils.convert_each_char(parts[-1])
        return tts


    @staticmethod
    def strip_tags(html):
        s = MLStripper()
        s.feed(html)
        return s.get_data()


    @staticmethod    
    def remove_markdown(md):
        # replace headers
        md = re.sub(r"^#.*$", "", md, flags=re.MULTILINE)
        # replace links and images
        md = re.sub(r"\[.*\]\(.*\)", "", md)
        # replace bold, italic, code text
        md = re.sub(r"[\*\~\`]{1,2}", "", md)
        # replace list, quote and horizontal rule
        md = re.sub(r"[-\*]{3,}|[>\-\*]\s", "", md)
        # replace html tags if any
        md = PhonemeUtils.strip_tags(md)
        return md.strip()