import csv
import datetime
import glob
import json
import logging
import os.path
import re
import sys
from dataclasses import dataclass
from functools import partial, reduce
from typing import Iterable, Iterator, Tuple

logger = logging.getLogger(__name__)


def load_config(path: str) -> dict:
    with open(path) as f:
        config = json.load(f)
    try:
        paths = config['twitter']['paths']
    except (KeyError, TypeError):
        logger.error('Invalid config')
        sys.exit(1)
    return {'paths': paths}


@dataclass
class Tweet:
    dt: datetime.datetime
    text: str

    @property
    def clean_text(self):
        return re.sub(r'\s+', ' ', self.text).strip()


def _parse_tweets_file(path: str) -> Iterator[Tweet]:
    with open(path) as f:
        f.readline()  # Skip first line, which is not JSOn
        tweets_data = json.load(f)
    for tweet_data in tweets_data:
        dt_str = tweet_data['created_at']
        dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S %z')
        text = tweet_data['text']
        yield Tweet(dt=dt, text=text)


def parse_all_archives(config: dict) -> Iterator[Tuple[Tweet, str]]:
    for path in config['paths']:
        logger.info('Reading Twitter archive %s', path)
        pathname = os.path.join(path, 'data', 'js', 'tweets', '*.js')
        for tweets_file_path in glob.glob(pathname):
            for tweet in _parse_tweets_file(tweets_file_path):
                yield tweet, path


def format_csv(
    tweets_and_paths: Iterable[Tuple[Tweet, str]], provider: str
) -> Iterator[Tuple[str, str, str, str]]:
    for tweet, path in tweets_and_paths:
        yield (tweet.dt.isoformat(), provider, path, tweet.clean_text)


def chain(*funcs):
    def wrapped(initializer):
        return reduce(lambda x, y: y(x), funcs, initializer)

    return wrapped


def main(config_path: str, csv_path: str):
    config = load_config(config_path)
    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        chain(
            parse_all_archives,
            partial(format_csv, provider='twitter'),
            writer.writerows,
        )(config)
