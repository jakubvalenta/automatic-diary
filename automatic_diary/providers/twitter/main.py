import datetime
import glob
import json
import logging
import os.path
from pathlib import Path
from typing import Iterator

from automatic_diary.common import Item

logger = logging.getLogger(__name__)
provider = Path(__file__).parent.name


def _parse_tweets_file(path: str) -> Iterator[Item]:
    with open(path) as f:
        f.readline()  # Skip first line, which is not JSOn
        tweets_data = json.load(f)
    for tweet_data in tweets_data:
        dt_str = tweet_data['created_at']
        dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S %z')
        text = tweet_data['text']
        screen_name = tweet_data['user']['screen_name']
        yield Item(
            dt=dt, text=text, provider=provider, subprovider=screen_name
        )


def main(config: dict, *args, **kwargs) -> Iterator[Item]:
    path = config['path']
    logger.info('Reading Twitter archive %s', path)
    pathname = os.path.join(path, 'data', 'js', 'tweets', '*.js')
    for tweets_file_path in glob.glob(pathname):
        yield from _parse_tweets_file(tweets_file_path)
