import datetime
import email
import email.header
import email.utils
import glob
import logging
import sys
from dataclasses import dataclass
from typing import Iterator, Union

from automatic_journal.common import Item

logger = logging.getLogger(__name__)

THeader = Union[str, email.header.Header, None]


def load_config(config_json: dict) -> dict:
    try:
        received_pathname = config_json['maildir']['received_pathname']
        sent_pathname = config_json['maildir']['sent_pathname']
    except (KeyError, TypeError):
        logger.error('Invalid config')
        sys.exit(1)
    return {
        'received_pathname': received_pathname,
        'sent_pathname': sent_pathname,
    }


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
    if not header:
        raise Exception('Missing Date header')
    header_str = str(header)
    return email.utils.parsedate_to_datetime(header_str)


@dataclass
class Message:
    subject: str
    from_: str
    to_: str
    dt: datetime.datetime
    sent: bool

    @property
    def text(self):
        if self.sent:
            return f'To {self.to_}: {self.subject}'.strip()
        return f'From {self.from_}: {self.subject}'.strip()


def _read_messages(pathname: str, sent: bool) -> Iterator[Item]:
    for path in glob.glob(pathname):
        logger.info('Reading message %s', path)
        with open(path, 'rb') as f:
            email_message = email.message_from_binary_file(f)
        message = Message(
            subject=_decode_header(email_message['Subject']),
            from_=_parse_address(email_message['From']),
            to_=_parse_address(email_message['To']),
            dt=_parse_date(email_message['Date']),
            sent=sent,
        )
        yield Item(dt=message.dt, text=message.text, subprovider=pathname)


def read_messages(config: dict) -> Iterator[Item]:
    yield from _read_messages(config['received_pathname'], sent=False)
    yield from _read_messages(config['sent_pathname'], sent=True)


def main(config_json: dict):
    config = load_config(config_json)
    return read_messages(config)
