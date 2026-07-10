#!/usr/bin/env python3
"""Harvest UK government evaluation publications from the GOV.UK Search API.

Collects publications of document type `research` and `independent_report`
matching the query "evaluation", keeps those whose title declares evaluative
intent, and writes one JSON record per publication.

GOV.UK content is Crown copyright, reused under the Open Government Licence v3.0.
"""
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://www.gov.uk/api/search.json"
FIELDS = [
    "title", "description", "link", "organisations",
    "public_timestamp", "content_store_document_type",
]
DOC_TYPES = ["research", "independent_report"]
PAGE = 500
OUT = Path(__file__).resolve().parent.parent / "data" / "raw_publications.jsonl"

# A publication is in scope if its title declares it an evaluation product.
TITLE_PATTERN = re.compile(
    r"\bevaluat(?:ion|ing|e[sd]?)\b|\brandomised controlled trial\b|\bimpact assessment of\b",
    re.IGNORECASE,
)


def fetch(params: dict) -> dict:
    url = API + "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={"User-Agent": "uk-evaluation-atlas/0.1 (open research; contact: fabio@thetesseractacademy.com)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def harvest() -> list[dict]:
    records: dict[str, dict] = {}
    for doc_type in DOC_TYPES:
        start, total = 0, None
        while total is None or start < total:
            batch = fetch({
                "q": "evaluation",
                "filter_content_store_document_type": doc_type,
                "count": PAGE,
                "start": start,
                "fields": FIELDS,
            })
            total = batch["total"]
            for r in batch["results"]:
                title = r.get("title", "")
                if not TITLE_PATTERN.search(title):
                    continue
                link = r.get("link", "")
                records[link] = {
                    "title": title,
                    "description": r.get("description"),
                    "url": "https://www.gov.uk" + link if link.startswith("/") else link,
                    "organisations": [
                        o.get("title") for o in r.get("organisations", []) if o.get("title")
                    ],
                    "published": r.get("public_timestamp"),
                    "document_type": r.get("content_store_document_type"),
                }
            start += PAGE
            print(f"{doc_type}: {min(start, total)}/{total} scanned, {len(records)} kept")
            time.sleep(0.5)
    return list(records.values())


if __name__ == "__main__":
    rows = harvest()
    rows.sort(key=lambda r: r.get("published") or "", reverse=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} records -> {OUT}")
