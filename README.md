# Vimarsh llms.txt Adoption Census

A real, reproducible measurement of AI-crawler readiness across 100,000 real
websites — run as part of Vimarsh's weekly Founder Outreach research series.

**No figure in this repository is estimated, guessed, or invented.** Every
number comes from a real HTTP check against real domains, run on
2026-11-15.

## What this measures

1. What fraction of real websites have published an `llms.txt` file (an
   optional file aimed at AI engines, similar in spirit to `robots.txt`).
2. How each site's `robots.txt` treats six real AI-crawler user-agents:
   `GPTBot`, `ClaudeBot`, `Claude-Web`, `anthropic-ai`, `PerplexityBot`,
   `Google-Extended`.
3. Whether adoption/blocking differs by site popularity tier.

## Method

- **Domain list:** [Tranco](https://tranco-list.eu/) — a research-grade
  domain popularity list combining several ranking sources. Top 100,000
  domains, snapshot taken 2026-11-15.
- **Checks:** one HTTP GET to `/llms.txt` and one to `/robots.txt` per
  domain. `robots.txt` parsed for each named AI-bot user-agent block AND a
  blanket `User-agent: *` disallow rule.
- **Concurrency:** 150 simultaneous requests, 6-second timeout per request.
  Each domain receives at most 2 requests total — no site is hit
  repeatedly.
- **Runtime:** 41.9 minutes for the full 100,000-domain run, on Google
  Colab's free tier (zero cost, no paid APIs).

Full script: [`census_script.py`](census_script.py)

## Results (2026-11-15, n=100,000)

| Metric | Value |
|---|---|
| Have `llms.txt` | 20,845 / 100,000 (20.8%) |
| Blocked by blanket wildcard rule | 2,234 / 100,000 (2.2%) |

**Bot-level blocking, among domains that explicitly addressed that bot:**

| Bot | Disallowed | Allowed | % Blocked (of those who addressed it) |
|---|---|---|---|
| GPTBot | 7,197 | 4,333 | 62.4% |
| ClaudeBot | 6,403 | 4,120 | 60.8% |
| Claude-Web | 5,337 | 1,478 | 78.3% |
| anthropic-ai | 5,786 | 2,159 | 72.8% |
| PerplexityBot | 1,869 | 3,603 | 34.2% |
| Google-Extended | 6,010 | 3,419 | 63.7% |

**Adoption by site popularity tier:**

| Rank tier | `llms.txt` adoption |
|---|---|
| Top 1,000 | 24.7% |
| 1,001–10,000 | 19.7% |
| 10,001–100,000 | 20.9% |

A smaller 10,000-domain pilot run (same method, same day) found 20.1%
overall adoption — closely matching the full 100,000-domain result (20.8%),
which is a real cross-validation signal that this measurement is stable,
not noise.

## What this can and cannot prove

**Can show:** whether a file exists, and what a domain's `robots.txt`
explicitly declares.

**Cannot show:** whether any AI engine actually reads or uses `llms.txt`,
or whether a declared `robots.txt` directive is actually honored by a given
crawler. A `robots.txt` entry is a declared policy, not observed crawler
behavior — a "blocked" bot may still reach content another way, and an
"allowed" one may never crawl it at all. User-agent strings can also be
spoofed by third parties, though that does not affect what was measured
here (declared policy, not traffic logs).

The 20.8% adoption figure is roughly double a previously published ~10%
estimate from another source/domain list — this discrepancy is reported
honestly; we do not know whether it reflects a different domain list,
genuine adoption growth over time, or a methodology difference, and make no
claim either way.

The most notable finding — that Anthropic's three distinct bot identities
(`ClaudeBot`, `Claude-Web`, `anthropic-ai`) are blocked at meaningfully
different rates (60.8% vs. 78.3% vs. 72.8%) from each other — is reported
as an observation, not an explained cause. A plausible but unconfirmed
hypothesis: site owners may be copying boilerplate "block AI" robots.txt
snippets without distinguishing between these three related but distinct
user-agents.

## Files

- `census_script.py` — the full, runnable Python script (Google Colab,
  free tier, zero API cost)
- `Vimarsh_llms_txt_Adoption_Census_100k_RAW_DATA.xlsx` — raw, per-domain
  results for all 100,000 domains checked, fully auditable (includes a
  Methodology sheet)

## About

Published by [Vimarsh](https://vimarshai.com) — AI visibility measurement
for ChatGPT, Gemini, Perplexity, and Claude. Built by Free Mind Consultancy.

Part of a weekly, zero-cost research series — one real experiment every
Sunday, results published openly regardless of outcome.
