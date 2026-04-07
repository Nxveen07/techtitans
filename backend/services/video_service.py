import re
from typing import Optional, Dict, Any
from youtube_transcript_api import YouTubeTranscriptApi
import requests
from bs4 import BeautifulSoup

def extract_youtube_id(url: str) -> Optional[str]:
    """Extract the YouTube video ID from a URL."""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
        r"embed\/([0-9A-Za-z_-]{11})",
        r"shorts\/([0-9A-Za-z_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_youtube_video_info(video_id: str) -> Dict[str, Any]:
    """Get basic metadata for a YouTube video using oEmbed or basic scraping."""
    info = {"title": "", "description": "", "author": ""}
    try:
        # Using oEmbed is cleaner for title and author
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        resp = requests.get(oembed_url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            info["title"] = data.get("title", "")
            info["author"] = data.get("author_name", "")
        
        # For description, we might need basic scraping or just rely on the transcript
        # Basic scraping for description (often truncated in HTML, but better than nothing)
        headers = {"User-Agent": "Mozilla/5.0 TruthTrace_Bot"}
        page_resp = requests.get(f"https://www.youtube.com/watch?v={video_id}", headers=headers, timeout=5)
        if page_resp.status_code == 200:
            soup = BeautifulSoup(page_resp.text, "html.parser")
            desc_tag = soup.find("meta", {"name": "description"})
            if desc_tag:
                info["description"] = desc_tag.get("content", "")
    except Exception:
        pass
    return info

def get_video_content(url: str) -> Dict[str, Any]:
    """
    Detects if the URL is a video and extracts transcript + metadata.
    Returns a dict with 'text', 'metadata', and 'is_video'.
    """
    video_id = extract_youtube_id(url)
    if not video_id:
        return {"is_video": False, "text": "", "metadata": {}}

    result = {
        "is_video": True,
        "video_id": video_id,
        "platform": "YouTube",
        "metadata": get_youtube_video_info(video_id),
        "transcript": ""
    }

    try:
        # Instantiate the API as it's not a static method in this version
        api = YouTubeTranscriptApi()
        transcript_list = api.fetch(video_id, languages=['en', 'hi', 'es'])
        full_transcript = " ".join([item.text for item in transcript_list])
        result["transcript"] = full_transcript
    except Exception as e:
        result["transcript_error"] = str(e)
        result["transcript"] = ""

    # Combine metadata and transcript for analysis
    combined_text = f"VIDEO TITLE: {result['metadata'].get('title')}\n"
    combined_text += f"CHANNEL: {result['metadata'].get('author')}\n"
    if result["metadata"].get("description"):
        combined_text += f"DESCRIPTION: {result['metadata'].get('description')}\n"
    
    if result["transcript"]:
        combined_text += f"\nTRANSCRIPT:\n{result['transcript']}"
    else:
        combined_text += f"\n(Transcript unavailable: {result.get('transcript_error', 'Private or disabled')})"

    result["text"] = combined_text[:6000] # Cap for LLM context
    return result
