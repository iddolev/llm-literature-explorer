# PRD: Download ArXiv Papers About LLMs (with Date Range and Title Filters)

## Introduction/Overview

This feature describes a tool that allows users to download papers about LLMs from ArXiv. The tool uses the **ArXiv API** and supports optional constraints: a **date range** (by last updated date), **keywords** (searched in the **paper abstract**, not only in the title), **expressions that must appear in the paper title**, and a choice between fetching **all** matching papers or a **configurable limit**. Output is one JSONL file for metadata and one directory for PDFs. The tool **skips downloading a PDF** when that file is already on disk.

The goal is to make bulk discovery and download of LLM-related literature configurable and efficient without re-downloading existing files.

## Goals

1. Support filtering by **last updated date** (configurable date range) so users can restrict to recent or historical papers.
2. Support **keywords** searched in the **paper title and abstract**.
3. Support both **“fetch all”** (query until ArXiv returns no more results) and **configurable limit** (e.g. `total_to_fetch`) so users can either cap or exhaust the result set.
4. **Do not re-download** a paper's PDF a paper’s PDF if that PDF file is already present on disk.
5. Use a **config-driven design** with clear options for keywords, ArXiv_categories, date range, title expressions, output paths (JSONL, pdf_dir), and fetch limit or fetch-all.


## Functional Requirements

1. The system must use the **ArXiv API** (Atom feed) for all search and metadata; no other source is required.
2. The system must build the search query using **keywords** (searched in title and abstract, e.g. via `all:`) and **ArXiv_categories** (e.g. `cs.CL`, `cs.AI`).
3. The system must support an optional **date range** (start and end) applied to the **last updated date** of papers; only papers whose last updated date falls within this range shall be included.
4. The system must support optional **title expressions** (e.g. phrases that must appear in the paper title); behavior (all vs. any phrase) should be consistent with the existing keyword/query style and documented in config.
5. The system must support either **“fetch all”** (continue requesting pages until the API returns no more results) or a **configurable maximum number** of papers to fetch (e.g. `total_to_fetch`).
6. The system must **not download a PDF** if a file for that paper already exists in the configured `pdf_dir` (same naming as today, e.g. by `arxiv_id`).
7. The system must write **metadata** to the configured **JSONL** path and **PDFs** to the configured **pdf_dir**, preserving the current schema and file layout.
8. All options must be configurable via the **config file** (e.g. `fetch_from_arxiv.config.yaml`). CLI overrides may be added later and are out of scope for this PRD.

## Non-Goals (Out of Scope)

- **GUI**: No graphical interface; the tool is config-driven (optionally CLI later).
- **Other sources**: Only ArXiv is in scope; no other preprint or publication APIs.
- **Skip logic for metadata**: Skip-only-when-PDF-exists; the tool need not skip or deduplicate metadata writes when the PDF is already on disk.
- **CLI arguments**: Configuration is file-based only for this feature; adding CLI overrides is explicitly deferred.

## Design Considerations

- **Config file**: Use a YAML config (e.g. `fetch_from_arxiv.config.yaml`) with optional keys for date range, title expressions, and “fetch all” vs. limit.
- **Output layout**: One JSONL file for metadata; one directory for PDFs.
- **Naming**: Config keys should be clear and consistent with existing names (e.g. `ArXiv_categories`, `keywords`).

## Success Metrics

- Running the tool with a **date range** and **title filter** only includes papers whose last updated date is in range and whose title matches the configured expressions.
- Running the tool with **“fetch all”** retrieves every matching paper from the API (until no more results).
- When a PDF for a paper **already exists** in `pdf_dir`, that PDF is **not downloaded again**.
