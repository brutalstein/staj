from __future__ import annotations

from pathlib import Path
import subprocess

from tools import project_launcher


def test_check_reports_missing_yaml_before_loading_configuration(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(project_launcher, "_check_python", lambda: [])
    monkeypatch.setattr(project_launcher, "_missing_modules", lambda _modules: ["yaml"])

    result = project_launcher.run_check(tmp_path / "missing.yaml", require_carla=False)

    assert result == project_launcher.EXIT_ENVIRONMENT


def test_install_keeps_simple_pip_execution(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(project_launcher, "_is_virtual_environment", lambda: True)

    def fake_call(command: list[str], *, cwd: Path) -> int:
        captured["command"] = command
        captured["cwd"] = cwd
        return 0

    monkeypatch.setattr(project_launcher.subprocess, "call", fake_call)

    result = project_launcher.run_install(include_docs=True)

    assert result == 0
    assert captured["command"][-2:] == ["-e", ".[dev,docs]"]
    assert captured["cwd"] == project_launcher.PROJECT_ROOT


def test_application_waits_for_graceful_shutdown_after_keyboard_interrupt(monkeypatch) -> None:
    class FakeProcess:
        def __init__(self) -> None:
            self.wait_calls: list[float | None] = []
            self.terminated = False
            self.killed = False

        def wait(self, timeout: float | None = None) -> int:
            self.wait_calls.append(timeout)
            if len(self.wait_calls) == 1:
                raise KeyboardInterrupt
            return 0

        def terminate(self) -> None:
            self.terminated = True

        def kill(self) -> None:
            self.killed = True

    process = FakeProcess()

    result = project_launcher._wait_for_application_shutdown(process)  # type: ignore[arg-type]

    assert result == 0
    assert process.wait_calls == [None, 5.0]
    assert process.terminated is False
    assert process.killed is False


def test_application_terminates_child_after_grace_timeout(monkeypatch) -> None:
    class FakeProcess:
        def __init__(self) -> None:
            self.wait_calls: list[float | None] = []
            self.terminated = False
            self.killed = False

        def wait(self, timeout: float | None = None) -> int:
            self.wait_calls.append(timeout)
            call_number = len(self.wait_calls)
            if call_number == 1:
                raise KeyboardInterrupt
            if call_number in {2, 3}:
                raise subprocess.TimeoutExpired(cmd="autonomy", timeout=timeout or 0.0)
            return -9

        def terminate(self) -> None:
            self.terminated = True

        def kill(self) -> None:
            self.killed = True

    process = FakeProcess()

    result = project_launcher._wait_for_application_shutdown(process)  # type: ignore[arg-type]

    assert result == -9
    assert process.wait_calls == [None, 5.0, 5.0, None]
    assert process.terminated is True
    assert process.killed is True
