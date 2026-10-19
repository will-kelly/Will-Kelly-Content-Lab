# Will Kelly Content Lab

**A quality gate for content that has to survive an editor, an engineer, and a skeptical buyer.**

This is a dependency-light, executable Python toolkit for Markdown and docs-as-code pipelines. It favors auditability and human decisions over synthetic content scores. It does **not** detect whether AI wrote something, fact-check web claims, measure real accessibility, or pretend that keyword matching is editorial judgment.

## Install and run

Requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
wkq scan examples/article.md --ledger examples/claims.json --fail-on none
wkq scan examples --format json --out report.json --fail-on none
wkq scan examples --format sarif --out quality.sarif --fail-on none
wkq ledger examples/claims.json
```

For a first integration against your own site, copy this repo or install it in your site's CI, then use `wkq scan docs --fail-on warning`. Exit codes: **0** pass, **1** invalid input/configuration, **2** quality gate triggered. Use `--fail-on info` for stricter checks and `--fail-on none` for report-only adoption.

## The seven instruments

| Instrument | What it spots | What a human must decide |
|---|---|---|
| **Claim Sentinel** | Numerical, absolute and superlative claims without local attribution or verified claim-ledger match | Whether the evidence really supports the exact assertion |
| **Jargon Tax** | Vague marketing language and buzzwords | When a term is a legitimate technical term |
| **AI Theater Detector** | AI automation, productivity and governance promises without *document-level* operational vocabulary | Whether control descriptions are specific and sufficient |
| **Reader First** | Missing H1, heading skips, dense paragraphs, weak links, empty alt text | Audience comprehension, hierarchy, and decorative-image exceptions |
| **Decay Radar** | Time-relative claims and old years | What has changed and whether historical details remain valid |
| **Evidence Trail** | Placeholder and tracking-laden URLs | Source authority, credibility and whether a primary source exists |
| **Echo Chamber** | Highly overlapping paragraph trigrams | Whether repetition is intentional emphasis |

These names are editorial provocations, not AI classifiers. The theater check is intentionally coarse, based on three or more occurrences of operational terms in the **whole document**, and can miss weak implementation descriptions. Claim Sentinel recognizes some local attribution patterns but does not validate the linked content. Code fences, inline code and top YAML-style frontmatter are masked in most language checks; the current parser is not a full MDX AST.

## Publishing model

1. **Draft:** run `wkq scan docs --fail-on none`. Capture findings, especially uncertain assertions.
2. **Substantiate:** maintain a JSON claim ledger with stable IDs, exact `claim` fragments, an owner, evidence URL, date and review status. Only `verified` ledger entries with a URL suppress exact-fragment matching alerts. Treat the ledger as accountability, not automatic fact verification.
3. **Edit:** remove generic promises, add evidence and explain operational owners, exceptions, evaluations and rollback paths.
4. **Review:** assign a human technical reviewer and an editorial reviewer. A clean scan is not publication approval.
5. **Gate:** set `--fail-on warning` in CI. Start with report-only if retrofitting a large docs repository.
6. **Maintain:** rerun on pull requests and schedule content-review dates for time-sensitive claims separately.

## Design constraints and future extensions

- **Offline by default:** no content sent to external models, no network fetches, no third-party runtime dependency.
- **Deterministic:** same source + same `--as-of` yields same findings. Pass `--as-of 2026-10-19` for reproducibility.
- **Reviewable outputs:** JSON for dashboards, SARIF for code-scanning pipelines, text for writers. The included GitHub Action uploads SARIF as an artifact; it does not automatically publish to GitHub Code Scanning.
- **No false confidence:** no opaque numerical quality grade. No plagiarism/AI-origin claim. No automated validation of evidence URLs.
- **Next version:** frontmatter freshness policy, canonical source comparison, internal broken links, content reuse graph, configurable editorial rules and agent-generated change provenance.

## A Will Kelly-specific editorial doctrine

**Human reader first. Search engines second. Answer engines third.** Good content is not merely fluent. It states who owns the workflow, what changed, what measurement proves it, how it fails, and how a reader can verify the result. A model may generate the draft; accountable humans must own the claims. This toolkit is the first checkpoint in that process, not a substitute for it.

See [PLAYBOOK.md](PLAYBOOK.md) for operational rollout and a practical docs-as-code workflow.
