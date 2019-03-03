import datetime
import logging
import re
from pathlib import Path
from typing import IO, Iterator, List, Optional

from more_itertools import peekable

from automatic_diary.common import Item

logger = logging.getLogger(__name__)
provider = Path(__file__).parent.name

regex_heading = re.compile(r'^(?P<date>\d{4}-\d{2}-\d{2})')
regex_content = re.compile(r'^(?P<indent> +)(?P<text>.+)$')


def parse_txt(
    f: IO,
    subprovider: str,
    indent_spaces: int = 4,
    sep: str = ': ',
    max_indent: int = 3,
    sep_after_max_indent: str = ' ',
) -> Iterator[Item]:
    current_date: Optional[datetime.date] = None
    stack: List[str] = []
    lines = peekable(f)
    for line in lines:
        line_clean = line.rstrip()
        if not line_clean:
            continue
        # Title line
        m = regex_heading.match(line_clean)
        if m:
            if stack:
                if not current_date:
                    raise ValueError('No date found')
                text = sep.join(stack)
                yield Item(
                    dt=current_date,
                    text=text,
                    provider=provider,
                    subprovider=subprovider,
                )
                stack.clear()
            date_str = m.group('date')
            current_date = datetime.datetime.strptime(
                date_str, '%Y-%m-%d'
            ).date()
        # Starts with a non-date line
        elif not current_date:
            raise ValueError('No date found')
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
            if indent_size > max_indent:
                indent_size = max_indent
                stack[-1] = sep_after_max_indent.join([stack[-1], raw_text])
                continue
            if indent_size <= len(stack):
                text = sep.join(stack)
                yield Item(
                    dt=current_date,
                    text=text,
                    provider=provider,
                    subprovider=subprovider,
                )
                if indent_size < len(stack):
                    stack.pop()
                stack.pop()
            stack.append(raw_text)
        if not lines and stack:
            text = sep.join(stack)
            yield Item(
                dt=current_date,
                text=text,
                provider=provider,
                subprovider=subprovider,
            )


def main(config: dict, *args, **kwargs) -> Iterator[Item]:
    path = config['path']
    logger.info('Reading txt file %s', path)
    with open(path) as f:
        yield from parse_txt(f, path)
