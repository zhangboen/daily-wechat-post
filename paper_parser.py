from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Paper:
    title: str
    ranked_topic: str
    authors: str
    journal: str
    publication_date: str
    identifier: str
    url: str
    abstract: str


def _field(block: str, label: str) -> str:
    pattern = rf"^{re.escape(label)}:\s*(.*?)(?=\n[A-Z][A-Za-z ]+?:|\nAbstract:|\Z)"
    match = re.search(pattern, block, flags=re.MULTILINE | re.DOTALL)
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""


def parse_papers(email_body: str) -> list[Paper]:
    blocks = re.split(r"\n(?=\d+\.\s+)", email_body.strip())
    papers: list[Paper] = []
    for block in blocks:
        title_match = re.match(r"(\d+)\.\s+(.+)", block)
        if not title_match:
            continue
        title = title_match.group(2).strip()
        abstract = _field(block, "Abstract")
        if abstract.lower().startswith("abstract."):
            abstract = abstract[9:].strip()
        elif abstract.lower().startswith("abstract "):
            abstract = abstract[8:].strip()
        papers.append(
            Paper(
                title=title,
                ranked_topic=_field(block, "Ranked topic"),
                authors=_field(block, "Authors"),
                journal=_field(block, "Journal"),
                publication_date=_field(block, "Publication date"),
                identifier=_field(block, "Identifier"),
                url=_field(block, "URL"),
                abstract=abstract,
            )
        )
    return papers
