import json
from argparse import Namespace
from pathlib import Path
from typing import Any

import pytest

from dzcz_merchant_ops import cli


def enroll_test_profile(data_dir: Path) -> str:
    args = Namespace(
        data_dir=str(data_dir),
        platform="bilibili",
        merchant_key="test-account",
        merchant_name="Bilibili Test Account",
        account_label="main",
        home_url="https://www.bilibili.com",
        profile_path=None,
        notes=None,
        no_open=True,
        wait_open=False,
    )
    payload = cli.command_profile_enroll(args)
    return str(payload["profile_id"])


def run_fixed_like(
    data_dir: Path,
    profile_id: str,
    monkeypatch: pytest.MonkeyPatch,
    eval_payload: dict[str, Any],
    *,
    keep_session_open: bool = False,
) -> dict[str, Any]:
    browser_commands: list[list[str]] = []
    close_all_calls: list[bool] = []

    monkeypatch.setattr(
        cli,
        "detect_login_state",
        lambda profile: {"platform": "bilibili", "login_state": "logged_in"},
    )
    monkeypatch.setattr(
        cli,
        "close_existing_daemon",
        lambda: close_all_calls.append(True) or cli.CommandResult(["agent-browser", "close", "--all"], 0, "", ""),
    )
    monkeypatch.setattr(
        cli,
        "start_agent_browser_detached",
        lambda args, log_dir, close_daemon=False: {
            "args": ["agent-browser", *list(args)],
            "pid": 123,
            "returncode_after_start": None,
            "stdout_log": str(Path(log_dir) / "agent-browser-open.stdout.log"),
            "stderr_log": str(Path(log_dir) / "agent-browser-open.stderr.log"),
        },
    )

    def fake_run_agent_browser(args: Any, timeout: int = 300) -> cli.CommandResult:
        command_args = list(args)
        browser_commands.append(command_args)
        if "eval" in command_args:
            stdout = json.dumps(json.dumps(eval_payload)) + "\n"
        else:
            stdout = "ok\n"
        return cli.CommandResult(["agent-browser", *command_args], 0, stdout, "")

    monkeypatch.setattr(cli, "run_agent_browser", fake_run_agent_browser)

    args = Namespace(
        data_dir=str(data_dir),
        workflow="bilibili.video.like.fixed",
        input=["video_url=https://www.bilibili.com/video/BV1UvXVBnEy6"],
        input_json=None,
        profile_id=profile_id,
        platform=None,
        merchant_key=None,
        account_label=None,
        reuse_session=True,
        keep_session_open=keep_session_open,
        timeout=30,
    )
    payload = cli.command_task_run(args)
    payload["_browser_commands"] = browser_commands
    payload["_close_all_calls"] = close_all_calls
    return payload


def test_reuse_session_closes_ops_session_by_default_and_reports_operation_result(tmp_path, monkeypatch):
    profile_id = enroll_test_profile(tmp_path)

    payload = run_fixed_like(
        tmp_path,
        profile_id,
        monkeypatch,
        {
            "ok": True,
            "clicked": True,
            "confirmed": True,
            "before": {"liked": False},
            "after": {"liked": True},
        },
    )

    assert payload["status"] == "succeeded"
    assert payload["operation_result"]["confirmed"] is True
    assert payload["operation_result"]["after"]["liked"] is True
    assert payload["_close_all_calls"] == []
    assert any(command[-1:] == ["close"] for command in payload["_browser_commands"])


def test_keep_session_open_leaves_reused_ops_session_running(tmp_path, monkeypatch):
    profile_id = enroll_test_profile(tmp_path)

    payload = run_fixed_like(
        tmp_path,
        profile_id,
        monkeypatch,
        {
            "ok": True,
            "clicked": True,
            "confirmed": True,
            "before": {"liked": False},
            "after": {"liked": True},
        },
        keep_session_open=True,
    )

    assert payload["status"] == "succeeded"
    assert payload["_close_all_calls"] == []
    assert not any(command[-1:] == ["close"] for command in payload["_browser_commands"])


def test_eval_ok_false_marks_task_failed(tmp_path, monkeypatch):
    profile_id = enroll_test_profile(tmp_path)

    payload = run_fixed_like(
        tmp_path,
        profile_id,
        monkeypatch,
        {
            "ok": False,
            "clicked": True,
            "confirmed": False,
            "before": {"liked": False},
            "after": {"liked": False},
        },
    )

    assert payload["status"] == "failed"
    assert "reported ok=false" in payload["error"]
    assert payload["operation_result"]["confirmed"] is False
