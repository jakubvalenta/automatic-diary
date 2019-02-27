import argparse
import csv
import importlib
import json
import logging
import os.path
import sys
from dataclasses import dataclass
from typing import Iterable, Iterator, List, Optional, Set, Tuple

from automatic_journal import __title__
from automatic_journal.common import Item

logger = logging.getLogger(__name__)

dir_ = os.path.dirname(__file__)


@dataclass
class Row:
    item: Item
    provider: str

    def astuple(self) -> Tuple[str, str, str, str]:
        return (
            self.item.dt_str,
            self.provider,
            self.item.subprovider,
            self.item.clean_text,
        )


def load_config(
    path: str, only_providers: Optional[List[str]] = None
) -> Tuple[List[str], dict]:
    with open(path) as f:
        config_json = json.load(f)
    try:
        providers = [
            k
            for k in config_json.keys()
            if not only_providers or k in only_providers
        ]
    except (AttributeError, TypeError):
        logger.error('Invalid config')
        sys.exit(1)
    return providers, config_json


def call_providers(
    providers: List[str], config_json: str, no_cache: bool
) -> Iterator[Row]:
    for provider in providers:
        name = f'automatic_journal.providers.{provider}.main'
        try:
            module = importlib.import_module(name)
        except ModuleNotFoundError:
            logger.error('Provider %s not found', provider)
            continue
        items = module.main(config_json, no_cache)  # type: ignore
        for item in items:
            yield Row(item, provider)


def write_csv(rows: Iterable[Row], path: str):
    with open(path, 'w') as f:
        writer = csv.writer(f, lineterminator='\n')
        sorted_rows: List[Row] = sorted(rows, key=lambda row: row.item)
        encountered_row_tuples: Set[Tuple[str, str, str, str]] = set()
        for row in sorted_rows:
            row_tuple = row.astuple()
            if row_tuple not in encountered_row_tuples:
                writer.writerow(row_tuple)
                encountered_row_tuples.add(row_tuple)


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
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(
            stream=sys.stdout, level=logging.INFO, format='%(message)s'
        )
    providers, config_json = load_config(args.config_path, args.provider)
    rows = call_providers(providers, config_json, args.no_cache)
    write_csv(rows, args.output_csv_path)
