import datetime
import email
import email.header
import email.utils
import glob
import logging
from pathlib import Path
from typing import Iterator, Union

from automatic_diary.model import Item

logger = logging.getLogger(__name__)
provider = Path(__file__).parent.name

THeader = Union[str, email.header.Header, None]


def _decode_header(header: THeader) -> str:
    if not header:
        return ''
    first_charset = email.header.decode_header(header)[0]
    header_bytes, _ = first_charset
    if isinstance(header_bytes, str):
        return header_bytes
    return header_bytes.decode(errors='ignore')


def _parse_address(header: THeader) -> str:
    if not header:
        return ''
    header_str = str(header)
    name, address = email.utils.parseaddr(header_str)
    if name:
        return _decode_header(name)
    return address


def _parse_date(header: THeader) -> datetime.datetime:
    header_str = str(header)
    return email.utils.parsedate_to_datetime(header_str)


def _format_text(from_: str, to_: str, subject: str, sent: bool) -> str:
    if sent:
        return f'To {to_}: {subject}'.strip()
    return f'From {from_}: {subject}'.strip()


def _read_messages(pathname: str, sent: bool) -> Iterator[Item]:
    for path in glob.glob(pathname):
        logger.info('Reading message %s', path)
        with open(path, 'rb') as f:
            email_message = email.message_from_binary_file(f)
        if not email_message['Date']:
            logger.warning('Skipping message without date: %s', path)
            continue
        datetime_ = _parse_date(email_message['Date'])
        text = _format_text(
            _parse_address(email_message['From']),
            _parse_address(email_message['To']),
            _decode_header(email_message['Subject']),
            sent,
        )
        yield Item.normalized(
            datetime_=datetime_,
            text=text,
            provider=provider,
            subprovider=pathname,
        )


def main(config: dict, *args, **kwargs) -> Iterator[Item]:
    yield from _read_messages(config['received_pathname'], sent=False)
    yield from _read_messages(config['sent_pathname'], sent=True)
