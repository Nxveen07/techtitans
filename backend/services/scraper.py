import requests
from bs4 import BeautifulSoup


def scrape_url_text(url: str) -> str:
    """Fetch URL and return cleaned visible text."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 TruthTrace_Bot"}
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for element in soup(["script", "style", "nav", "footer", "aside"]):
            element.extract()

        text = soup.get_text(separator=" ")
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = "\n".join(chunk for chunk in chunks if chunk)
        return clean_text[:5000]
    except Exception:
        return ""
