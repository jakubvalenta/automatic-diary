import argparse
import importlib
import json
import logging
import os.path
import sys
from typing import List

from automatic_journal import __title__

logger = logging.getLogger(__name__)

dir_ = os.path.dirname(__file__)


def load_config(path: str) -> dict:
    with open(path) as f:
        config = json.load(f)
    try:
        providers = list(config.keys())
    except (AttributeError, TypeError):
        logger.error('Invalid config')
        sys.exit(1)
    return {
        'providers': providers,
    }


def call_providers(providers: List[str], *args, **kwargs):
    for provider in providers:
        name = f'automatic_journal.providers.{provider}.main'
        try:
            module = importlib.import_module(name)
        except ModuleNotFoundError:
            logger.error('Provider %s not found', provider)
            continue
        module.main(*args, **kwargs)  # type: ignore


def main():
    parser = argparse.ArgumentParser(description=__title__)
    parser.add_argument(
        'config_path',
        help='Configuration file path'
    )
    parser.add_argument(
        'output_csv_path',
        help='Output CSV file path'
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Enable debugging output'
    )
    parser.add_argument(
        '-c',
        '--clean',
        action='store_true',
        help='Clean cache and exit'
    )
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.INFO,
            format='%(message)s')
    if args.clean:
        pass  # TODO
    else:
        config = load_config(args.config_path)
        call_providers(
            config['providers'],
            args.config_path,
            args.output_csv_path
        )