from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup


def _doi_from_text(text: str) -> str | None:
    match = re.search(r"10\.\d{4,9}/\S+", text)
    if not match:
        return None
    return match.group(0).rstrip(".,;)")


def _clean_html(raw: str) -> str:
    soup = BeautifulSoup(raw, "html.parser")
    return soup.get_text(" ", strip=True)


def lookup_abstract(title: str, identifier: str, url: str) -> str:
    doi = _doi_from_text(identifier) or _doi_from_text(url)
    if doi:
        crossref_url = f"https://api.crossref.org/works/{doi}"
        try:
            data = requests.get(crossref_url, timeout=30).json()
            abstracts = data.get("message", {}).get("abstract") or []
            if isinstance(abstracts, str) and abstracts:
                return _clean_html(abstracts)
        except Exception:
            pass

        semantic_url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
        try:
            data = requests.get(semantic_url, params={"fields": "abstract"}, timeout=30).json()
            if data.get("abstract"):
                return data["abstract"].strip()
        except Exception:
            pass

    return ""
