#!/usr/bin/env python3
"""Classify harvested evaluation publications by evaluation type and method signal.

Classification is from title + published description ONLY (the publication
metadata), by a locally hosted open-weights model. Labels therefore represent
what the publication *declares about itself*, not a reading of the full report.
Records the model cannot place are labelled `unclear` rather than guessed.
"""
import json
import time
import urllib.request
from pathlib import Path

HOST = "http://localhost:8080/v1/chat/completions"
MODEL = "mlx-community/Qwen3-Coder-30B-A3B-Instruct-8bit"
DATA = Path(__file__).resolve().parent.parent / "data"
RAW = DATA / "raw_publications.jsonl"
OUT = DATA / "classified.jsonl"
BATCH = 15

EVAL_TYPES = {"impact", "process", "economic", "mixed", "feasibility", "evidence_synthesis", "unclear"}
METHODS = {"rct", "quasi_experimental", "theory_based", "qualitative", "survey_monitoring", "economic_model", "mixed_methods", "unstated"}

PROMPT = """You classify UK government evaluation publications using ONLY their title and description.

For each numbered item return a JSON object with:
- "i": the item number
- "evaluation_type": one of "impact" (measures whether outcomes changed), "process" (how a programme was implemented/delivered), "economic" (value for money, cost-benefit), "mixed" (explicitly both impact and process), "feasibility" (scoping/feasibility study for a future evaluation), "evidence_synthesis" (review/synthesis of existing evaluations), "unclear" (metadata does not say)
- "method_signal": one of "rct", "quasi_experimental", "theory_based", "qualitative", "survey_monitoring", "economic_model", "mixed_methods", "unstated" - ONLY if the title/description names or clearly implies the method, otherwise "unstated"

Be conservative: if the metadata does not state it, use "unclear"/"unstated". Do not guess.
Return ONLY a JSON array of the objects, no other text.

Items:
{items}"""


def call(prompt: str) -> str:
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 3000,
    }).encode()
    req = urllib.request.Request(HOST, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def parse(text: str, n: int):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1].lstrip("json").strip()
    try:
        arr = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(arr, list) or len(arr) != n:
        return None
    for o in arr:
        if o.get("evaluation_type") not in EVAL_TYPES or o.get("method_signal") not in METHODS:
            return None
    return arr


def main() -> None:
    rows = [json.loads(l) for l in RAW.open()]
    done = set()
    if OUT.exists():
        done = {json.loads(l)["url"] for l in OUT.open()}
    todo = [r for r in rows if r["url"] not in done]
    print(f"{len(todo)} to classify ({len(done)} already done)")
    out = OUT.open("a")
    for b in range(0, len(todo), BATCH):
        chunk = todo[b:b + BATCH]
        items = "\n".join(
            f"{i+1}. TITLE: {r['title']}\n   DESC: {(r.get('description') or '')[:300]}"
            for i, r in enumerate(chunk)
        )
        labels = None
        for attempt in range(3):
            try:
                labels = parse(call(PROMPT.format(items=items)), len(chunk))
            except Exception as e:
                print(f"batch {b//BATCH}: attempt {attempt} error {e}")
                time.sleep(5)
                continue
            if labels:
                break
        if not labels:
            labels = [{"i": i + 1, "evaluation_type": "unclear", "method_signal": "unstated"} for i in range(len(chunk))]
            print(f"batch {b//BATCH}: fell back to unclear")
        for r, lab in zip(chunk, sorted(labels, key=lambda o: o["i"])):
            r["evaluation_type"] = lab["evaluation_type"]
            r["method_signal"] = lab["method_signal"]
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
        out.flush()
        print(f"batch {b//BATCH + 1}/{(len(todo) + BATCH - 1)//BATCH} done")
    out.close()


if __name__ == "__main__":
    main()
