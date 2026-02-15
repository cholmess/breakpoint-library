import re

from breakpoint.engine.policies.base import PolicyResult


def evaluate_drift_policy(baseline: dict, candidate: dict, thresholds: dict) -> PolicyResult:
    baseline_text = _as_text(baseline.get("output", ""))
    candidate_text = _as_text(candidate.get("output", ""))

    if not candidate_text.strip():
        return PolicyResult(
            policy="drift",
            status="BLOCK",
            reasons=["Candidate output is empty."],
            codes=["DRIFT_BLOCK_EMPTY"],
        )

    reasons = []
    codes = []
    details = {}

    baseline_len = max(1, len(baseline_text))
    candidate_len = len(candidate_text)
    delta_pct = abs(candidate_len - baseline_len) / baseline_len * 100
    short_ratio = candidate_len / baseline_len

    warn_delta = float(thresholds.get("warn_length_delta_pct", 60))
    warn_short_ratio = float(thresholds.get("warn_short_ratio", 0.35))
    min_similarity = float(thresholds.get("warn_min_similarity", 0.15))
    semantic_enabled = bool(thresholds.get("semantic_check_enabled", True))
    similarity_method = str(thresholds.get("similarity_method", "max(token_jaccard,char_3gram_jaccard)"))

    if delta_pct > warn_delta:
        direction = "expanded" if candidate_len > baseline_len else "compressed"
        reasons.append(
            f"Response length {direction} by {delta_pct:.1f}% (threshold {warn_delta:.0f}%)."
        )
        codes.append("DRIFT_WARN_LENGTH_DELTA")
        details["length_delta_pct"] = delta_pct

    if short_ratio < warn_short_ratio:
        shrink_pct = (1 - short_ratio) * 100
        reasons.append(
            f"Response appears over-compressed: {shrink_pct:.1f}% shorter than baseline "
            f"(ratio {short_ratio:.2f}, threshold {warn_short_ratio:.2f})."
        )
        codes.append("DRIFT_WARN_SHORT_OUTPUT")
        details["short_ratio"] = short_ratio

    if semantic_enabled:
        similarity = _similarity(baseline_text, candidate_text, method=similarity_method)
        details["similarity"] = similarity
        details["similarity_method"] = similarity_method
        if similarity < min_similarity:
            reasons.append(
                f"Response content overlap is low: similarity {similarity:.2f} "
                f"(threshold {min_similarity:.2f})."
            )
            codes.append("DRIFT_WARN_LOW_SIMILARITY")

    if reasons:
        return PolicyResult(policy="drift", status="WARN", reasons=reasons, codes=codes, details=details)
    return PolicyResult(policy="drift", status="ALLOW", details=details)


def _token_overlap_similarity(left: str, right: str) -> float:
    left_tokens = set(_tokenize(left))
    right_tokens = set(_tokenize(right))
    union = left_tokens | right_tokens
    if not union:
        return 1.0
    intersection = left_tokens & right_tokens
    return len(intersection) / len(union)


def _char_ngram_jaccard(left: str, right: str, n: int) -> float:
    left_grams = set(_char_ngrams(_normalize_for_ngrams(left), n))
    right_grams = set(_char_ngrams(_normalize_for_ngrams(right), n))
    union = left_grams | right_grams
    if not union:
        return 1.0
    return len(left_grams & right_grams) / len(union)


def _normalize_for_ngrams(value: str) -> str:
    # Keep it deterministic and cheap: lowercase and keep basic word chars/spaces.
    return " ".join(re.findall(r"[a-zA-Z0-9_]+", value.lower()))


def _char_ngrams(value: str, n: int) -> list[str]:
    if n <= 0:
        return []
    if len(value) < n:
        return []
    return [value[i : i + n] for i in range(0, len(value) - n + 1)]


def _similarity(left: str, right: str, method: str) -> float:
    if method == "token_jaccard":
        return _token_overlap_similarity(left, right)
    if method == "char_3gram_jaccard":
        return _char_ngram_jaccard(left, right, 3)
    if method.startswith("max(") and method.endswith(")"):
        items = [item.strip() for item in method[4:-1].split(",") if item.strip()]
        scores = [_similarity(left, right, item) for item in items] if items else [1.0]
        return max(scores)
    return _token_overlap_similarity(left, right)


def _tokenize(value: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9_]+", value.lower())


def _as_text(value: object) -> str:
    if isinstance(value, str):
        return value
    return str(value)
