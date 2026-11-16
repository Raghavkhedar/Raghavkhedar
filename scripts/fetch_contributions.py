#!/usr/bin/env python3
"""Fetch the last year of contributions via the GitHub GraphQL API into data/contributions.json."""
import datetime as dt
import json
import os
import pathlib
import urllib.request

USER = os.environ.get("GH_USER", "Raghavkhedar")
TOKEN = os.environ["GITHUB_TOKEN"]
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "contributions.json"

QUERY = """query($u:String!,$from:DateTime!,$to:DateTime!){
  user(login:$u){contributionsCollection(from:$from,to:$to){
    contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""

now = dt.datetime.now(dt.timezone.utc)
body = json.dumps({"query": QUERY, "variables": {
    "u": USER,
    "from": (now - dt.timedelta(days=364)).strftime("%Y-%m-%dT00:00:00Z"),
    "to": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
}}).encode()
req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
    "Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "readme-cards"})
data = json.load(urllib.request.urlopen(req, timeout=30))
if "errors" in data:
    raise SystemExit(data["errors"])
weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
days = [{"date": d["date"], "count": d["contributionCount"]} for w in weeks for d in w["contributionDays"]]
OUT.write_text(json.dumps({"user": USER, "days": days}, indent=0))
print(f"wrote {len(days)} days to {OUT}")
