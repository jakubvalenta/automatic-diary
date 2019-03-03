import datetime
import logging
import os
import subprocess
from pathlib import Path
from typing import Iterable, Iterator, Tuple

from automatic_diary.common import Item, run_shell_cmd

logger = logging.getLogger(__name__)
provider = Path(__file__).parent.name

TDateTimeTextSubprovider = Tuple[datetime.datetime, str, str]


def find_git_repos(base_path: str) -> Iterator[str]:
    for entry in os.scandir(base_path):
        if entry.name == '.git':
            yield base_path
        if not entry.name.startswith('.') and entry.is_dir():
            yield from find_git_repos(entry.path)


def read_git_logs(repo_paths: Iterable[str], author: str) -> Iterator[Item]:
    for repo_path in repo_paths:
        logger.info('Reading repository %s', repo_path)
        try:
            log = run_shell_cmd(
                [
                    'git',
                    '--no-pager',
                    'log',
                    f'--author={author}',
                    '--format=%ad,%s',
                    '--date=iso8601-strict',
                ],
                cwd=repo_path,
            )
        except subprocess.CalledProcessError:
            continue
        for log_line in log.splitlines():
            dt_str, text = log_line.split(',', maxsplit=1)
            dt = datetime.datetime.fromisoformat(dt_str)
            yield Item(
                dt=dt, text=text, provider=provider, subprovider=repo_path
            )


def main(config: dict, *args, **kwargs) -> Iterator[Item]:
    base_path = config['base_path']
    author = config['author']
    repo_paths = find_git_repos(base_path)
    return read_git_logs(repo_paths, author)
