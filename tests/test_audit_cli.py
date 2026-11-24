"""Unit tests for the audit CLI covering valid and invalid configurations."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Iterator

import pytest

from app.main import create_server
from scripts.audit_cli import audit_healthcheck, audit_terraform, audit_yaml_manifests, main


@pytest.fixture()
def live_health_url() -> Iterator[str]:
    server = create_server(host="127.0.0.1", port=0)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}/health"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_audit_terraform_passes_on_repo_terraform_dir() -> None:
    repo_tf = Path(__file__).resolve().parent.parent / "terraform"
    result = audit_terraform(repo_tf)
    assert result.passed is True
    assert result.errors == []
    assert result.checked_items >= 6


def test_audit_terraform_fails_when_variable_missing_description_or_type(tmp_path: Path) -> None:
    (tmp_path / "variables.tf").write_text(
        'variable "bad_var" {\n  default = "oops"\n}\n',
        encoding="utf-8",
    )
    result = audit_terraform(tmp_path)
    assert result.passed is False
    assert any("missing required 'description'" in e for e in result.errors)
    assert any("missing required 'type'" in e for e in result.errors)


def test_audit_terraform_fails_on_tfstate_and_hardcoded_secret(tmp_path: Path) -> None:
    (tmp_path / "terraform.tfstate").write_text("{}", encoding="utf-8")
    (tmp_path / "main.tf").write_text(
        'locals {\n  api_key = "super-secret-value-12345"\n}\n',
        encoding="utf-8",
    )
    result = audit_terraform(tmp_path)
    assert result.passed is False
    assert any("Forbidden Terraform state file" in e for e in result.errors)
    assert any("hardcoded secret" in e for e in result.errors)


def test_audit_yaml_passes_valid_deployment_and_argocd_app(tmp_path: Path) -> None:
    (tmp_path / "deployment.yaml").write_text(
        """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-app
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
      containers:
        - name: app
          image: us-central1-docker.pkg.dev/demo/repo/app:1.0.0
""",
        encoding="utf-8",
    )
    (tmp_path / "argocd.yaml").write_text(
        """
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: demo-app
spec:
  source:
    repoURL: https://github.com/JagaScripts/gcp-devops-gitops-demo.git
  destination:
    server: https://kubernetes.default.svc
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
""",
        encoding="utf-8",
    )
    result = audit_yaml_manifests(tmp_path)
    assert result.passed is True
    assert result.errors == []


def test_audit_yaml_fails_on_syntax_error_and_insecure_deployment(tmp_path: Path) -> None:
    (tmp_path / "broken.yaml").write_text("apiVersion: v1\n  bad: [unclosed", encoding="utf-8")
    (tmp_path / "insecure.yaml").write_text(
        """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: insecure-app
spec:
  template:
    spec:
      containers:
        - name: app
          image: my-repo/app:latest
""",
        encoding="utf-8",
    )
    result = audit_yaml_manifests(tmp_path)
    assert result.passed is False
    assert any("invalid YAML syntax" in e for e in result.errors)
    assert any(":latest" in e for e in result.errors)
    assert any("runAsNonRoot=true" in e for e in result.errors)


def test_audit_healthcheck_passes_and_fails_cleanly(live_health_url: str) -> None:
    ok_result = audit_healthcheck(live_health_url, timeout=2.0)
    assert ok_result.passed is True
    assert ok_result.errors == []

    bad_url = live_health_url.replace("/health", "/missing")
    fail_result = audit_healthcheck(bad_url, timeout=2.0)
    assert fail_result.passed is False
    assert any("404" in e for e in fail_result.errors)


def test_cli_exit_codes_for_valid_and_invalid_configs(tmp_path: Path, live_health_url: str) -> None:
    repo_tf = Path(__file__).resolve().parent.parent / "terraform"
    assert main(["--terraform-dir", str(repo_tf), "--health-url", live_health_url]) == 0

    (tmp_path / "bad.tf").write_text('variable "x" {}\n', encoding="utf-8")
    assert main(["--terraform-dir", str(tmp_path)]) != 0
    assert main([]) != 0
