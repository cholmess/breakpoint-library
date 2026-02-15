from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class MetricsSummary:
    total: int
    by_schema_version: dict[str, int]
    by_status: dict[str, int]
    reason_code_counts: dict[str, int]
    waived_reason_code_counts: dict[str, int]
    waivers_applied_total: int
    mode_counts: dict[str, int]
    override_decision_total: int
    override_risk_counts: dict[str, int]
    ci_decision_total: int
    unique_project_total: int
    repeat_project_total: int

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "by_schema_version": dict(sorted(self.by_schema_version.items())),
            "by_status": dict(sorted(self.by_status.items())),
            "reason_code_counts": dict(sorted(self.reason_code_counts.items())),
            "waived_reason_code_counts": dict(sorted(self.waived_reason_code_counts.items())),
            "waivers_applied_total": self.waivers_applied_total,
            "mode_counts": dict(sorted(self.mode_counts.items())),
            "override_decision_total": self.override_decision_total,
            "override_risk_counts": dict(sorted(self.override_risk_counts.items())),
            "ci_decision_total": self.ci_decision_total,
            "unique_project_total": self.unique_project_total,
            "repeat_project_total": self.repeat_project_total,
        }


def summarize_decisions(paths: list[str]) -> MetricsSummary:
    file_paths = _expand_paths(paths)
    by_schema_version: dict[str, int] = {}
    by_status: dict[str, int] = {"ALLOW": 0, "WARN": 0, "BLOCK": 0}
    reason_code_counts: dict[str, int] = {}
    waived_reason_code_counts: dict[str, int] = {}
    waivers_applied_total = 0
    mode_counts: dict[str, int] = {}
    override_decision_total = 0
    override_risk_counts: dict[str, int] = {}
    ci_decision_total = 0
    project_counts: dict[str, int] = {}

    for path in file_paths:
        payload = _read_json(path)
        _validate_decision_payload(payload, source=path)

        schema_version = str(payload["schema_version"])
        by_schema_version[schema_version] = by_schema_version.get(schema_version, 0) + 1

        status = str(payload["status"]).upper()
        by_status[status] = by_status.get(status, 0) + 1

        for code in payload.get("reason_codes", []) or []:
            if isinstance(code, str) and code:
                reason_code_counts[code] = reason_code_counts.get(code, 0) + 1

        metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata"), dict) else {}

        mode = metadata.get("mode")
        if isinstance(mode, str) and mode.strip():
            mode_counts[mode.strip().lower()] = mode_counts.get(mode.strip().lower(), 0) + 1

        accepted_risks = metadata.get("accepted_risks")
        if isinstance(accepted_risks, list):
            normalized_risks = []
            for item in accepted_risks:
                if isinstance(item, str) and item.strip():
                    normalized_risks.append(item.strip().lower())
            if normalized_risks:
                override_decision_total += 1
                for risk in sorted(set(normalized_risks)):
                    override_risk_counts[risk] = override_risk_counts.get(risk, 0) + 1

        if metadata.get("ci") is True:
            ci_decision_total += 1

        project_key = metadata.get("project_key")
        if isinstance(project_key, str) and project_key.strip():
            key = project_key.strip()
            project_counts[key] = project_counts.get(key, 0) + 1

        waivers = metadata.get("waivers_applied", [])
        if isinstance(waivers, list) and waivers:
            waivers_applied_total += len(waivers)
            for w in waivers:
                if not isinstance(w, dict):
                    continue
                rc = w.get("reason_code")
                if isinstance(rc, str) and rc:
                    waived_reason_code_counts[rc] = waived_reason_code_counts.get(rc, 0) + 1

    return MetricsSummary(
        total=len(file_paths),
        by_schema_version=by_schema_version,
        by_status=by_status,
        reason_code_counts=reason_code_counts,
        waived_reason_code_counts=waived_reason_code_counts,
        waivers_applied_total=waivers_applied_total,
        mode_counts=mode_counts,
        override_decision_total=override_decision_total,
        override_risk_counts=override_risk_counts,
        ci_decision_total=ci_decision_total,
        unique_project_total=len(project_counts),
        repeat_project_total=sum(1 for count in project_counts.values() if count >= 2),
    )


def decision_fingerprint(payload: dict) -> str:
    # Stable hash for joining to external labels. Canonicalize JSON first.
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _expand_paths(paths: list[str]) -> list[str]:
    if not paths:
        raise ValueError("At least one path is required.")

    out: list[str] = []
    for p in paths:
        if p == "-":
            out.append(p)
            continue
        if os.path.isdir(p):
            for root, _dirs, files in os.walk(p):
                for name in sorted(files):
                    if name.endswith(".json"):
                        out.append(os.path.join(root, name))
            continue
        out.append(p)

    # Deterministic order.
    return sorted(out)


def _read_json(path: str) -> dict:
    if path == "-":
        return json.loads(sys.stdin.read())
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _validate_decision_payload(payload: object, source: str) -> None:
    if not isinstance(payload, dict):
        raise ValueError(f"{source}: decision payload must be a JSON object.")
    for key in ("schema_version", "status", "reasons", "reason_codes"):
        if key not in payload:
            raise ValueError(f"{source}: missing required key '{key}'.")
    if not isinstance(payload["schema_version"], str) or not payload["schema_version"]:
        raise ValueError(f"{source}: key 'schema_version' must be a non-empty string.")
    if not isinstance(payload["status"], str) or payload["status"].upper() not in {"ALLOW", "WARN", "BLOCK"}:
        raise ValueError(f"{source}: key 'status' must be one of ALLOW|WARN|BLOCK.")
    if not isinstance(payload["reasons"], list) or not all(isinstance(x, str) for x in payload["reasons"]):
        raise ValueError(f"{source}: key 'reasons' must be an array of strings.")
    if not isinstance(payload["reason_codes"], list) or not all(isinstance(x, str) for x in payload["reason_codes"]):
        raise ValueError(f"{source}: key 'reason_codes' must be an array of strings.")
