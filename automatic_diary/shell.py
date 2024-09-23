import subprocess
from typing import Optional


def run_shell_cmd(cmd: list[str], **kwargs) -> str:
    completed_process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        check=True,
        universal_newlines=True,  # Don't use arg 'text' for Python 3.6 compat.
        **kwargs,
    )
    return completed_process.stdout


def search_secret(key: str, val: str, label: str) -> Optional[str]:
    out = run_shell_cmd(["secret-tool", "search", key, val])
    lines = out.splitlines()
    for i, line in enumerate(lines):
        if line == f"label = {label}":
            if len(lines) == i + 1:
                raise Exception("Invalid secret-tool output")
            secret_line = lines[i + 1]
            if not secret_line.startswith("secret = "):
                raise Exception("Invalid secret-tool output")
            start = len("secret = ")
            return secret_line[start:]
    return None
