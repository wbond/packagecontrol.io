import bz2
import gzip
import hashlib
import os

def store_asset(filename, content):
    """
    Stores an asset uncompressed and as gzip, bzip2 archive.

    :param filename:
        The filename
    :param content:
        The content
    """
    new_filename     = filename + '-new'
    new_filename_gz  = filename + '.gz-new'
    new_filename_bz2 = filename + '.bz2-new'
    filename_gz      = filename + '.gz'
    filename_bz2     = filename + '.bz2'
    filename_sha512  = filename + '.sha512'

    encoded_content = content.encode('utf-8')
    content_hash = hashlib.sha512(encoded_content).hexdigest().encode('utf-8')

    # Abort, if content hasn't changed so http server continues to return 304
    # if clients already have a locally cached copy.
    try:
        with open(filename_sha512, 'rb') as f:
            if f.read().strip() == content_hash:
                return
    except FileNotFoundError:
        pass

    with open(new_filename, 'wb') as f:
        f.write(encoded_content)

    os.rename(new_filename, filename)

    with gzip.open(new_filename_gz, 'w') as f:
        f.write(encoded_content)

    os.rename(new_filename_gz, filename_gz)

    with bz2.open(new_filename_bz2, 'w') as f:
        f.write(encoded_content)

    os.rename(new_filename_bz2, filename_bz2)

    with open(filename_sha512, 'wb') as f:
        f.write(content_hash)
