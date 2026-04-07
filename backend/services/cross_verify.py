from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote_plus, urlparse

import requests


@dataclass(frozen=True)
class EvidenceItem:
    title: str
    url: str
    domain: str
    published_at: str | None = None


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _extract_query(text: str) -> str:
    """
    Create a compact search query from user text.
    We intentionally keep it simple and dependency-free.
    """
    t = _normalize_whitespace(text)
    # Drop URLs to avoid overly-specific queries
    t = re.sub(r"https?://\S+", " ", t)
    t = _normalize_whitespace(t)
    # Keep first ~18 words to avoid long queries
    words = t.split(" ")
    return " ".join(words[:18]) if words else ""


def _domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def _gdelt_search(query: str, maxrecords: int = 10, timeout_s: int = 6) -> list[EvidenceItem]:
    """
    Search news coverage using GDELT Doc 2.1 API (no API key required).
    Returns a small list of articles (title + url + domain).
    """
    q = _extract_query(query)
    if not q:
        return []

    # GDELT Doc 2.1 endpoint
    url = (
        "https://api.gdeltproject.org/api/v2/doc/doc"
        f"?query={quote_plus(q)}&mode=ArtList&format=json&maxrecords={int(maxrecords)}&sort=HybridRel"
    )
    resp = requests.get(url, timeout=timeout_s, headers={"User-Agent": "TruthTraceAI/1.0"})
    resp.raise_for_status()
    data: dict[str, Any] = resp.json()
    articles = data.get("articles") or []

    out: list[EvidenceItem] = []
    for a in articles:
        a_url = str(a.get("url") or "").strip()
        if not a_url:
            continue
        out.append(
            EvidenceItem(
                title=_normalize_whitespace(str(a.get("title") or ""))[:200] or "(untitled)",
                url=a_url,
                domain=_domain(a_url),
                published_at=str(a.get("seendate") or "") or None,
            )
        )
    # De-dup by url
    seen: set[str] = set()
    deduped: list[EvidenceItem] = []
    for item in out:
        if item.url in seen:
            continue
        seen.add(item.url)
        deduped.append(item)
    return deduped


def cross_verify(input_text_or_url: str) -> dict[str, Any]:
    """
    Cross-verify a claim by looking for related coverage across sources.
    Returns a corroboration score + evidence links.
    """
    evidence = _gdelt_search(input_text_or_url, maxrecords=12)
    domains = {e.domain for e in evidence if e.domain}
    coverage_count = len(evidence)
    domain_diversity = len(domains)

    # Heuristic corroboration score (0..1)
    # - more distinct domains increases confidence
    # - a few articles is usually enough for "corroborated", but not always
    coverage_score = min(1.0, coverage_count / 6.0)
    diversity_score = min(1.0, domain_diversity / 4.0)
    corroboration = 0.65 * coverage_score + 0.35 * diversity_score

    return {
        "provider": "gdelt",
        "query": _extract_query(input_text_or_url),
        "coverage_count": coverage_count,
        "domain_diversity": domain_diversity,
        "corroboration": round(float(corroboration), 3),
        "evidence": [
            {
                "title": e.title,
                "url": e.url,
                "domain": e.domain,
                "published_at": e.published_at,
            }
            for e in evidence[:10]
        ],
    }

