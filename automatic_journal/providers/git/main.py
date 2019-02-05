import datetime
import logging
import os
import subprocess
import sys
from functools import partial
from typing import Iterable, Iterator, List, Optional, Tuple

from automatic_journal.common import Item, chain

logger = logging.getLogger(__name__)

TDateTimeTextSubprovider = Tuple[datetime.datetime, str, str]


def load_config(config_json: dict) -> dict:
    try:
        author = config_json['git']['author']
        base_path = config_json['git']['base_path']
    except (KeyError, TypeError):
        logger.error('Invalid config')
        sys.exit(1)
    return {'author': author, 'base_path': base_path}


def _run_shell_cmd(cmd: List[str], **kwargs) -> Optional[str]:
    try:
        completed_process = subprocess.run(
            cmd, stdout=subprocess.PIPE, check=True, text=True, **kwargs
        )
        return completed_process.stdout
    except subprocess.CalledProcessError:
        return None


def find_git_repos(path: str) -> Iterator[str]:
    for entry in os.scandir(path):
        if entry.name == '.git':
            yield path
        if not entry.name.startswith('.') and entry.is_dir():
            yield from find_git_repos(entry.path)


def read_git_logs(repo_paths: Iterable[str], author: str) -> Iterator[Item]:
    for repo_path in repo_paths:
        logger.info('Reading repository %s', repo_path)
        log = _run_shell_cmd(
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
        if not log:
            continue
        for log_line in log.splitlines():
            dt_str, text = log_line.split(',', maxsplit=1)
            dt = datetime.datetime.fromisoformat(dt_str)
            yield Item(dt=dt, text=text, subprovider=repo_path)


def main(config_json: dict):
    config = load_config(config_json)
    return chain(
        find_git_repos, partial(read_git_logs, author=config['author'])
    )(config['base_path'])
