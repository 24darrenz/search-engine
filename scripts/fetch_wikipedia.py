#!/usr/bin/env python
"""Fetch Wikipedia articles as plain-text .txt files into data/raw/.

Usage:
    # Random articles:
    python scripts/fetch_wikipedia.py --random 100

    # Articles from one or more categories, recursing into subcategories
    # (most Wikipedia categories hold few direct articles -- the bulk of
    # their content lives one or two levels down in subcategories):
    python scripts/fetch_wikipedia.py --category "Computer science" --limit 150 --depth 2

    python scripts/fetch_wikipedia.py --category "Computer science" --category "Operating systems" --limit 150

Requires: pip install requests
"""
import argparse
import re
import sys
import time
from pathlib import Path

import requests

API_URL = "https://en.wikipedia.org/w/api.php"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
HEADERS = {"User-Agent": "search-engine-project/1.0 (student portfolio project)"}


def safe_filename(title: str) -> str:
    name = re.sub(r"[^\w\-]+", "_", title).strip("_")
    return name[:150] + ".txt"


def api_get(params: dict, max_retries: int = 5) -> dict:
    """GET with retry/backoff on 429 (rate limit) and transient 5xx errors."""
    delay = 1.0
    for attempt in range(max_retries):
        resp = requests.get(API_URL, params=params, headers=HEADERS)
        if resp.status_code == 429:
            wait = float(resp.headers.get("Retry-After", delay))
            print(f"    rate limited, waiting {wait:.1f}s...")
            time.sleep(wait)
            delay *= 2
            continue
        if resp.status_code >= 500:
            time.sleep(delay)
            delay *= 2
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()  # give up, surface the last error


def fetch_article_text(title: str) -> str | None:
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "extracts",
        "explaintext": True,
    }
    data = api_get(params)
    pages = data.get("query", {}).get("pages", {})
    page = next(iter(pages.values()), None)
    if not page or "extract" not in page or not page["extract"].strip():
        return None
    return page["extract"]


def random_titles(n: int) -> list[str]:
    titles = []
    while len(titles) < n:
        batch_size = min(n - len(titles), 500)
        params = {
            "action": "query",
            "format": "json",
            "list": "random",
            "rnnamespace": 0,
            "rnlimit": batch_size,
        }
        data = api_get(params)
        batch = data["query"]["random"]
        titles.extend(p["title"] for p in batch)
        time.sleep(0.5)
    return titles


def category_members(category: str, limit: int) -> tuple[list[str], list[str]]:
    """Returns (article_titles, subcategory_names) for one category page."""
    articles, subcats = [], []
    cmcontinue = None
    while len(articles) < limit:
        params = {
            "action": "query",
            "format": "json",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmnamespace": "0|14",  # 0 = articles, 14 = subcategories
            "cmlimit": min(limit - len(articles), 500),
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        data = api_get(params)
        for m in data["query"]["categorymembers"]:
            if m["title"].startswith("Category:"):
                subcats.append(m["title"][len("Category:"):])
            else:
                articles.append(m["title"])
        cmcontinue = data.get("continue", {}).get("cmcontinue")
        time.sleep(0.5)
        if not cmcontinue:
            break
    return articles[:limit], subcats


def collect_titles_recursive(category: str, limit: int, depth: int) -> list[str]:
    """BFS over subcategories up to `depth` levels, collecting article
    titles until `limit` is reached."""
    seen_categories = {category}
    queue = [(category, 0)]
    titles: list[str] = []

    while queue and len(titles) < limit:
        current, level = queue.pop(0)
        remaining = limit - len(titles)
        print(f"  scanning category: {current!r} (depth {level})")
        articles, subcats = category_members(current, remaining)
        titles.extend(articles)

        if level < depth:
            for sub in subcats:
                if sub not in seen_categories:
                    seen_categories.add(sub)
                    queue.append((sub, level + 1))

    # de-dupe while preserving order
    return list(dict.fromkeys(titles))[:limit]


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--random", type=int, help="Number of random articles to fetch")
    group.add_argument(
        "--category", action="append", dest="categories",
        help="Wikipedia category name (without 'Category:'). Repeatable.",
    )
    parser.add_argument("--limit", type=int, default=100, help="Max articles total")
    parser.add_argument(
        "--depth", type=int, default=1,
        help="How many subcategory levels to recurse into (default 1). "
             "Most categories need at least 1 to find enough articles.",
    )
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds to wait between article fetches")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.random:
        titles = random_titles(args.random)
    else:
        per_category_limit = max(args.limit // len(args.categories), 1)
        titles = []
        for cat in args.categories:
            titles.extend(collect_titles_recursive(cat, per_category_limit, args.depth))
        titles = list(dict.fromkeys(titles))[: args.limit]

    print(f"\nFound {len(titles)} candidate titles\n")

    saved = 0
    for i, title in enumerate(titles, 1):
        try:
            text = fetch_article_text(title)
        except requests.RequestException as e:
            print(f"  [{i}/{len(titles)}] {title!r} -> request failed: {e}")
            continue

        if not text:
            print(f"  [{i}/{len(titles)}] {title!r} -> skipped (no content)")
            continue

        out_path = OUT_DIR / safe_filename(title)
        out_path.write_text(text, encoding="utf-8")
        saved += 1
        print(f"  [{i}/{len(titles)}] {title!r} -> saved ({len(text)} chars)")

        time.sleep(args.delay)

    print(f"\nSaved {saved}/{len(titles)} articles to {OUT_DIR}")


if __name__ == "__main__":
    main()
