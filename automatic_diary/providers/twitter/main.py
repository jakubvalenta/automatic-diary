import datetime
import json
import logging
from pathlib import Path
from typing import Iterator

from automatic_diary.model import Item

logger = logging.getLogger(__name__)
provider = Path(__file__).parent.name


def _parse_tweets_file(path: Path) -> Iterator[Item]:
    with path.open() as f:
        f.readline()  # Skip first line, which is not JSOn
        tweets_data = json.load(f)
    for tweet_data in tweets_data:
        datetime_ = datetime.datetime.strptime(
            tweet_data['created_at'], '%Y-%m-%d %H:%M:%S %z'
        )
        text = tweet_data['text']
        screen_name = tweet_data['user']['screen_name']
        yield Item.normalized(
            datetime_=datetime_,
            text=text,
            provider=provider,
            subprovider=screen_name,
        )


def main(config: dict, *args, **kwargs) -> Iterator[Item]:
    path = Path(config['path'])
    logger.info('Reading Twitter archive %s', path)
    for tweets_file_path in (path / 'data' / 'js' / 'tweets').glob('*.js'):
        yield from _parse_tweets_file(tweets_file_path)
