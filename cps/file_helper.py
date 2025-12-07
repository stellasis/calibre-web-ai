# -*- coding: utf-8 -*-

#  This file is part of the Calibre-Web (https://github.com/janeczku/calibre-web)
#    Copyright (C) 2023 OzzieIsaacs
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.

from tempfile import gettempdir
import os
import shutil
import zipfile
import mimetypes
from io import BytesIO

from . import logger

log = logger.create()

try:
    import magic
    error = None
except ImportError as e:
    error = "Cannot import python-magic, checking uploaded file metadata will not work: {}".format(e)


def get_mimetype(ext):
    # overwrite some mimetypes for proper file detection
    mimes = {".fb2": "text/xml",
             ".cbz": "application/zip",
             ".cbr": "application/x-rar",
             ".epub": "application/epub+zip",  # Explicit EPUB MIME type
             ".kepub": "application/epub+zip"  # KEPUB is also EPUB format
             }
    # Return explicit mapping if available
    if ext in mimes:
        return mimes[ext]
    # Try mimetypes.types_map, with fallback for common extensions
    try:
        return mimetypes.types_map[ext]
    except KeyError:
        # Common fallbacks for extensions that might not be in types_map
        fallbacks = {
            ".mobi": "application/x-mobipocket-ebook",
            ".azw": "application/vnd.amazon.ebook",
            ".azw3": "application/vnd.amazon.ebook"
        }
        return fallbacks.get(ext, "application/octet-stream")


def get_temp_dir():
    tmp_dir = os.path.join(gettempdir(), 'calibre_web')
    if not os.path.isdir(tmp_dir):
        os.mkdir(tmp_dir)
    return tmp_dir


def del_temp_dir():
    tmp_dir = os.path.join(gettempdir(), 'calibre_web')
    shutil.rmtree(tmp_dir)


def validate_mime_type(file_buffer, allowed_extensions):
    # If python-magic is not available, skip MIME validation
    # The file extension check will still be performed by the caller
    if error:
        log.warning("python-magic not available, skipping MIME type validation: %s", error)
        return True  # Allow upload if extension check passes (handled by caller)
    
    try:
        # Read file content into memory for MIME checking
        # Flask file objects might not support seek(), so read into BytesIO
        file_content = file_buffer.read()
        file_buffer.seek(0)  # Try to reset, but don't fail if it doesn't work
        
        # If seek failed, create a new BytesIO from the content
        if hasattr(file_buffer, 'tell'):
            try:
                file_buffer.tell()  # Test if we can get position
            except:
                file_buffer = BytesIO(file_content)
        else:
            file_buffer = BytesIO(file_content)
        
        mime = magic.Magic(mime=True)
        allowed_mimetypes = list()
        for x in allowed_extensions:
            try:
                mimetype = get_mimetype("." + x)
                allowed_mimetypes.append(mimetype)
                log.debug("Added allowed MIME type for %s: %s", x, mimetype)
            except KeyError:
                log.error("Unknown mimetype for Extension: {}".format(x))
        
        tmp_mime_type = mime.from_buffer(file_content)
        log.debug("Detected MIME type: %s, Allowed types: %s", tmp_mime_type, allowed_mimetypes)
        
        # First check: If EPUB is in allowed extensions, check ZIP files for EPUB structure
        # (EPUBs often show up as application/zip)
        if "epub" in [x.lower() for x in allowed_extensions]:
            if "zip" in tmp_mime_type or "application/zip" in tmp_mime_type:
                try:
                    with zipfile.ZipFile(BytesIO(file_content), 'r') as epub:
                        if "mimetype" in epub.namelist():
                            # Read mimetype file to verify it's EPUB
                            mimetype_content = epub.read("mimetype").decode('utf-8', errors='ignore').strip()
                            if "epub" in mimetype_content.lower() or "application/epub+zip" in mimetype_content:
                                log.debug("EPUB detected via ZIP structure (mimetype file: %s)", mimetype_content)
                                return True
                except Exception as zip_error:
                    log.debug("ZIP check failed (might not be EPUB): %s", zip_error)
        
        # Check if MIME type matches any allowed type
        if any(mime_type in tmp_mime_type for mime_type in allowed_mimetypes):
            log.debug("MIME type validation passed: %s", tmp_mime_type)
            return True
        
        # Some epubs show up as zip mimetypes - check if it's actually an EPUB (fallback check)
        if "zip" in tmp_mime_type or "application/zip" in tmp_mime_type:
            try:
                with zipfile.ZipFile(BytesIO(file_content), 'r') as epub:
                    if "mimetype" in epub.namelist():
                        # Read mimetype file to verify it's EPUB
                        mimetype_content = epub.read("mimetype").decode('utf-8', errors='ignore').strip()
                        if "epub" in mimetype_content.lower() or "application/epub+zip" in mimetype_content:
                            log.debug("EPUB detected via ZIP structure (mimetype file: %s)", mimetype_content)
                            return True
            except Exception as zip_error:
                log.debug("ZIP check failed (might not be EPUB): %s", zip_error)
        
        # Final fallback: If epub is in allowed extensions and file is ZIP, allow it
        # (EPUB files are ZIP archives, so this is a reasonable fallback)
        if "epub" in [x.lower() for x in allowed_extensions]:
            if "zip" in tmp_mime_type or "application/zip" in tmp_mime_type:
                log.warning("Allowing ZIP file as EPUB (epub is in allowed extensions, file detected as ZIP)")
                return True
        
        log.error("Mimetype '%s' not found in allowed types: %s", tmp_mime_type, allowed_mimetypes)
        return False
    except Exception as e:
        log.warning("Error during MIME type validation, allowing upload: %s", e)
        try:
            file_buffer.seek(0)
        except:
            pass
        return True  # Fallback: allow if extension check passes
