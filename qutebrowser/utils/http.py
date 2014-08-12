# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2014 Florian Bruhin (The Compiler) <mail@qutebrowser.org>
#
# This file is part of qutebrowser.
#
# qutebrowser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# qutebrowser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with qutebrowser.  If not, see <http://www.gnu.org/licenses/>.

"""Other utilities which don't fit anywhere else. """


import os.path
import rfc6266
from qutebrowser.utils.log import misc as logger

from PyQt5.QtNetwork import QNetworkRequest


def parse_content_disposition(reply):
    """Parse a content_disposition header.

    Args:
        reply: The QNetworkReply to get a filename for.

    Return:
        A (is_inline, filename) tuple.
    """
    is_inline = True
    filename = None
    # First check if the Content-Disposition header has a filename
    # attribute.
    if reply.hasRawHeader('Content-Disposition'):
        # We use the unsafe variant of the filename as we sanitize it via
        # os.path.basename later.
        try:
            content_disposition = rfc6266.parse_headers(
                bytes(reply.rawHeader('Content-Disposition')), relaxed=True)
            filename = content_disposition.filename_unsafe
        except UnicodeDecodeError as e:
            logger.warning("Error while getting filename: {}: {}".format(
                e.__class__.__name__, e))
            filename = None
        else:
            is_inline = content_disposition.is_inline
    # Then try to get filename from url
    if not filename:
        filename = reply.url().path()
    # If that fails as well, use a fallback
    if not filename:
        filename = 'qutebrowser-download'
    return is_inline, os.path.basename(filename)


def parse_content_type(reply):
    """Parse a Content-Type header.

    The parsing done here is very cheap, as we really only want to get the
    Mimetype. Parameters aren't parsed specially.

    Args:
        reply: The QNetworkReply to handle.

    Return:
        A [mimetype, rest] list, or [None, None] if unset.
        Rest can be None.
    """
    content_type = reply.header(QNetworkRequest.ContentTypeHeader)
    if content_type is None:
        return [None, None]
    if ';' in content_type:
        ret = content_type.split(';', maxsplit=1)
    else:
        ret = [content_type, None]
    ret[0] = ret[0].strip()
    return ret


def change_content_type(reply, mapping):
    """Change a content-type of a QNetworkReply.

    Args:
        reply: The QNetworkReply to handle.
        mapping: A mapping of source to target content types.

    Return:
        None (modifies the passed reply).
    """
    content_type, rest = parse_content_type(reply)
    if content_type is None:
        return
    try:
        content_type = mapping[content_type]
    except KeyError:
        return
    if rest is not None:
        header = ';'.join((content_type, rest))
    else:
        header = content_type
    reply.setHeader(QNetworkRequest.ContentTypeHeader, header)
