#!/usr/bin/env python3
"""Aggregate the classified evaluation publications into an atlas summary + CSV."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "classified.jsonl"
SUMMARY = ROOT / "data" / "atlas_summary.json"
CSV_OUT = ROOT / "data" / "evaluation_atlas.csv"


def main() -> None:
    rows = [json.loads(l) for l in SRC.open()]
    et, ms, orgs, by_year = Counter(), Counter(), Counter(), Counter()
    for r in rows:
        et[r["evaluation_type"]] += 1
        ms[r["method_signal"]] += 1
        for o in r.get("organisations", []):
            orgs[o] += 1
        if r.get("published"):
            by_year[r["published"][:4]] += 1

    method_stated = sum(v for k, v in ms.items() if k != "unstated")
    summary = {
        "meta": {
            "source": "GOV.UK Search API (document types: research, independent_report)",
            "source_url": "https://www.gov.uk/api/search.json",
            "licence": "Open Government Licence v3.0",
            "n_publications": len(rows),
            "classification_note": "Labels are assigned from each publication's title and description (its own declared framing), by a locally hosted open-weights model, not from a reading of the full report.",
            "year_range": [min(by_year), max(by_year)] if by_year else None,
        },
        "evaluation_type": dict(et.most_common()),
        "method_signal": dict(ms.most_common()),
        "method_declared_rate": round(method_stated / len(rows), 4),
        "top_commissioners": orgs.most_common(15),
        "by_year": dict(sorted(by_year.items())),
    }
    SUMMARY.write_text(json.dumps(summary, indent=2))

    with CSV_OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["title", "url", "published", "document_type", "organisations", "evaluation_type", "method_signal"])
        for r in rows:
            w.writerow([r["title"], r["url"], r.get("published", ""), r.get("document_type", ""),
                        "; ".join(r.get("organisations", [])), r["evaluation_type"], r["method_signal"]])

    print(f"{len(rows)} publications")
    print(f"method declared in metadata: {summary['method_declared_rate']*100:.1f}%")
    print("types:", dict(et.most_common()))


if __name__ == "__main__":
    main()
