"""
Fetch arXiv papers about LLMs (metadata + optional PDF download).

- Queries arXiv's API (Atom feed)
- Saves results to: path specified in config (out_jsonl)
- Optionally downloads PDFs to: path specified in config (pdf_dir)
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import requests
import feedparser
import yaml


# Default arXiv API URL (can be overridden via config)
DEFAULT_ARXIV_API = "https://export.arxiv.org/api/query"


def build_query(
    keywords: List[str],
    categories: Optional[List[str]] = None,
) -> str:
    """
    Build an arXiv API search query.

    - keywords are searched in title+abstract (via all:)
    - categories restrict to arXiv subject classes, e.g. cs.CL, cs.AI
    """
    kw_part = " OR ".join([f'all:"{kw}"' for kw in keywords])

    if categories:
        cat_part = " OR ".join([f"cat:{c}" for c in categories])
        return f"({kw_part}) AND ({cat_part})"

    return f"({kw_part})"


def arxiv_search(
    search_query: str,
    start: int = 0,
    max_results: int = 100,
    sort_by: str = "submittedDate",
    sort_order: str = "descending",
    timeout_s: int = 30,
    arxiv_api: str = DEFAULT_ARXIV_API,
) -> Dict:
    """
    Call arXiv API and return parsed feed.
    """
    params = {
        "search_query": search_query,
        "start": start,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": sort_order,
    }

    # arXiv sometimes prefers a descriptive User-Agent
    headers = {"User-Agent": "llm-rag-demo/0.1 (contact: example@example.com)"}

    r = requests.get(arxiv_api, params=params, headers=headers, timeout=timeout_s)
    r.raise_for_status()
    return feedparser.parse(r.text)


def normalize_arxiv_id(entry_id: str) -> str:
    # entry.id looks like: "http://arxiv.org/abs/2401.12345v2"
    m = re.search(r"/abs/([^/]+)$", entry_id)
    return m.group(1) if m else entry_id


def extract_pdf_url(entry) -> Optional[str]:
    # Find a link with rel="related" and type="application/pdf" if present
    for link in entry.get("links", []):
        if link.get("type") == "application/pdf":
            return link.get("href")
    # Fallback: convert abs -> pdf
    # e.g., http://arxiv.org/abs/2401.12345v2 -> http://arxiv.org/pdf/2401.12345v2.pdf
    if entry.get("id"):
        abs_url = entry["id"].replace("https://", "http://")
        if "/abs/" in abs_url:
            return abs_url.replace("/abs/", "/pdf/") + ".pdf"
    return None


def save_jsonl(path: str, records: List[Dict]) -> None:
    # Ensure the directory exists before opening the file
    dir_path = os.path.dirname(path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def download_pdf(pdf_url: str, out_path: str, timeout_s: int = 60) -> None:
    headers = {"User-Agent": "llm-rag-demo/0.1 (contact: example@example.com)"}
    with requests.get(pdf_url, headers=headers, stream=True, timeout=timeout_s) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 128):
                if chunk:
                    f.write(chunk)


def build_search_query(config: Dict) -> str:
    """Build arXiv query from config keywords and categories."""
    keywords = config.get("keywords", [])
    categories = config.get("ArXiv_categories", [])

    query = build_query(keywords=keywords, categories=categories)
    print("arXiv query:", query)
    return query


def fetch_entry(e: Dict[str, Any]) -> Dict:
    """Extract metadata from an arXiv entry and return as a record dict."""
    arxiv_id = normalize_arxiv_id(e.get("id", ""))
    title = (e.get("title") or "").replace("\n", " ").strip()
    summary = (e.get("summary") or "").replace("\n", " ").strip()

    authors = [a.get("name") for a in e.get("authors", []) if a.get("name")]
    published = e.get("published")
    updated = e.get("updated")

    pdf_url = extract_pdf_url(e)

    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "summary": summary,
        "authors": authors,
        "published": published,
        "updated": updated,
        "abs_url": e.get("id"),
        "pdf_url": pdf_url,
        "categories": [t.get("term") for t in e.get("tags", []) if t.get("term")],
        "fetched_at_utc": datetime.utcnow().isoformat() + "Z",
    }


def load_config(config_file: Optional[str] = None) -> Dict:
    """Load configuration from YAML file and validate required fields."""
    if config_file is None:
        config_file = os.path.join(os.path.dirname(__file__), "fetch_from_arxiv.config.yaml")
    
    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    # Set default for arxiv_api if not present
    if "arxiv_api" not in config:
        config["ArXiv_api"] = DEFAULT_ARXIV_API
    
    required_fields = ["out_jsonl", "download_pdfs", "pdf_dir", "batch_size", "total_to_fetch",
                       "keywords", "ArXiv_categories"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field '{field}' in config file: {config_file}")
    
    return config


def download_pdfs_for_records(records: List[Dict], pdf_dir: str) -> None:
    """
    Download PDFs for all records that have a pdf_url.
    
    Args:
        records: List of record dictionaries containing arxiv_id and pdf_url
        pdf_dir: Directory to save PDF files
    """
    os.makedirs(pdf_dir, exist_ok=True)

    for rec in records:
        pdf_url = rec.get("pdf_url")
        if not pdf_url:
            continue
        arxiv_id = rec["arxiv_id"]
        safe_name = arxiv_id.replace("/", "_")
        pdf_path = os.path.join(pdf_dir, f"{safe_name}.pdf")
        if not os.path.exists(pdf_path):
            try:
                download_pdf(pdf_url, pdf_path)
                print(f"Downloaded: {pdf_path}")
                # Be polite to arXiv
                time.sleep(1.0)
            except Exception as ex:
                print(f"PDF download failed for {arxiv_id}: {ex}")


def fetch_and_process_papers(
    query: str,
    config: Dict,
) -> List[Dict]:
    """
    Fetch papers from arXiv in batches and process them (save metadata, optionally download PDFs).
    
    Args:
        query: arXiv search query string
        config: Configuration dictionary containing:
            - out_jsonl: Path to output JSONL file for metadata
            - download_pdfs: Whether to download PDF files
            - pdf_dir: Directory to save PDFs
            - batch_size: Number of papers to fetch per API call
            - total_to_fetch: Total number of papers to fetch
            - arxiv_api: arXiv API endpoint URL
    """

    out_jsonl = config["out_jsonl"]
    batch_size = config["batch_size"]
    total_to_fetch = config["total_to_fetch"]
    arxiv_api = config["ArXiv_api"]
    
    # arXiv API is paginated: start=0,100,200...
    fetched = 0
    all_records = []
    while fetched < total_to_fetch:
        feed = arxiv_search(
            search_query=query,
            start=fetched,
            max_results=min(batch_size, total_to_fetch - fetched),
            arxiv_api=arxiv_api,
        )

        entries = feed.get("entries", [])
        if not entries:
            print("No more results.")
            break

        records = [fetch_entry(e) for e in entries]
        all_records.extend(records)
        fetched += len(entries)
        print(f"Fetched {fetched} total so far.")

        # Be polite to arXiv between batches
        time.sleep(1.0)

    # Save all records to JSONL
    save_jsonl(out_jsonl, all_records)
    print(f"Saved {len(all_records)} records to {out_jsonl}")

    return all_records


def main():
    config = load_config()    
    query = build_search_query(config)
    all_records = fetch_and_process_papers(
        query=query,
        config=config,
    )
    if config["download_pdfs"]:
        download_pdfs_for_records(all_records, config["pdf_dir"])


if __name__ == "__main__":
    main()
