import logging
from collections.abc import Callable
from pathlib import Path

logger = logging.getLogger(__name__)


def with_cache(
    func: Callable[..., str], cache_file: Path | None, no_cache: bool
) -> str:
    if not cache_file:
        return func()
    if not no_cache and cache_file.is_file():
        logger.info("Reading cache %s", cache_file)
        res = cache_file.read_text()
    else:
        res = func()
        logger.info("Writing cache %s", cache_file)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(res)
    return res
