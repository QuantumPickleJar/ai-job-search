from __future__ import annotations

from pathlib import Path

from scripts import setup_pi_job_intake


def test_render_extension_config_uses_pi_host() -> None:
    config = setup_pi_job_intake.render_extension_config("192.168.1.55")

    assert "window.__AI_JOB_INTAKE_URL__ = 'http://192.168.1.55:3927/jobs/capture';" in config


def test_render_systemd_service_uses_repo_root(tmp_path: Path) -> None:
    unit = setup_pi_job_intake.render_systemd_unit(str(tmp_path))

    assert "WorkingDirectory=" in unit
    assert str(tmp_path) in unit
    assert "ExecStart=/usr/bin/python3" in unit
    assert "job_intake_server.py" in unit
    assert "WantedBy=multi-user.target" in unit
