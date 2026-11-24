#!/usr/bin/env python3
"""Structured-logging CLI to audit Terraform variables, YAML manifests, and HTTP /health."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import yaml


SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("gcp_api_key", re.compile(r"AIza[0-9A-Za-z_-]{35}")),
    ("github_token", re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[0-9A-Za-z]{36}")),
    (
        "hardcoded_secret_assignment",
        re.compile(
            r"""(?i)\b(?:password|passwd|secret_key|api_key|access_token|private_key)\s*[:=]\s*["'][^$"'{][^"']{3,}["']"""
        ),
    ),
)

VARIABLE_HEADER_RE = re.compile(r'variable\s+"([^"]+)"\s*\{')


class JsonFormatter(logging.Formatter):
    """Formats audit logs as structured single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        event: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        details = getattr(record, "details", None)
        if isinstance(details, dict):
            event["details"] = details
        return json.dumps(event, ensure_ascii=False)


def configure_logger(level: str = "INFO") -> logging.Logger:
    """Create and configure the structured JSON logger."""
    logger = logging.getLogger("gcp_devops_demo.audit_cli")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(level.upper())
    logger.propagate = False
    return logger


LOGGER = configure_logger()


@dataclass
class AuditResult:
    """Aggregated result of an audit domain."""

    check: str
    passed: bool = True
    errors: list[str] = field(default_factory=list)
    checked_items: int = 0

    def add_error(self, message: str) -> None:
        self.passed = False
        self.errors.append(message)


def _scan_secrets(text: str, source: str, result: AuditResult) -> None:
    for pattern_name, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            result.add_error(f"{source}: potential hardcoded secret detected ({pattern_name})")


def _extract_variable_blocks(content: str) -> list[tuple[str, str]]:
    """Extract (variable_name, block_body) tuples from HCL content using brace balancing."""
    blocks: list[tuple[str, str]] = []
    pos = 0
    while True:
        match = VARIABLE_HEADER_RE.search(content, pos)
        if not match:
            break
        var_name = match.group(1)
        brace_start = match.end() - 1
        depth = 0
        idx = brace_start
        while idx < len(content):
            ch = content[idx]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    blocks.append((var_name, content[brace_start + 1 : idx]))
                    break
            idx += 1
        pos = idx + 1
    return blocks


def audit_terraform(tf_dir: Path) -> AuditResult:
    """Audit Terraform files for variable metadata, secret leaks, and forbidden .tfstate files."""
    result = AuditResult(check="terraform")

    if not tf_dir.exists() or not tf_dir.is_dir():
        result.add_error(f"Terraform directory does not exist: {tf_dir}")
        return result

    for state_file in tf_dir.rglob("*.tfstate*"):
        if ".terraform" not in state_file.parts:
            result.add_error(f"Forbidden Terraform state file present: {state_file}")

    tf_files = [
        path for path in sorted(tf_dir.rglob("*.tf")) if ".terraform" not in path.parts
    ]
    if not tf_files:
        result.add_error(f"No .tf files found under {tf_dir}")
        return result

    for tf_file in tf_files:
        result.checked_items += 1
        content = tf_file.read_text(encoding="utf-8")
        _scan_secrets(content, str(tf_file), result)

        for var_name, body in _extract_variable_blocks(content):
            if not re.search(r"(?m)^\s*description\s*=", body):
                result.add_error(
                    f"{tf_file}: variable '{var_name}' is missing required 'description'"
                )
            if not re.search(r"(?m)^\s*type\s*=", body):
                result.add_error(
                    f"{tf_file}: variable '{var_name}' is missing required 'type'"
                )

    LOGGER.info(
        "terraform_audit_completed",
        extra={
            "details": {
                "directory": str(tf_dir),
                "files_checked": result.checked_items,
                "passed": result.passed,
                "error_count": len(result.errors),
            }
        },
    )
    return result


def _validate_k8s_or_argocd_doc(doc: dict[str, Any], source: str, result: AuditResult) -> None:
    api_version = doc.get("apiVersion")
    kind = doc.get("kind")
    metadata = doc.get("metadata")

    if not isinstance(api_version, str) or not api_version.strip():
        result.add_error(f"{source}: missing or empty 'apiVersion'")
    if not isinstance(kind, str) or not kind.strip():
        result.add_error(f"{source}: missing or empty 'kind'")
    if not isinstance(metadata, dict) or not isinstance(metadata.get("name"), str) or not metadata["name"].strip():
        result.add_error(f"{source}: missing or empty 'metadata.name'")

    spec = doc.get("spec")
    if kind == "Deployment":
        if not isinstance(spec, dict):
            result.add_error(f"{source}: Deployment missing 'spec'")
            return
        pod_spec = spec.get("template", {}).get("spec", {})
        containers = pod_spec.get("containers")
        if not isinstance(containers, list) or not containers:
            result.add_error(f"{source}: Deployment missing non-empty 'spec.template.spec.containers'")
            return
        pod_non_root = (pod_spec.get("securityContext") or {}).get("runAsNonRoot") is True
        for container in containers:
            if not isinstance(container, dict):
                result.add_error(f"{source}: invalid container entry in Deployment")
                continue
            image = str(container.get("image", ""))
            if not image:
                result.add_error(f"{source}: container missing 'image'")
            elif image.endswith(":latest"):
                result.add_error(f"{source}: container image '{image}' must not use ':latest' tag")
            container_non_root = (container.get("securityContext") or {}).get("runAsNonRoot") is True
            if not (pod_non_root or container_non_root):
                result.add_error(
                    f"{source}: container '{container.get('name', 'unknown')}' must enforce securityContext.runAsNonRoot=true"
                )

    elif kind == "Service":
        if not isinstance(spec, dict):
            result.add_error(f"{source}: Service missing 'spec'")
            return
        if not isinstance(spec.get("ports"), list) or not spec["ports"]:
            result.add_error(f"{source}: Service missing non-empty 'spec.ports'")
        if not isinstance(spec.get("selector"), dict) or not spec["selector"]:
            result.add_error(f"{source}: Service missing non-empty 'spec.selector'")

    elif kind == "Application" and isinstance(api_version, str) and api_version.startswith("argoproj.io/"):
        if not isinstance(spec, dict):
            result.add_error(f"{source}: ArgoCD Application missing 'spec'")
            return
        source_cfg = spec.get("source")
        dest_cfg = spec.get("destination")
        automated = (spec.get("syncPolicy") or {}).get("automated")
        if not isinstance(source_cfg, dict) or not source_cfg.get("repoURL"):
            result.add_error(f"{source}: ArgoCD Application missing 'spec.source.repoURL'")
        if not isinstance(dest_cfg, dict) or not dest_cfg.get("server"):
            result.add_error(f"{source}: ArgoCD Application missing 'spec.destination.server'")
        if not isinstance(automated, dict):
            result.add_error(f"{source}: ArgoCD Application missing 'spec.syncPolicy.automated'")
        else:
            if automated.get("prune") is not True:
                result.add_error(f"{source}: ArgoCD Application must set automated.prune=true")
            if automated.get("selfHeal") is not True:
                result.add_error(f"{source}: ArgoCD Application must set automated.selfHeal=true")


def audit_yaml_manifests(yaml_dir: Path) -> AuditResult:
    """Audit YAML manifests and workflows for syntax, required schema fields, and secrets."""
    result = AuditResult(check="yaml")

    if not yaml_dir.exists() or not yaml_dir.is_dir():
        result.add_error(f"YAML directory does not exist: {yaml_dir}")
        return result

    yaml_files = sorted(list(yaml_dir.rglob("*.yaml")) + list(yaml_dir.rglob("*.yml")))
    if not yaml_files:
        result.add_error(f"No YAML files found under {yaml_dir}")
        return result

    for yaml_file in yaml_files:
        result.checked_items += 1
        raw_text = yaml_file.read_text(encoding="utf-8")
        _scan_secrets(raw_text, str(yaml_file), result)

        try:
            docs = list(yaml.safe_load_all(raw_text))
        except yaml.YAMLError as exc:
            result.add_error(f"{yaml_file}: invalid YAML syntax: {exc}")
            continue

        non_empty_docs = [doc for doc in docs if doc is not None]
        if not non_empty_docs:
            result.add_error(f"{yaml_file}: YAML file contains no documents")
            continue

        for idx, doc in enumerate(non_empty_docs, start=1):
            source = f"{yaml_file}[doc#{idx}]"
            if not isinstance(doc, dict):
                result.add_error(f"{source}: top-level YAML document must be a mapping")
                continue

            if "apiVersion" in doc or "kind" in doc:
                _validate_k8s_or_argocd_doc(doc, source, result)
            elif "jobs" in doc:
                jobs = doc.get("jobs")
                if not isinstance(jobs, dict) or not jobs:
                    result.add_error(f"{source}: workflow 'jobs' must be a non-empty mapping")

    LOGGER.info(
        "yaml_audit_completed",
        extra={
            "details": {
                "directory": str(yaml_dir),
                "files_checked": result.checked_items,
                "passed": result.passed,
                "error_count": len(result.errors),
            }
        },
    )
    return result


def audit_healthcheck(url: str, timeout: float = 5.0) -> AuditResult:
    """Validate that the target /health HTTP endpoint returns HTTP 200 and JSON status='ok'."""
    result = AuditResult(check="healthcheck", checked_items=1)
    request = urllib.request.Request(url=url, method="GET", headers={"Accept": "application/json"})

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status_code = getattr(response, "status", response.getcode())
            body = response.read().decode("utf-8")
            if status_code != 200:
                result.add_error(f"Healthcheck {url} returned unexpected HTTP status {status_code}")
            else:
                try:
                    payload = json.loads(body)
                except json.JSONDecodeError as exc:
                    result.add_error(f"Healthcheck {url} returned invalid JSON: {exc}")
                else:
                    if not isinstance(payload, dict) or payload.get("status") != "ok":
                        result.add_error(
                            f"Healthcheck {url} JSON payload missing expected status='ok': {payload}"
                        )
    except urllib.error.HTTPError as exc:
        result.add_error(f"Healthcheck {url} failed with HTTP error {exc.code}")
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        result.add_error(f"Healthcheck {url} connection error: {exc}")

    LOGGER.info(
        "healthcheck_audit_completed",
        extra={
            "details": {
                "url": url,
                "passed": result.passed,
                "error_count": len(result.errors),
            }
        },
    )
    return result


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Terraform variables, YAML manifests, and HTTP /health endpoints."
    )
    parser.add_argument(
        "--terraform-dir",
        type=Path,
        help="Path to Terraform root or module directory to audit.",
    )
    parser.add_argument(
        "--yaml-dir",
        type=Path,
        action="append",
        default=[],
        help="Path to directory containing YAML manifests/workflows (repeatable).",
    )
    parser.add_argument(
        "--health-url",
        type=str,
        help="HTTP URL of the microservice /health endpoint to verify.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="HTTP request timeout in seconds for --health-url (default: 5.0).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    results: list[AuditResult] = []

    if args.terraform_dir:
        results.append(audit_terraform(args.terraform_dir))
    for yaml_dir in args.yaml_dir:
        results.append(audit_yaml_manifests(yaml_dir))
    if args.health_url:
        results.append(audit_healthcheck(args.health_url, timeout=args.timeout))

    if not results:
        LOGGER.error(
            "no_audit_targets_specified",
            extra={"details": {"hint": "Pass --terraform-dir, --yaml-dir, and/or --health-url"}},
        )
        return 2

    all_errors = [err for res in results for err in res.errors]
    if all_errors:
        for err in all_errors:
            LOGGER.error("audit_violation", extra={"details": {"error": err}})
        return 1

    LOGGER.info(
        "all_audits_passed",
        extra={
            "details": {
                "checks": [res.check for res in results],
                "total_checked_items": sum(res.checked_items for res in results),
            }
        },
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
