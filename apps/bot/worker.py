import json
import os
import re
import subprocess
import sys
from pathlib import Path

from django.conf import settings


WORKER_MARKER = "manage.py run_telegram_bot"
DEFAULT_POLL_TIMEOUT = 10
DEFAULT_SLEEP = 1.0


def _run_command(command):
    try:
        return subprocess.check_output(command, stderr=subprocess.DEVNULL, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return ""


def _windows_worker_processes():
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        (
            "Get-CimInstance Win32_Process | "
            "Where-Object { $_.Name -match 'python' -and $_.CommandLine -like '*manage.py run_telegram_bot*' } | "
            "Select-Object ProcessId,ParentProcessId,CreationDate,CommandLine | ConvertTo-Json -Compress"
        ),
    ]
    output = _run_command(command).strip()
    if not output:
        return []

    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return []

    if isinstance(payload, dict):
        payload = [payload]

    processes = []
    for item in payload:
        command_line = item.get("CommandLine") or ""
        if WORKER_MARKER not in command_line:
            continue
        processes.append(
            {
                "pid": int(item.get("ProcessId")),
                "parent_pid": item.get("ParentProcessId"),
                "started_at": item.get("CreationDate") or "",
                "command_line": command_line,
            }
        )
    return processes


def _posix_worker_processes():
    output = _run_command(["pgrep", "-af", WORKER_MARKER]).strip()
    processes = []
    for line in output.splitlines():
        if not line.strip():
            continue
        pid_text, _, command_line = line.partition(" ")
        if not pid_text.isdigit() or int(pid_text) == os.getpid():
            continue
        processes.append(
            {
                "pid": int(pid_text),
                "parent_pid": "",
                "started_at": "",
                "command_line": command_line,
            }
        )
    return processes


def get_worker_processes():
    if os.name == "nt":
        return _windows_worker_processes()
    return _posix_worker_processes()


def parse_worker_period(command_line):
    poll_timeout = DEFAULT_POLL_TIMEOUT
    sleep = DEFAULT_SLEEP

    poll_match = re.search(r"--poll-timeout\s+([0-9]+)", command_line or "")
    if poll_match:
        poll_timeout = int(poll_match.group(1))

    sleep_match = re.search(r"--sleep\s+([0-9]+(?:\.[0-9]+)?)", command_line or "")
    if sleep_match:
        sleep = float(sleep_match.group(1))

    return {
        "poll_timeout": poll_timeout,
        "sleep": sleep,
        "period_label": f"{poll_timeout}s long-poll, {sleep:g}s tanaffus",
    }


def get_worker_state(bot_settings=None):
    processes = get_worker_processes()
    primary = processes[-1] if processes else None
    period = parse_worker_period(primary["command_line"]) if primary else {
        "poll_timeout": DEFAULT_POLL_TIMEOUT,
        "sleep": DEFAULT_SLEEP,
        "period_label": "Ishlamayapti",
    }
    last_response = getattr(bot_settings, "last_response", {}) or {}
    return {
        "is_running": bool(processes),
        "processes": processes,
        "primary_pid": primary["pid"] if primary else "",
        "period": period,
        "last_polling": last_response if last_response.get("polling") else {},
    }


def stop_worker_processes():
    processes = get_worker_processes()
    for process in processes:
        pid = str(process["pid"])
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", pid, "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(["kill", "-TERM", pid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return len(processes)


def start_worker_process(poll_timeout=DEFAULT_POLL_TIMEOUT, sleep=DEFAULT_SLEEP):
    if get_worker_processes():
        return {"started": False, "reason": "already_running", "processes": get_worker_processes()}

    manage_py = Path(settings.BASE_DIR) / "manage.py"
    stdout_path = Path(settings.BASE_DIR) / "bot-worker.out.log"
    stderr_path = Path(settings.BASE_DIR) / "bot-worker.err.log"
    args = [
        sys.executable,
        str(manage_py),
        "run_telegram_bot",
        "--poll-timeout",
        str(poll_timeout),
        "--sleep",
        str(sleep),
    ]
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    with stdout_path.open("a", encoding="utf-8") as stdout, stderr_path.open("a", encoding="utf-8") as stderr:
        process = subprocess.Popen(
            args,
            cwd=settings.BASE_DIR,
            stdout=stdout,
            stderr=stderr,
            creationflags=creationflags,
            close_fds=os.name != "nt",
        )

    return {"started": True, "pid": process.pid, "processes": get_worker_processes()}
