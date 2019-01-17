#!/usr/bin/env python3

import csv
import datetime
import json
import logging
import mailbox
import sys
from functools import partial, reduce
from pathlib import Path
from typing import Iterable, Iterator, Tuple

logger = logging.getLogger(__name__)

TDateTimeAndText = Tuple[datetime.datetime, str]


def load_config(path: str) -> dict:
    with open(path) as f:
        config = json.load(f)
    try:
        path = config['maildir']['path']
    except (KeyError, TypeError):
        logger.error('Invalid config')
        sys.exit(1)
    return {
        'path': path
    }


def read_messages(config: dict) -> Iterator[TDateTimeAndText]:
    path = config['path']
    maildir = mailbox.Maildir(path)
    for message in maildir:
        yield ('', '')


def format_csv(dt_and_text: Iterable[TDateTimeAndText],
               provider: str,
               subprovider: str) -> Iterator[Tuple[str, str, str, str]]:
    for dt, text in dt_and_text:
        yield (
            dt.isoformat(),
            provider,
            subprovider,
            text
        )


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
            partial(
                format_csv,
                provider='maildir',
                subprovider=config['path']
            ),
            writer.writerows
        )(config)
