# UK Government Evaluation Evidence Atlas

An open, classified atlas of **1,770** UK government evaluation publications,
harvested from the GOV.UK Search API and labelled by evaluation type and
declared method. A map of what government evaluates, who commissions it, and how
openly it states its methods.

| | |
|---|---|
| Publications | **1,770** |
| Document types | research, independent_report |
| Year range | 1996–2026 |
| Source | GOV.UK Search API |
| Licence | Open Government Licence v3.0 |

## The finding

Impact evaluations dominate the published record (886 of 1,770), ahead of
process (391), mixed (139), feasibility (108) and economic (91). But the sharper
result is about transparency: **only 11% of publications declare a recognisable
method in their title or description.** Where a method is stated, qualitative
(60) and survey/monitoring (50) lead; randomised designs are named in just 19.
The largest commissioners are DfID, DfE and DWP.

## Honest about method

Labels are assigned from each publication's **title and description** (its own
declared framing), by a locally hosted open-weights model, not from a reading of
the full report. The atlas therefore measures how evaluations *present*
themselves in the public catalogue, which is exactly the surface a searcher or
an automated evidence-synthesis tool sees first. Publications the model cannot
place are labelled `unclear`, not guessed.

## Files

- `data/atlas_summary.json` — counts by type, method, commissioner and year
- `data/evaluation_atlas.csv` — one row per publication with labels and URL
- `data/classified.jsonl` — full classified records
- `scripts/harvest.py`, `scripts/classify.py`, `scripts/build_atlas.py`

## Reproduce

```bash
python3 scripts/harvest.py    # harvest from the GOV.UK Search API
python3 scripts/classify.py   # classify (local open-weights model)
python3 scripts/build_atlas.py
```

Contains public sector information licensed under the Open Government Licence
v3.0. Independent, self-initiated open research by
[Tesseract Academy](https://gov.tesseract.academy).
