#!/usr/bin/env python
# pylint: disable=redefined-builtin, no-name-in-module
#
# A library that provides a Python interface to the Telegram Bot API
# Copyright (C) 2015-2022
# Leandro Toledo de Souza <devs@python-telegram-bot.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser Public License for more details.
#
# You should have received a copy of the GNU Lesser Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].
"""This module contains an object that represents a Telegram InputFile."""

import imghdr
import logging
import mimetypes
from pathlib import Path
from typing import IO, Optional, Tuple, Union
from uuid import uuid4

DEFAULT_MIME_TYPE = 'application/octet-stream'
logger = logging.getLogger(__name__)


class InputFile:
    """This object represents a Telegram InputFile.

    Args:
        obj (:term:`file object` | :obj:`bytes`): An open file descriptor or the files content as
            bytes.
        filename (:obj:`str`, optional): Filename for this InputFile.
        attach (:obj:`bool`, optional): Whether this should be send as one file or is part of a
            collection of files.

    Raises:
        TelegramError

    Attributes:
        input_file_content (:obj:`bytes`): The binary content of the file to send.
        filename (:obj:`str`): Optional. Filename for the file to be sent.
        attach (:obj:`str`): Optional. Attach id for sending multiple files.
        mimetype (:obj:`str`): Optional. The mimetype inferred from the file to be sent.

    """

    __slots__ = ('filename', 'attach', 'input_file_content', 'mimetype')

    def __init__(self, obj: Union[IO, bytes], filename: str = None, attach: bool = None):
        if isinstance(obj, bytes):
            self.input_file_content = obj
        else:
            self.input_file_content = obj.read()
        self.attach = 'attached' + uuid4().hex if attach else None

        if (
            not filename
            and hasattr(obj, 'name')
            and not isinstance(obj.name, int)  # type: ignore[union-attr]
        ):
            filename = Path(obj.name).name  # type: ignore[union-attr]

        image_mime_type = self.is_image(self.input_file_content)
        if image_mime_type:
            self.mimetype = image_mime_type
        elif filename:
            self.mimetype = mimetypes.guess_type(filename)[0] or DEFAULT_MIME_TYPE
        else:
            self.mimetype = DEFAULT_MIME_TYPE

        self.filename = filename or self.mimetype.replace('/', '.')

    @property
    def field_tuple(self) -> Tuple[str, bytes, str]:  # skipcq: PY-D0003
        return self.filename, self.input_file_content, self.mimetype

    @staticmethod
    def is_image(stream: bytes) -> Optional[str]:
        """Check if the content file is an image by analyzing its headers.

        Args:
            stream (:obj:`bytes`): A byte stream representing the content of a file.

        Returns:
            :obj:`str` | :obj:`None`: The mime-type of an image, if the input is an image, or
            :obj:`None` else.

        """
        try:
            image = imghdr.what(None, stream)
            if image:
                return f'image/{image}'
            return None
        except Exception:
            logger.debug(
                "Could not parse file content. Assuming that file is not an image.", exc_info=True
            )
            return None

    @staticmethod
    def is_file(obj: object) -> bool:  # skipcq: PY-D0003
        return hasattr(obj, 'read')

    def to_dict(self) -> Optional[str]:
        """See :meth:`telegram.TelegramObject.to_dict`."""
        if self.attach:
            return 'attach://' + self.attach
        return None
