import argparse
import csv
import dataclasses
import datetime
import importlib
import json
import logging
import os.path
import random
import string
import sys
import unicodedata
from typing import Iterable, Iterator, List, Optional, Set, Tuple

from automatic_diary import __title__
from automatic_diary.model import Item

logger = logging.getLogger(__name__)

dir_ = os.path.dirname(__file__)


def _obfuscate_char(char: str) -> str:
    category = unicodedata.category(char)
    if category == 'Lu':
        return random.choice(string.ascii_uppercase)
    if category == 'Ll':
        return random.choice(string.ascii_lowercase)
    if category == 'Nd':
        return random.choice(string.digits)
    return char


def obfuscate(s: str) -> str:
    return ''.join(_obfuscate_char(char) for char in s)


def load_configs(
    path: str, only_providers: Optional[List[str]] = None
) -> Iterator[Tuple[str, dict]]:
    with open(path) as f:
        config_json = json.load(f)
    for config_json_item in config_json:
        provider = config_json_item['provider']
        config = config_json_item['config']
        if not only_providers or provider in only_providers:
            yield provider, config


def call_providers(
    configs: Iterable[Tuple[str, dict]], no_cache: bool
) -> Iterator[Item]:
    for provider, config in configs:
        name = f'automatic_diary.providers.{provider}.main'
        try:
            logger.info('Running provider %s', name)
            module = importlib.import_module(name)
        except ModuleNotFoundError:
            logger.error('Provider %s not found', provider)
            continue
        yield from module.main(config, no_cache)  # type: ignore


def write_csv(items: Iterable[Item], path: str):
    now = datetime.datetime.now().astimezone()
    with open(path, 'w') as f:
        writer = csv.writer(f, lineterminator='\n')
        encountered_item_tuples: Set[Tuple[str, str, str, str]] = set()
        for item in sorted(items):
            if item.datetime_ > now:
                break
            item_tuple = item.astuple()
            if item_tuple not in encountered_item_tuples:
                writer.writerow(item_tuple)
                encountered_item_tuples.add(item_tuple)


def main():
    parser = argparse.ArgumentParser(description=__title__)
    parser.add_argument('config_path', help='Configuration file path')
    parser.add_argument('output_csv_path', help='Output CSV file path')
    parser.add_argument(
        '-p',
        '--provider',
        action='append',
        help=(
            'Provider to use. Pass the option several times to use several '
            'providers. If not passed at all, all configured providers will '
            'be used.'
        ),
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Enable debugging output'
    )
    parser.add_argument(
        '-n', '--no-cache', action='store_true', help='Don\'t use cache'
    )
    parser.add_argument(
        '-o',
        '--obfuscate',
        action='store_true',
        help='Obfuscate the text output (to publish examples and screenshots)',
    )
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(
            stream=sys.stdout, level=logging.INFO, format='%(message)s'
        )
    configs = load_configs(args.config_path, args.provider)
    items = call_providers(configs, args.no_cache)
    if args.obfuscate:
        items = (
            dataclasses.replace(item, text=obfuscate(item.text))
            for item in items
        )
    write_csv(items, args.output_csv_path)
