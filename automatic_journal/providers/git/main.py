#!/usr/bin/env python3

import csv
import datetime
import json
import logging
import os
import subprocess
import sys
from functools import partial, reduce
from typing import Iterable, Iterator, List, Optional, Tuple

logger = logging.getLogger(__name__)

TDateTimeTextSubprovider = Tuple[datetime.datetime, str, str]


def load_config(path: str) -> dict:
    with open(path) as f:
        config = json.load(f)
    try:
        author = config['git']['author']
        base_path = config['git']['base_path']
    except (KeyError, TypeError):
        logger.error('Invalid config')
        sys.exit(1)
    return {
        'author': author,
        'base_path': base_path
    }


def run_shell_cmd(cmd: List[str], *args, **kwargs) -> Optional[str]:
    try:
        completed_process = subprocess.run(
            cmd,
            *args,
            stdout=subprocess.PIPE,
            check=True,
            text=True,
            **kwargs
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


def read_git_logs(
        repo_paths: Iterable[str],
        author: str) -> Iterator[TDateTimeTextSubprovider]:
    for repo_path in repo_paths:
        logger.info('Reading repository %s', repo_path)
        log = run_shell_cmd(
            [
                'git',
                '--no-pager',
                'log',
                f'--author={author}',
                '--format=%ad,%s',
                '--date=iso8601-strict'
            ],
            cwd=repo_path
        )
        if not log:
            continue
        for log_line in log.splitlines():
            dt_str, text = log_line.split(',', maxsplit=1)
            dt = datetime.datetime.fromisoformat(dt_str)
            yield dt, text, repo_path


def format_csv(dt_text_subprovider: Iterable[TDateTimeTextSubprovider],
               provider: str) -> Iterator[Tuple[str, str, str, str]]:
    for dt, text, subprovider in dt_text_subprovider:
        yield (
            dt.isoformat(),
            provider,
            subprovider,
            text
        )


def chain(*funcs):
    def wrapped(initializer):
        return reduce(lambda x, y: y(x), funcs, initializer)
    return wrapped


def main(config_path: str, csv_path: str):
    config = load_config(config_path)
    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        chain(
            find_git_repos,
            partial(
                read_git_logs,
                author=config['author']
            ),
            partial(
                format_csv,
                provider='git'
            ),
            writer.writerows
        )(config['base_path'])
