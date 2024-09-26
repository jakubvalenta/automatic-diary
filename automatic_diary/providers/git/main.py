import datetime
import logging
import os
import subprocess
from pathlib import Path
from typing import Iterable, Iterator

from automatic_diary.cache import with_cache
from automatic_diary.model import Item
from automatic_diary.shell import run_shell_cmd

logger = logging.getLogger(__name__)
provider = Path(__file__).parent.name


def _find_git_repos(base_path: str) -> Iterator[str]:
    if not os.path.isdir(base_path):
        logger.warn(f"Directory {base_path} doesn't exist")
        return
    try:
        entries = os.scandir(base_path)
    except PermissionError:
        return
    for entry in entries:
        if entry.name == ".git":
            yield base_path
        try:
            is_normal_dir = not entry.name.startswith(".") and entry.is_dir()
        except OSError:
            return
        if is_normal_dir:
            yield from _find_git_repos(entry.path)


def _call_git_rev_parse(repo_path: str) -> str:
    return run_shell_cmd(["git", "rev-parse", "HEAD"], cwd=repo_path)


def _call_git_log(repo_path: str, author: str) -> str:
    logger.info("Calling git log in %s", repo_path)
    return run_shell_cmd(
        [
            "git",
            "--no-pager",
            "log",
            f"--author={author}",
            "--format=%ad,%s",
            "--date=iso8601-strict",
        ],
        cwd=repo_path,
    )


def _read_git_logs(
    repo_paths: Iterable[str], author: str, cache_dir: Path | None, no_cache: bool
) -> Iterator[Item]:
    for repo_path in repo_paths:
        repo_name = os.path.basename(repo_path)
        try:
            rev = _call_git_rev_parse(repo_path).strip()
        except subprocess.CalledProcessError:
            continue
        cache_file = cache_dir / repo_name / f"{rev}.txt" if cache_dir else None
        try:
            log = with_cache(
                lambda: _call_git_log(repo_path, author), cache_file, no_cache
            )
        except subprocess.CalledProcessError:
            continue
        for log_line in log.splitlines():
            formatted_datetime_, text = log_line.split(",", maxsplit=1)
            datetime_ = datetime.datetime.fromisoformat(formatted_datetime_)
            yield Item.normalized(
                datetime_=datetime_,
                text=text,
                provider=provider,
                subprovider=repo_name,
            )


def main(config: dict, no_cache: bool, *args, **kwargs) -> Iterator[Item]:
    base_path = config["base_path"]
    author = config["author"]
    repo_paths = _find_git_repos(base_path)
    cache_dir_str = config.get("cache_dir")
    cache_dir = Path(cache_dir_str) if cache_dir_str else None
    return _read_git_logs(repo_paths, author, cache_dir, no_cache)
