import re

from breakpoint.engine.policies.base import PolicyResult


def evaluate_pii_policy(candidate: dict, patterns: dict, allowlist: list[str]) -> PolicyResult:
    text = candidate.get("output", "")
    if not isinstance(text, str):
        text = str(text)

    blocked_type_counts: dict[str, int] = {}
    compiled_allowlist = [re.compile(item) for item in allowlist]
    for label, pattern in patterns.items():
        regex = re.compile(pattern)
        count = 0
        for match in regex.finditer(text):
            value = match.group(0)
            if _is_allowlisted_value(value, compiled_allowlist):
                continue
            if label.lower() == "credit_card" and not _is_luhn_valid(value):
                continue
            count += 1
        if count > 0:
            blocked_type_counts[label.upper()] = count

    if blocked_type_counts:
        blocked_patterns = sorted(blocked_type_counts.keys())
        total = sum(blocked_type_counts.values())
        parts = [f"{name}({blocked_type_counts[name]})" for name in blocked_patterns]
        return PolicyResult(
            policy="pii",
            status="BLOCK",
            reasons=[f"PII detected: {', '.join(parts)}. Total matches: {total}."],
            codes=[f"PII_BLOCK_{name}" for name in blocked_patterns],
            details={
                "blocked_types": blocked_patterns,
                "blocked_type_counts": blocked_type_counts,
                "blocked_total": total,
            },
        )
    return PolicyResult(policy="pii", status="ALLOW")


def _is_allowlisted_value(value: str, allowlist: list[re.Pattern]) -> bool:
    for allowed in allowlist:
        if allowed.search(value):
            return True
    return False


def _is_luhn_valid(value: str) -> bool:
    candidate = re.sub(r"[^0-9]", "", value)
    if not 13 <= len(candidate) <= 19:
        return False
    return _luhn_check(candidate)


def _luhn_check(value: str) -> bool:
    total = 0
    parity = (len(value) - 2) % 2
    for index, ch in enumerate(value):
        digit = ord(ch) - ord("0")
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0
