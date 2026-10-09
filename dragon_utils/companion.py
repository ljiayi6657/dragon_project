"""Companion transport helpers adapted from existing DRAGON run scripts.

Sources:
  Script/analysis/optimization/optim_copy.py: upload and download operations.
  Script/analysis/optimization/calcDRAGONauto.py: rsync transport.
  Script/analysis/dragon_flux_package/run_l_scan.py: command logging.
"""

from datetime import datetime
from pathlib import Path
import shlex
import subprocess
from zoneinfo import ZoneInfo


HOST = "ljiayi@192.168.72.54"
SSH = ("ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10")


def run_command(args, log, cwd=None):
    """Run one command, recording stdout, stderr and its exit status."""

    args = [str(part) for part in args]
    target = Path(log).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as stream:
        stamp = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds")
        stream.write(f"\n[{stamp}] $ {shlex.join(args)}\n")
        stream.flush()
        try:
            done = subprocess.run(
                args,
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=stream,
                stderr=subprocess.STDOUT,
                check=False,
            )
        except OSError as exc:
            stream.write(f"\nLaunch failed: {exc}\n")
            raise
        stamp = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds")
        stream.write(f"\n[{stamp}] Exit code: {done.returncode}\n")
    if done.returncode:
        raise RuntimeError(f"Command failed with exit code {done.returncode}; log: {target}")
    return done


def execute(args, log, cwd=None, host=HOST):
    """Execute one quoted argument list on the companion host."""

    command = shlex.join(str(part) for part in args)
    if cwd is not None:
        command = f"cd -- {shlex.quote(str(cwd))} && {command}"
    return run_command([*SSH, host, command], log)


def upload(local, remote, log, host=HOST):
    """Upload one existing file to an existing remote directory."""

    source = Path(local).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    return run_command(
        ["rsync", "-a", "--checksum", "--protect-args", "-e", shlex.join(SSH),
         "--", source, f"{host}:{remote}"],
        log,
    )


def download(remote, local, log, host=HOST):
    """Download one exact remote file into the local output directory."""

    target = Path(local).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    return run_command(
        ["rsync", "-a", "--checksum", "--protect-args", "-e", shlex.join(SSH),
         "--", f"{host}:{remote}", target],
        log,
    )
