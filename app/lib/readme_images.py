import re
import os
import hashlib
from urllib.parse import urlparse

from .package_control.download_manager import downloader
from .package_control.downloaders.downloader_exception import DownloaderException


project_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
readme_img_dir = os.path.join(project_dir, 'readmes', 'img')


def cache(settings, rendered_html):
    urls = re.findall('<img.*? src="([^"]+)"', rendered_html)
    for url in urls:
        with downloader(url, settings) as manager:
            path = urlparse(url)[2]
            filename = os.path.basename(path)
            ext = os.path.splitext(filename)[1].lower()
            sha1 = hashlib.sha1(url.encode('utf-8')).hexdigest()
            local_filename = sha1 + ext
            local_path = os.path.join(readme_img_dir, local_filename)

            try:
                data = manager.fetch(url, 'fetching readme image')

                # Detect file extension by file contents
                if ext == '':
                    length = len(data)

                    if data[0:8] == b'\x89PNG\r\n\x1A\n':
                        ext = '.png'
                    elif data[0:6] == b'GIF87a' or data[0:6] == b'GIF89a':
                        ext = '.gif'
                    elif (length > 10 and data[6:10] in [b'JFIF', b'Exif']) or (length > 24 and data[0:4] == b'\xFF\xD8\xFF\xED' and data[20:24] == b'8BIM'):
                        ext = '.jpg'
                    elif data[0:128].find(b'<svg') != -1:
                        ext = '.svg'

                with open(local_path, 'wb') as f:
                    f.write(data)
                local_url = '/readmes/img/%s' % local_filename
                rendered_html = rendered_html.replace(url, local_url)

            except (DownloaderException):
                regex = '<img.*? src="' + re.escape(url) + '"[^>]+>'
                rendered_html = re.sub(regex, '', rendered_html)

    return rendered_html

