"""Utility functions for phoneme interact action."""

import re
from html.parser import HTMLParser
from typing import Dict


class MLStripper(HTMLParser):
    """HTML parser to strip tags from text."""

    def __init__(self) -> None:
        """Initializes the HTML parser."""
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text: list[str] = []

    def handle_data(self, d: str) -> None:
        """Handles data."""
        self.text.append(d)

    def get_data(self) -> str:
        """Returns the data."""
        return "".join(self.text)


class PhonemeUtils:
    """Utility functions for phoneme interact action."""

    @staticmethod
    def phonetic_format(text: str, mapping: Dict[str, str]) -> str:
        """
        Converts phone numbers, emails, web addresses, and supplied strings
        in mapping into a phonetic format for TTS engines.
        """

        # Process phone numbers
        text = PhonemeUtils.process_phone_numbers(text)

        # Handle URLs and Emails
        url_pattern = re.compile(r"\b(?:http|https)://[^\s]*\b")
        email_pattern = re.compile(
            r"\b([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b"
        )
        markdown_pattern = re.compile(r"\[([^\]]*)\]\((http[^\s)]+)\)")

        # Process URLs and Emails
        text = PhonemeUtils.process_urls(text, url_pattern, markdown_pattern)
        text = PhonemeUtils.process_emails(text, email_pattern)

        # Handle word replacement
        text = PhonemeUtils.process_word_replacements(text, mapping)

        # Handle markdown / HTML
        text = PhonemeUtils.remove_markdown(text)

        return text

    @staticmethod
    def process_phone_numbers(text: str) -> str:
        """Converts phone numbers into a phonetic format."""

        phone_patterns = [
            (
                r"\b(\d)(\d)(\d)[ -](\d)(\d)(\d)[ -](\d)(\d)(\d)(\d)\b",
                r"\1-\2-\3-\4-\5-\6-\7-\8-\9-\10",
            ),
            (
                r"\b\((\d)(\d)(\d)\)[ -](\d)(\d)(\d)[ -](\d)(\d)(\d)\b",
                r"\1-\2-\3-\4-\5-\6-\7-\8-\9",
            ),
            (r"\b(\d)(\d)(\d)[ -](\d)(\d)(\d)(\d)\b", r"\1-\2-\3-\4-\5-\6-\7"),
        ]

        for pattern, replacement in phone_patterns:
            text = re.sub(pattern, replacement, text)

        return text

    @staticmethod
    def process_urls(
        text: str, url_pattern: re.Pattern, markdown_pattern: re.Pattern
    ) -> str:
        """Converts URLs into a phonetic format."""

        def process_url(url: str) -> str:
            """Converts a URL into a phonetic format."""
            protocol, remainder = url.split("://", 1)
            parts = remainder.split("/", 1)
            domain = parts[0]
            path = parts[1] if len(parts) > 1 else ""
            return PhonemeUtils.create_url_tts(protocol, domain, path)

        markdown_urls = markdown_pattern.findall(text)
        for label, url in markdown_urls:
            if re.match(url_pattern, url):
                tts = process_url(url)
                text = text.replace(f"[{label}]({url})", tts, 1)

        plain_urls = url_pattern.findall(text)
        for url in plain_urls:
            tts = process_url(url)
            text = text.replace(url, tts, 1)

        return text

    @staticmethod
    def create_url_tts(protocol: str, domain: str, path: str) -> str:
        """Creates a phonetic representation of a URL."""
        protocol = protocol.replace("https", "h-t-t-p-s").replace("http", "h-t-t-p")
        tts = protocol + " colon slash slash "
        tts += PhonemeUtils.create_tts(domain, " dot ", ".")
        if path:
            tts += " slash " + PhonemeUtils.create_tts(path, " slash ", "/")
        return tts + " "

    @staticmethod
    def process_emails(text: str, email_pattern: re.Pattern) -> str:
        """Converts emails into a phonetic format."""
        emails = re.findall(email_pattern, text)
        for email in emails:
            username, domain = email.split("@")
            tts = PhonemeUtils.create_tts(username, " dot ", ".") + " at "
            tts += PhonemeUtils.create_tts(domain, " dot ", ".")
            text = text.replace(email, tts, 1)
        return text

    @staticmethod
    def process_word_replacements(text: str, mapping: Dict[str, str]) -> str:
        """Replaces words in the text with their phonetic equivalents."""
        for key in sorted(mapping, key=len, reverse=True):
            escaped_key = re.escape(key)
            pattern = r"(?<!\w)(" + escaped_key + r")(?!\w)"
            text = re.sub(pattern, mapping[key], text, flags=re.I)
        return text

    @staticmethod
    def convert_each_char(part: str) -> str:
        """Converts each character in the part to its phonetic equivalent."""
        mappings = {".": " dot ", "-": " dash ", "/": " slash "}
        return "".join(
            mappings.get(char, char) + "-" if char.isalnum() else mappings.get(char, "")
            for char in part
        )

    @staticmethod
    def create_tts(segment: str, separator: str, splitter: str) -> str:
        """Creates a phonetic representation of a segment."""
        tts = ""
        parts = segment.split(splitter)
        for part in parts[:-1]:
            tts += PhonemeUtils.convert_each_char(part) + separator
        tts += PhonemeUtils.convert_each_char(parts[-1])
        return tts

    @staticmethod
    def strip_tags(html: str) -> str:
        """Strips HTML tags from the given text."""
        s = MLStripper()
        s.feed(html)
        return s.get_data()

    @staticmethod
    def remove_markdown(md: str) -> str:
        """Removes markdown from the given text."""
        md = re.sub(r"^#.*$", "", md, flags=re.MULTILINE)
        md = re.sub(r"\[.*\]\(.*\)", "", md)
        md = re.sub(r"[\*\~\`]{1,2}", "", md)
        md = re.sub(r"[-\*]{3,}|[>\-\*]\s", "", md)
        md = PhonemeUtils.strip_tags(md)
        return md.strip()
