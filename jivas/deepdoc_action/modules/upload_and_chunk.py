import os
import re
import mimetypes
import sys
import nltk

# Download NLTK data
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('wordnet')

# Get the directory where the script is running
current_dir = os.path.dirname(os.path.abspath(__file__))

# Ensure the current directory is in sys.path
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from rag.app.naive import chunk
except ModuleNotFoundError as e:
    print(f"Module import failed: {e}. Check if 'rag/' contains an __init__.py file.")

import json
import requests
from urllib.parse import urlparse, unquote
from rag.app.naive import chunk
import logging
logging.basicConfig(level = logging.INFO)

def dummy(prog=None, msg=""):
    """
    Sample callback.
    """
    print(prog)
    print(msg)

def get_filename_from_cd(cd):
    """
    Extract filename from Content-Disposition header.
    """
    if not cd:
        return None
    fname = re.findall('filename="([^"]+)"', cd)
    if not fname:
        # Try without quotes
        fname = re.findall('filename=([^;]+)', cd)
    return fname[0] if fname else None

def get_filename(response, url):
    """
    Determine the filename using the following steps:
    1. Check Content-Disposition header.
    2. Fallback to URL extraction.
    3. Ensure the filename has an extension by using the MIME type.
    """
    # Attempt to extract from Content-Disposition header.
    cd = response.headers.get('content-disposition')
    filename = get_filename_from_cd(cd) if cd else None
    if filename:
        filename = unquote(filename)
    else:
        # Fallback: extract filename from URL.
        parsed = urlparse(url)
        filename = unquote(os.path.basename(parsed.path))
    
    # If there's no file extension, try to guess one using the Content-Type header.
    if not os.path.splitext(filename)[1]:
        content_type = response.headers.get('Content-Type')
        ext = mimetypes.guess_extension(content_type)
        if ext:
            filename = filename + ext
        else:
            filename = filename + ".bin"  # default extension if all else fails
    return filename

class UploadAndChunk:
    def __init__(self, **kwargs):
        pass

    @staticmethod
    def upload_and_chunk(urls: list = []):
        # Create a temporary directory for processing files
        temp_dir = os.path.join(os.getcwd(), ".temp")
        os.makedirs(temp_dir, exist_ok=True)

        # Create the .images directory for saving images if it doesn't exist
        images_dir = os.path.join(os.getcwd(), ".images")
        os.makedirs(images_dir, exist_ok=True)

        # List to store the paths of files to be processed
        file_paths = []

        # Process files provided as URLs
        for url in urls:
            try:
                response = requests.get(
                    url, 
                    stream=False, 
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                        "Accept": "*/*"
                    }
                )
                if response.status_code == 200:
                    # Generate a unique filename; you could also attempt to extract the original filename or extension from the URL if needed.
                    unique_filename = get_filename(response, url)
                    temp_file_path = os.path.join(temp_dir, unique_filename)
                    with open(temp_file_path, 'wb') as f:
                        f.write(response.content)
                    file_paths.append(temp_file_path)
                else:
                    print(f"Failed to download from URL: {url}, status code: {response.status_code}")
            except Exception as e:
                print(f"Exception while downloading {url}: {e}")
                continue

        if not file_paths:
            ValueError("No files to process. Please provide valid URLs or upload files.")

        results = []

        # Process each file (either uploaded or downloaded)
        for temp_file_path in file_paths:
            try:
                result = chunk(temp_file_path, binary=False, from_page=0, to_page=100000,
                            lang="english", callback=dummy)

                data = result

                converted = []
                image_counter = 1

                for item in data:
                    text = item.get("content_with_weight", "")
                    metadata = {}
                    for key, value in item.items():
                        if key == "content_with_weight":
                            continue

                        if key == "position_int":
                            if isinstance(value, list):
                                new_positions = []
                                for pos in value:
                                    if isinstance(pos, (list, tuple)):
                                        new_positions.append(list(pos))
                                    else:
                                        new_positions.append(pos)
                                metadata[key] = new_positions
                            else:
                                metadata[key] = value
                        else:
                            try:
                                json.dumps(value)
                                metadata[key] = value
                            except (TypeError, OverflowError):
                                metadata[key] = str(value)

                    converted.append({
                        "id": "",
                        "metadata": metadata,
                        "text": text
                    })
                results.extend(converted)
            except Exception as e:
                return ValueError(f"Error processing file {temp_file_path}: {e}")
            finally:
                # Ensure the temporary file is removed to keep the endpoint stateless.
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            
            return results

if __name__ == "__main__":
    # Example usage
    results = UploadAndChunk.upload_and_chunk(["https://arxiv.org/pdf/2305.09864.pdf"])

    # print("Final Results:", results)