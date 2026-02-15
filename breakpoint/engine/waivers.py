from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from breakpoint.engine.reason_codes import DECISION_TO_INTERNAL, INTERNAL_TO_DECISION
from breakpoint.engine.policies.base import PolicyResult
from breakpoint.engine.errors import ConfigValidationError


@dataclass(frozen=True)
class Waiver:
    reason_code: str
    expires_at: str
    reason: str
    issued_by: str | None = None
    ticket: str | None = None


def parse_evaluation_time(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("metadata.evaluation_time must be a non-empty ISO-8601 string.")
    return _parse_iso8601_utc(value.strip())


def parse_waivers(raw: object) -> list[Waiver]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ConfigValidationError("Config key 'waivers' must be an array.")

    waivers: list[Waiver] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ConfigValidationError(f"Config key 'waivers[{idx}]' must be an object.")
        reason_code = item.get("reason_code")
        expires_at = item.get("expires_at")
        reason = item.get("reason")
        if not isinstance(reason_code, str) or not reason_code.strip():
            raise ConfigValidationError(
                f"Config key 'waivers[{idx}].reason_code' must be a non-empty string."
            )
        if not isinstance(expires_at, str) or not expires_at.strip():
            raise ConfigValidationError(
                f"Config key 'waivers[{idx}].expires_at' must be a non-empty string."
            )
        if not isinstance(reason, str) or not reason.strip():
            raise ConfigValidationError(f"Config key 'waivers[{idx}].reason' must be a non-empty string.")

        # Validate timestamp deterministically. We do not check "expired" here since that depends on evaluation_time.
        _parse_iso8601_utc(expires_at.strip())

        issued_by = item.get("issued_by")
        if issued_by is not None and not isinstance(issued_by, str):
            raise ConfigValidationError(f"Config key 'waivers[{idx}].issued_by' must be a string.")
        ticket = item.get("ticket")
        if ticket is not None and not isinstance(ticket, str):
            raise ConfigValidationError(f"Config key 'waivers[{idx}].ticket' must be a string.")

        waivers.append(
            Waiver(
                reason_code=reason_code.strip(),
                expires_at=expires_at.strip(),
                reason=reason.strip(),
                issued_by=issued_by.strip() if isinstance(issued_by, str) else None,
                ticket=ticket.strip() if isinstance(ticket, str) else None,
            )
        )

    # Deterministic order (for metadata emission and stable behavior).
    return sorted(waivers, key=lambda w: (w.reason_code, w.expires_at, w.reason))


def apply_waivers_to_policy_results(
    results: list[PolicyResult],
    waivers: list[Waiver],
    evaluation_time: datetime,
) -> tuple[list[PolicyResult], list[Waiver]]:
    active = [w for w in waivers if evaluation_time <= _parse_iso8601_utc(w.expires_at)]
    if not active:
        return results, []

    waived_internal_codes = _waived_internal_codes(active)
    filtered: list[PolicyResult] = []
    applied: dict[str, Waiver] = {}

    for result in results:
        kept_reasons: list[str] = []
        kept_codes: list[str] = []
        matched_any = False

        for reason, code in zip(result.reasons, result.codes, strict=True):
            if code in waived_internal_codes:
                matched_any = True
                continue
            kept_reasons.append(reason)
            kept_codes.append(code)

        if matched_any:
            for code in result.codes:
                if code in waived_internal_codes:
                    decision_code = INTERNAL_TO_DECISION.get(code, code)
                    waiver = _waiver_for_decision_code(active, decision_code)
                    if waiver is not None:
                        applied[waiver.reason_code] = waiver

        filtered.append(
            PolicyResult(
                policy=result.policy,
                status=_status_from_internal_codes(kept_codes),
                reasons=kept_reasons,
                codes=kept_codes,
                details=result.details,
            )
        )

    applied_list = sorted(applied.values(), key=lambda w: (w.reason_code, w.expires_at, w.reason))
    return filtered, applied_list


def _waived_internal_codes(waivers: list[Waiver]) -> set[str]:
    internal: set[str] = set()
    for w in waivers:
        decision_code = w.reason_code
        internal.add(DECISION_TO_INTERNAL.get(decision_code, decision_code))
    return internal


def _status_from_internal_codes(codes: list[str]) -> str:
    if not codes:
        return "ALLOW"
    decision_codes = [INTERNAL_TO_DECISION.get(c, c) for c in codes]
    if any(c.endswith("_BLOCK") for c in decision_codes):
        return "BLOCK"
    if any(c.endswith("_WARN") for c in decision_codes):
        return "WARN"
    # Unknown/other codes default to WARN (conservative but non-breaking).
    return "WARN"


def _waiver_for_decision_code(waivers: list[Waiver], decision_code: str) -> Waiver | None:
    for w in waivers:
        if w.reason_code == decision_code:
            return w
    return None


def _parse_iso8601_utc(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"

    # Support date-only inputs as end-of-day UTC.
    if len(raw) == 10 and raw[4] == "-" and raw[7] == "-":
        dt = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
        return dt.replace(hour=23, minute=59, second=59, microsecond=0)

    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
