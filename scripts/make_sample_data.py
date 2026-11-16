#!/usr/bin/env python3
"""PREVIEW ONLY: writes made-up contribution data so the cards can be rendered offline.
The GitHub Action overwrites data/contributions.json with your real numbers."""
import datetime as dt
import json
import pathlib
import random

random.seed(7)
end = dt.date(2026, 11, 16)
days = []
for i in range(364, -1, -1):
    d = end - dt.timedelta(days=i)
    busy = 1.0 + 1.6 * (d.month in (8, 9, 10)) + 0.8 * (d.month == 11)
    c = 0 if random.random() > 0.55 * busy else int(random.expovariate(1 / (3 * busy))) + 1
    days.append({"date": d.isoformat(), "count": min(c, 28)})
(pathlib.Path(__file__).resolve().parent.parent / "data" / "contributions.json").write_text(
    json.dumps({"sample": True, "days": days}))
