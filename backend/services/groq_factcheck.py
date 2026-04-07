from __future__ import annotations

import json
import os
from typing import Any

import requests


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def _safe_json_loads(text: str) -> dict[str, Any] | None:
    try:
        data = json.loads(text)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def analyze_with_groq(headline: str, article_text: str, source_name: str | None = None) -> dict[str, Any] | None:
    """
    Returns structured fact-check JSON from Groq or None when unavailable.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return None

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    system_prompt = (
        "You are an expert fact-checking AI specialized in detecting fake news.\n\n"
        "Your job is to analyze news content and determine whether it is:\n"
        "- REAL\n- FAKE\n- MISLEADING\n- UNCERTAIN\n\n"
        "Base your decision on:\n"
        "- Logical consistency\n"
        "- Known facts and general knowledge\n"
        "- Presence of sensationalism or exaggeration\n"
        "- Credibility of claims\n"
        "- Language patterns typical of misinformation\n\n"
        "Additionally, perform cross-verification by checking whether the core claim is "
        "consistent with multiple independent, generally reliable references (for example: "
        "major wire services, peer-reviewed science bodies, government/statistical portals, "
        "recognized fact-checkers). If exact sources are unknown, state that clearly.\n\n"
        "Respond ONLY in valid JSON format with:\n"
        "{\n"
        '  "label": "REAL | FAKE | MISLEADING | UNCERTAIN",\n'
        '  "confidence": 0-100,\n'
        '  "reasoning": "short explanation",\n'
        '  "red_flags": ["list of suspicious elements"],\n'
        '  "suggested_verification": ["ways to verify this news"],\n'
        '  "cross_verification": {\n'
        '    "status": "CORROBORATED | PARTIALLY_CORROBORATED | NOT_CORROBORATED | INSUFFICIENT_EVIDENCE",\n'
        '    "score": 0-100,\n'
        '    "notes": "short summary of cross-check outcome",\n'
        '    "evidence": [\n'
        '      {\n'
        '        "title": "source/report title",\n'
        '        "url": "optional URL or empty",\n'
        '        "domain": "optional domain or empty",\n'
        '        "stance": "supports | contradicts | unclear"\n'
        "      }\n"
        "    ]\n"
        "  }\n"
        "}\n"
    )

    user_prompt = (
        "Analyze the following news and classify it:\n\n"
        f"Headline: {headline}\n"
        f"Content: {article_text}\n"
        f"Source: {source_name or 'Unknown'}\n\n"
        "Return the result in JSON only."
    )

    payload = {
        "model": model,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=12)
        resp.raise_for_status()
        body = resp.json()
        content = (
            body.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "{}")
        )
        parsed = _safe_json_loads(content if isinstance(content, str) else "{}")
        if not parsed:
            return None
    except Exception:
        return None

    allowed = {"REAL", "FAKE", "MISLEADING", "UNCERTAIN"}
    label = str(parsed.get("label", "UNCERTAIN")).upper().strip()
    if label not in allowed:
        label = "UNCERTAIN"

    try:
        confidence = int(round(float(parsed.get("confidence", 0))))
    except Exception:
        confidence = 0
    confidence = max(0, min(100, confidence))

    red_flags = parsed.get("red_flags")
    if not isinstance(red_flags, list):
        red_flags = []
    red_flags = [str(x) for x in red_flags][:8]

    suggested_verification = parsed.get("suggested_verification")
    if not isinstance(suggested_verification, list):
        suggested_verification = []
    suggested_verification = [str(x) for x in suggested_verification][:8]

    reasoning = str(parsed.get("reasoning", "")).strip()

    cross_raw = parsed.get("cross_verification")
    cross_verification = None
    if isinstance(cross_raw, dict):
        status_allowed = {
            "CORROBORATED",
            "PARTIALLY_CORROBORATED",
            "NOT_CORROBORATED",
            "INSUFFICIENT_EVIDENCE",
        }
        status = str(cross_raw.get("status", "INSUFFICIENT_EVIDENCE")).upper().strip()
        if status not in status_allowed:
            status = "INSUFFICIENT_EVIDENCE"
        try:
            score = int(round(float(cross_raw.get("score", 0))))
        except Exception:
            score = 0
        score = max(0, min(100, score))
        notes = str(cross_raw.get("notes", "")).strip()
        evidence_in = cross_raw.get("evidence")
        evidence_out: list[dict[str, Any]] = []
        if isinstance(evidence_in, list):
            for ev in evidence_in[:8]:
                if not isinstance(ev, dict):
                    continue
                evidence_out.append(
                    {
                        "title": str(ev.get("title", "")).strip() or "Reference",
                        "url": str(ev.get("url", "")).strip(),
                        "domain": str(ev.get("domain", "")).strip(),
                        "stance": str(ev.get("stance", "unclear")).strip().lower(),
                    }
                )
        cross_verification = {
            "status": status,
            "score": score,
            "notes": notes,
            "evidence": evidence_out,
            "provider": "groq_model_estimate",
        }

    return {
        "label": label,
        "confidence": confidence,
        "reasoning": reasoning,
        "red_flags": red_flags,
        "suggested_verification": suggested_verification,
        "cross_verification": cross_verification,
        "provider": "groq",
        "model": model,
    }

