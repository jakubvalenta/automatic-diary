import subprocess
from typing import List


def run_shell_cmd(cmd: List[str], **kwargs) -> str:
    completed_process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        check=True,
        universal_newlines=True,  # Don't use arg 'text' for Python 3.6 compat.
        **kwargs,
    )
    return completed_process.stdout


def lookup_secret(key: str, val: str) -> str:
    return run_shell_cmd(['secret-tool', 'lookup', key, val])
