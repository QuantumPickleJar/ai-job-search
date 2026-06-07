#!/usr/bin/env python3
"""Create the Pi-side intake endpoint config and auto-start service file."""

from __future__ import annotations

import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXTENSION_DIR = REPO_ROOT / "extensions" / "linkedin-job-clipper"
DEPLOY_DIR = REPO_ROOT / "deploy"
SERVICE_NAME = "ai-job-intake.service"


def render_extension_config(pi_host: str) -> str:
    return (
        "window.__AI_JOB_INTAKE_URL__ = 'http://"
        f"{pi_host}:3927/jobs/capture';\n"
    )


def render_systemd_unit(repo_root: str) -> str:
    return """[Unit]
Description=AI Job Search intake server on the Pi
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory={repo_root}
ExecStart=/usr/bin/python3 scripts/job_intake_server.py --host 0.0.0.0 --port 3927
Restart=on-failure
RestartSec=5
User=pi

[Install]
WantedBy=multi-user.target
""".format(repo_root=repo_root)


def write_pi_setup_files(pi_host: str, repo_root: Path = REPO_ROOT) -> dict[str, Path]:
    EXTENSION_DIR.mkdir(parents=True, exist_ok=True)
    DEPLOY_DIR.mkdir(parents=True, exist_ok=True)

    config_path = EXTENSION_DIR / "config.js"
    config_path.write_text(render_extension_config(pi_host), encoding="utf-8")

    service_path = DEPLOY_DIR / SERVICE_NAME
    service_path.write_text(render_systemd_unit(str(repo_root)), encoding="utf-8")

    return {"config": config_path, "service": service_path}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Pi intake endpoint config and systemd service")
    parser.add_argument("--pi-host", required=True, help="Private Pi LAN address used by the browser extension")
    args = parser.parse_args()

    written = write_pi_setup_files(args.pi_host)
    print(f"Wrote {written['config']} with endpoint http://{args.pi_host}:3927/jobs/capture")
    print(f"Wrote {written['service']} for auto-start on the Pi")
    print("Install with: sudo cp deploy/ai-job-intake.service /etc/systemd/system/")
    print("Then: sudo systemctl daemon-reload && sudo systemctl enable --now ai-job-intake")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
