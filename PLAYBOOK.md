# Content quality field playbook

## Use case 1: Tech marketing content with an unearned ROI claim

The sentence “Our agentic platform improves output by 40%” triggers **Claim Sentinel** because it contains a quantified claim with no local evidence. Before publishing, ask for sample size, baseline, measured outcome, dates, methodology and the source. If those cannot be produced, remove or qualify the claim. An attribution phrase alone is not conclusive evidence.

## Use case 2: AI adoption theater

“The autonomous system transforms every workflow” is a promise, not an operating model. **AI Theater Detector** checks for missing operational vocabulary. The editor asks: What triggers the agent? What is its tool access? Who approves changes? Where is the audit trail? What is the rollback? What human handles exceptions? How are quality and cost measured? Its heuristic cannot establish that every answer exists.

## Use case 3: Documentation debt in GitHub

On every pull request, scan `docs/`. Triage temporal claims, dead placeholder citations, content structure and wordy repetition. Commit the cleaned Markdown alongside the issue/PR review; preserve sources separately. This keeps CI as a guardrail, not as a substitute for subject-matter review.

## Triage rules

| Finding | Default response | Escalation |
|---|---|---|
| Unsourced absolute or metric | Ask for a traceable primary source | Technical reviewer / PMM owns the claim |
| Vague AI benefit | Require a named workflow and operating boundary | Product owner validates |
| Temporal language | Add an explicit as-of date and review owner | Re-review on significant product change |
| Heading/image/link issue | Fix Markdown or document a reasonable exception | Editorial review |
| Repeat paragraph | Remove, combine or retain with purpose | Editorial judgment |

## Local workflow

```bash
# Install once in the repo
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .

# Inspect without blocking publication while introducing rules
wkq scan docs --fail-on none --out artifacts/content-review.txt

# Enforce warnings once the team agrees on rule ownership
wkq scan docs --ledger claims.json --fail-on warning

# Export machine-readable review findings
wkq scan docs --format json --out artifacts/content-review.json --fail-on none
```

`docs` and `claims.json` above are example locations for your own documentation repository, not folders pre-created by this demo. `--out` creates its parent folder.

## Integrating with Zensical, MkDocs or Docusaurus

Put the scan before your build/deploy step in GitHub Actions, pointed at the actual Markdown source directory. The scan does not build or alter the site. It is independent of your site generator. Copy the provided workflow as a template and adjust source paths, artifact handling and PR enforcement.

## Quality measurement without score theater

Track warning count per 1,000 words, verified claim coverage from editorial audits, average age of time-sensitive pages, editorial turnaround, reopened accuracy issues and post-publication corrections. Compare across the same content cohort and policy version. A lower warning count is not automatically higher quality: evidence review is the control metric.

## Boundaries

This v0.1 operates on Markdown/MDX *text*, not rendered pages. Regex-based sentence detection has edge cases with abbreviations, decimals and tables. URLs are not fetched or validated. Paragraph overlap is a clue, not a plagiarism finding. Extend it with configuration and tests before making hard publication policy decisions.
