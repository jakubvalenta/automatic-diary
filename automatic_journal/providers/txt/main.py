import datetime
import logging
import re
import sys
from typing import IO, Iterator, Optional

from more_itertools import peekable

from automatic_journal.common import Item

logger = logging.getLogger(__name__)


def load_config(config_json: dict) -> dict:
    try:
        path = config_json['txt']['paths']
    except (KeyError, TypeError):
        logger.error('Invalid config')
        sys.exit(1)
    return {'path': path}


regex_heading = re.compile(r'^(?P<date>\d{4}-\d{2}-\d{2})')
regex_content = re.compile(r'^(?P<indent> +)(?P<text>.+)$')


def parse_txt(
    f: IO, subprovider: str, indent_spaces: int = 4, sep: str = ': '
) -> Item:
    current_date: Optional[datetime.date] = None
    stack = []
    lines = peekable(f)
    for line in lines:
        line_clean = line.rstrip()
        if not line_clean:
            continue
        print(line_clean)
        # Title line
        m = regex_heading.match(line_clean)
        if m:
            if stack:
                text = sep.join(stack)
                print('=>', text)
                yield Item(dt=current_date, text=text, subprovider=subprovider)
                stack.clear()
            date_str = m.group('date')
            current_date = datetime.datetime.strptime(
                date_str, '%Y-%m-%d'
            ).date()
        # Content line
        else:
            m = regex_content.match(line_clean)
            if not m:
                raise ValueError(f'Misformatted line "{line_clean}"')
            indent_len = len(m.group('indent'))
            if indent_len % indent_spaces != 0:
                raise ValueError(
                    f'Indent not a multiple of {indent_spaces} '
                    f'"{line_clean}"'
                )
            indent_size = indent_len / indent_spaces
            raw_text = m.group('text')
            if indent_size <= len(stack):
                text = sep.join(stack)
                print('=>', text)
                yield Item(dt=current_date, text=text, subprovider=subprovider)
                if indent_size < len(stack):
                    stack.pop()
                stack.pop()
            stack.append(raw_text)
        if not lines and stack:
            text = sep.join(stack)
            print('=>', text)
            yield Item(dt=current_date, text=text, subprovider=subprovider)
        print('STACK', stack)


def read_txt(path: str) -> Iterator[Item]:
    logger.info('Reading txt file %s', path)
    with open(path) as f:
        yield from parse_txt(f, path)


def main(config_json: dict):
    config = load_config(config_json)
    return read_txt(config['path'])