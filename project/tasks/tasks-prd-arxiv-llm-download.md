---
title: Tasks
---

## ArXiv LLM downloader

- [ ] 1.0 Align config schema with PRD (date range, title expressions, fetch-all vs limit, output paths)
  - [v] 1.1 Output paths (out_jsonl, pdf_dir) in config
  - [ ] 1.2 Add date range (start/end) to config schema
  - [v] 1.3 Add search expressions to config schema
  - [ ] 1.4 Add fetch-all vs limit option to config schema

- [ ] 2.0 Implement ArXiv query construction (keywords + categories) and request paging
  - [v] 2.1 Query from keywords + ArXiv_categories (build_query, all:)
  - [v] 2.2 Request paging (start, batch_size, loop in fetch_and_process_papers)

- [ ] 3.0 Add result post-filters (last-updated date range; title expressions)
  - [ ] 3.1 Filter results by last-updated date range
  - [ ] 3.2 Filter results by title expressions

- [ ] 4.0 Implement "fetch all" mode and configurable maximum fetch limit
  - [v] 4.1 Configurable maximum (total_to_fetch)
  - [ ] 4.2 "Fetch all" mode (continue until API returns no more results)

- [v] 5.0 Ensure PDF download skip behavior when file already exists
  - [v] 5.1 Skip download when PDF path already exists (download_pdfs_for_records)
  - [v] 5.2 Retain naming/layout (arxiv_id → safe_name.pdf in pdf_dir)

- [ ] 6.0 Validate outputs (JSONL metadata + pdf_dir) and preserve existing schema/layout
  - [v] 6.1 JSONL metadata with current schema (arxiv_id, title, summary, authors, etc.)
  - [v] 6.2 PDFs in pdf_dir with current layout
  - [ ] 6.3 Add explicit validation (or cover in tests) per PRD requirements

- [ ] 7.0 Add automated tests and minimal documentation updates for the new config options
  - [ ] 7.1 Automated tests
  - [ ] 7.2 Documentation updates for new config options

## Relevant Files

- `tools/fetch_from_arxiv.py` — main tool
- `tools/fetch_from_arxiv.config.yaml` — config
- `project/documents/prds/prd-arxiv-llm-download.md` — PRD
