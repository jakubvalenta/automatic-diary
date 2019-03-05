import datetime
import logging
import os
import subprocess
from pathlib import Path
from typing import Iterable, Iterator

from automatic_diary.model import Item
from automatic_diary.shell import run_shell_cmd

logger = logging.getLogger(__name__)
provider = Path(__file__).parent.name


def _find_git_repos(base_path: str) -> Iterator[str]:
    for entry in os.scandir(base_path):
        if entry.name == '.git':
            yield base_path
        if not entry.name.startswith('.') and entry.is_dir():
            yield from _find_git_repos(entry.path)


def _call_git_log(repo_path: str, author: str) -> str:
    return run_shell_cmd(
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


def _read_git_logs(repo_paths: Iterable[str], author: str) -> Iterator[Item]:
    for repo_path in repo_paths:
        logger.info('Reading repository %s', repo_path)
        repo_name = os.path.basename(repo_path)
        try:
            log = _call_git_log(repo_path, author)
        except subprocess.CalledProcessError:
            continue
        for log_line in log.splitlines():
            formatted_datetime_, text = log_line.split(',', maxsplit=1)
            datetime_ = datetime.datetime.fromisoformat(formatted_datetime_)
            yield Item.normalized(
                datetime_=datetime_,
                text=text,
                provider=provider,
                subprovider=repo_name,
            )


def main(config: dict, *args, **kwargs) -> Iterator[Item]:
    base_path = config['base_path']
    author = config['author']
    repo_paths = _find_git_repos(base_path)
    return _read_git_logs(repo_paths, author)
