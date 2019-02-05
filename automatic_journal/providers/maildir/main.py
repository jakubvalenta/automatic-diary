import csv
import datetime
import email
import email.header
import email.utils
import glob
import json
import logging
import sys
from dataclasses import dataclass
from functools import partial, reduce
from typing import Iterable, Iterator, Tuple, Union

logger = logging.getLogger(__name__)

THeader = Union[str, email.header.Header, None]


def load_config(path: str) -> dict:
    with open(path) as f:
        config = json.load(f)
    try:
        received_pathname = config['maildir']['received_pathname']
        sent_pathname = config['maildir']['sent_pathname']
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
            return f'To {self.to_}: {self.subject}'
        return f'From {self.from_}: {self.subject}'


def _read_messages(pathname: str, sent: bool) -> Iterator[Tuple[Message, str]]:
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
        yield message, pathname


def read_messages(config: dict) -> Iterator[Tuple[Message, str]]:
    yield from _read_messages(config['received_pathname'], sent=False)
    yield from _read_messages(config['sent_pathname'], sent=True)


def format_csv(
    messages_and_pathnames: Iterable[Tuple[Message, str]], provider: str
) -> Iterator[Tuple[str, str, str, str]]:
    for message, pathname in messages_and_pathnames:
        yield (message.dt.isoformat(), provider, pathname, message.text)


def chain(*funcs):
    def wrapped(initializer):
        return reduce(lambda x, y: y(x), funcs, initializer)

    return wrapped


def main(config_path: str, csv_path: str):
    config = load_config(config_path)
    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        chain(
            read_messages,
            partial(format_csv, provider='maildir'),
            writer.writerows,
        )(config)
