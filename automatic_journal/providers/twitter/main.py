import datetime
import glob
import json
import logging
import os.path
import sys
from typing import Iterator

from automatic_journal.common import Item

logger = logging.getLogger(__name__)


def load_config(config_json: dict) -> dict:
    try:
        paths = config_json['twitter']['paths']
    except (KeyError, TypeError):
        logger.error('Invalid config')
        sys.exit(1)
    return {'paths': paths}


def _parse_tweets_file(path: str) -> Iterator[Item]:
    with open(path) as f:
        f.readline()  # Skip first line, which is not JSOn
        tweets_data = json.load(f)
    for tweet_data in tweets_data:
        dt_str = tweet_data['created_at']
        dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S %z')
        text = tweet_data['text']
        screen_name = tweet_data['user']['screen_name']
        yield Item(dt=dt, text=text, subprovider=screen_name)


def parse_all_archives(config: dict) -> Iterator[Item]:
    for path in config['paths']:
        logger.info('Reading Twitter archive %s', path)
        pathname = os.path.join(path, 'data', 'js', 'tweets', '*.js')
        for tweets_file_path in glob.glob(pathname):
            yield from _parse_tweets_file(tweets_file_path)


def main(config_json: dict, *args, **kwargs) -> Iterator[Item]:
    config = load_config(config_json)
    return parse_all_archives(config)
