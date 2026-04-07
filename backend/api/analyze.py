from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.models import AnalysisLog
from db.session import SessionLocal
from services.cross_verify import cross_verify
from services.groq_factcheck import analyze_with_groq
from services.scraper import scrape_url_text


router = APIRouter()


class ContentRequest(BaseModel):
    content: str
    type: str = "url"


@router.post("/api/v1/content/analyze")
def analyze_content(req: ContentRequest):
    content_raw = req.content.strip()
    if not content_raw:
        raise HTTPException(status_code=400, detail="Please provide content to analyze.")

    analysis_text = content_raw
    if content_raw.startswith("http://") or content_raw.startswith("https://"):
        scraped = scrape_url_text(content_raw)
        if scraped:
            analysis_text = scraped

    if len(analysis_text) < 5 and not content_raw.startswith("http"):
        raise HTTPException(
            status_code=400,
            detail="Not enough text context. Please provide a longer claim or URL.",
        )

    is_video = "VIDEO TITLE:" in analysis_text and "TRANSCRIPT:" in analysis_text
    
    def _chatgpt_to_result(chatgpt_out: dict) -> dict:
        label = str(chatgpt_out.get("label", "UNCERTAIN")).upper()
        conf = int(chatgpt_out.get("confidence", 0))
        reason = str(chatgpt_out.get("reasoning", "")).strip() or "Groq analysis completed."
        red_flags = chatgpt_out.get("red_flags", []) if isinstance(chatgpt_out.get("red_flags"), list) else []
        verify_steps = (
            chatgpt_out.get("suggested_verification", [])
            if isinstance(chatgpt_out.get("suggested_verification"), list)
            else []
        )

        if label == "REAL":
            classification = "Verified Fact"
            fake_probability = max(0, min(100, 100 - conf))
            sentiment = "Neutral / Informative"
            fact = "The claim appears credible based on consistency and known evidence."
        elif label == "FAKE":
            classification = "Highly Suspicious"
            fake_probability = max(0, min(100, conf))
            sentiment = "Sensational / Risky"
            fact = "The claim appears false or fabricated based on available context."
        elif label == "MISLEADING":
            classification = "Unverified Claim"
            fake_probability = max(45, min(95, conf))
            sentiment = "Uncertain"
            fact = "The claim appears partially true but lacks important context."
        else:
            classification = "Unverified Claim"
            fake_probability = 50
            sentiment = "Uncertain"
            fact = "The claim cannot be confidently verified with available information."

        explanation_parts = [reason]
        if is_video:
            explanation_parts.insert(0, "[Video Analysis] Speech and metadata analyzed.")
        if red_flags:
            explanation_parts.append(f"Red flags: {', '.join(red_flags[:3])}.")

        source = "Groq AI fact-checking API"
        if verify_steps:
            source = f"{source} | Verify via: {verify_steps[0]}"

        claim = f'"{content_raw[:160]}..."' if len(content_raw) > 160 else f'"{content_raw}"'

        cross = chatgpt_out.get("cross_verification")
        cross_obj = cross if isinstance(cross, dict) else None

        return {
            "classification": classification,
            "fake_probability": fake_probability,
            "explanation": " ".join(explanation_parts),
            "bias_level": 50,
            "sentiment": sentiment,
            "claim": claim,
            "fact": fact,
            "source": source,
            "fact_check_label": label,
            "fact_check_confidence": conf,
            "red_flags": red_flags,
            "suggested_verification": verify_steps,
            "fact_check_provider": "groq",
            "cross_verification": cross_obj,
            "is_video": is_video
        }

    groq_result = analyze_with_groq(
        headline=content_raw[:180],
        article_text=analysis_text[:6000],
        source_name="User Input",
    )

    if groq_result is not None:
        result = _chatgpt_to_result(groq_result)
    else:
        raise HTTPException(
            status_code=503,
            detail="Groq analysis failed or is unavailable. Please check your API key and connection.",
        )

    # Cross-verification (best-effort). Prefer ChatGPT-produced cross-check when available.
    cross = result.get("cross_verification") if isinstance(result.get("cross_verification"), dict) else None
    if cross is None:
        try:
            cross = cross_verify(content_raw)
        except Exception:
            cross = None

    # Credibility score (0..100): combine model signal with cross-verification corroboration.
    # fake_probability is "likelihood of fake" in this UI, so we invert it to start.
    base_cred = max(0, min(100, 100 - int(result.get("fake_probability", 50))))
    if isinstance(cross, dict):
        if isinstance(cross.get("corroboration"), (int, float)):
            # Legacy corroboration (0..1)
            corr = float(cross["corroboration"])
            base_cred = int(round(base_cred * (0.65 + 0.35 * corr)))
        elif isinstance(cross.get("score"), (int, float)):
            # ChatGPT cross-verification score (0..100)
            corr = max(0.0, min(1.0, float(cross["score"]) / 100.0))
            base_cred = int(round(base_cred * (0.65 + 0.35 * corr)))
    result["credibility_score"] = base_cred
    if cross is not None:
        result["cross_verification"] = cross

    db = None
    try:
        db = SessionLocal()
        db.add(
            AnalysisLog(
                input_text=content_raw[:2000],
                classification=result["classification"],
                confidence=result["fake_probability"],
            )
        )
        db.commit()
    except Exception:
        pass
    finally:
        if db is not None:
            db.close()

    return {"status": "success", "analysis": result}


@router.get("/api/v1/analytics/dashboard")
def get_dashboard_stats():
    return {
        "threat_level": "Elevated",
        "items_verified": 12482,
        "ai_confidence": 98.5,
        "recent_alerts": [
            {"type": "fake", "title": "Deepfake Video Detected", "desc": "Origin: Telegram"},
            {
                "type": "suspicious",
                "title": "Suspicious Quote",
                "desc": "Political quote gaining traction",
            },
        ],
    }
