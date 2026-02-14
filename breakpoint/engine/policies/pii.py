import re

from breakpoint.engine.policies.base import PolicyResult


def evaluate_pii_policy(candidate: dict, patterns: dict, allowlist: list[str]) -> PolicyResult:
    text = candidate.get("output", "")
    if not isinstance(text, str):
        text = str(text)

    blocked_patterns = []
    compiled_allowlist = [re.compile(item) for item in allowlist]
    for label, pattern in patterns.items():
        regex = re.compile(pattern)
        if not regex.search(text):
            continue
        if _is_allowlisted(text, regex, compiled_allowlist):
            continue
        if label.lower() == "credit_card" and not _has_luhn_valid_match(text, regex):
            continue
        blocked_patterns.append(label.upper())

    if blocked_patterns:
        return PolicyResult(
            policy="pii",
            status="BLOCK",
            reasons=[f"PII detected: {', '.join(blocked_patterns)}."],
            codes=[f"PII_BLOCK_{name}" for name in blocked_patterns],
        )
    return PolicyResult(policy="pii", status="ALLOW")


def _is_allowlisted(text: str, regex: re.Pattern, allowlist: list[re.Pattern]) -> bool:
    for match in regex.finditer(text):
        value = match.group(0)
        for allowed in allowlist:
            if allowed.search(value):
                return True
    return False


def _has_luhn_valid_match(text: str, regex: re.Pattern) -> bool:
    for match in regex.finditer(text):
        candidate = re.sub(r"[^0-9]", "", match.group(0))
        if 13 <= len(candidate) <= 19 and _luhn_check(candidate):
            return True
    return False


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
