# ==== llms.txt Adoption Census v2 - 100,000 domains, wildcard-aware, Excel proof output ====
# Run on Google Colab's free tier. Zero cost, no paid APIs.
!pip install -q tranco aiohttp nest_asyncio pandas openpyxl

import asyncio, aiohttp, nest_asyncio, pandas as pd, re, time
from tranco import Tranco
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

nest_asyncio.apply()

N_DOMAINS = 100000
CONCURRENCY = 150
TIMEOUT = 6

t = Tranco(cache=True, cache_dir='.tranco')
latest_list = t.list()
domains = latest_list.top(N_DOMAINS)
print(f"Loaded {len(domains)} real domains from Tranco.")

AI_BOTS = ["GPTBot", "ClaudeBot", "Claude-Web", "anthropic-ai", "PerplexityBot", "Google-Extended"]

def parse_robots(text):
    """Checks each named AI bot AND the wildcard User-agent: * block for a full disallow."""
    result = {bot: "not_mentioned" for bot in AI_BOTS}
    wildcard_blocks_all = False
    if not text:
        return result, wildcard_blocks_all
    blocks = re.split(r'(?im)^user-agent:\s*', text)
    for block in blocks[1:]:
        lines = block.splitlines()
        agent = lines[0].strip()
        disallow_all = any(re.match(r'(?i)disallow:\s*/\s*$', l.strip()) for l in lines[1:])
        if agent == "*":
            wildcard_blocks_all = disallow_all
        matched_bot = next((b for b in AI_BOTS if b.lower() == agent.lower()), None)
        if matched_bot:
            result[matched_bot] = "disallowed" if disallow_all else "allowed"
    return result, wildcard_blocks_all

async def check_domain(session, sem, domain, rank):
    async with sem:
        row = {"domain": domain, "rank": rank, "llms_txt_status": None, "robots_txt_status": None, "wildcard_blocks_all": False}
        row.update({f"{b}_directive": "not_mentioned" for b in AI_BOTS})
        for scheme in ["https", "http"]:
            try:
                async with session.get(f"{scheme}://{domain}/llms.txt", timeout=TIMEOUT, ssl=False) as r:
                    row["llms_txt_status"] = r.status
                    break
            except Exception:
                row["llms_txt_status"] = "error"
        for scheme in ["https", "http"]:
            try:
                async with session.get(f"{scheme}://{domain}/robots.txt", timeout=TIMEOUT, ssl=False) as r:
                    row["robots_txt_status"] = r.status
                    if r.status == 200:
                        text = await r.text(errors="ignore")
                        directives, wildcard = parse_robots(text)
                        row.update({f"{b}_directive": directives[b] for b in AI_BOTS})
                        row["wildcard_blocks_all"] = wildcard
                    break
            except Exception:
                row["robots_txt_status"] = "error"
        return row

async def main():
    sem = asyncio.Semaphore(CONCURRENCY)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY, ssl=False)
    async with aiohttp.ClientSession(connector=connector, headers={"User-Agent": "VimarshResearchBot/1.0 (+https://vimarshai.com)"}) as session:
        tasks = [check_domain(session, sem, d, i+1) for i, d in enumerate(domains)]
        results = []
        for i, coro in enumerate(asyncio.as_completed(tasks), 1):
            results.append(await coro)
            if i % 5000 == 0:
                print(f"{i}/{len(domains)} done...")
        return results

start = time.time()
results = asyncio.run(main())
print(f"Finished in {round((time.time()-start)/60, 1)} minutes")

df = pd.DataFrame(results)

# ---- Save raw proof data as a proper, publishable Excel file ----
EXCEL_PATH = "Vimarsh_llms_txt_Adoption_Census_100k_RAW_DATA.xlsx"
df.to_excel(EXCEL_PATH, index=False, sheet_name="Raw Data")

from openpyxl import load_workbook
wb = load_workbook(EXCEL_PATH)
ws = wb["Raw Data"]

HEADER_FONT = Font(name="Arial", bold=True, color="FFFFFF", size=10)
HEADER_FILL = PatternFill("solid", fgColor="1F3864")
BODY_FONT = Font(name="Arial", size=9)

for cell in ws[1]:
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal="center")
for row in ws.iter_rows(min_row=2):
    for cell in row:
        cell.font = BODY_FONT
widths = {"A": 28, "B": 8, "C": 14, "D": 14, "E": 16}
for col, w in widths.items():
    ws.column_dimensions[col].width = w
for i in range(6, ws.max_column + 1):
    ws.column_dimensions[get_column_letter(i)].width = 16
ws.freeze_panes = "A2"
ws.auto_filter.ref = ws.dimensions

# ---- Methodology / README sheet, so the published file is self-explaining ----
readme = wb.create_sheet("Methodology", 0)
readme["A1"] = "Vimarsh - llms.txt Adoption Census (100,000 real domains)"
readme["A1"].font = Font(name="Arial", bold=True, size=13)
notes = [
    "",
    "What this is: a real, reproducible check of whether real websites have published an llms.txt file",
    "(an optional file aimed at AI engines, similar in spirit to robots.txt) and how their robots.txt",
    "treats major AI crawlers (GPTBot, ClaudeBot, Claude-Web, anthropic-ai, PerplexityBot, Google-Extended).",
    "",
    "Domain list source: Tranco (tranco-list.eu) - a research-grade domain popularity list combining",
    "several ranking sources. Top 100,000 domains, snapshot taken on the date this file was generated.",
    "",
    "Method: one HTTP GET to /llms.txt and one to /robots.txt per domain. robots.txt parsed for named",
    "AI-bot user-agent blocks AND a blanket 'User-agent: *' disallow rule.",
    "",
    "What this can prove: whether the file exists and what robots.txt explicitly states.",
    "What this CANNOT prove: whether any AI engine actually reads or uses llms.txt, or whether a robots.txt",
    "directive is actually honored by a given crawler. A user-agent string in robots.txt is a declared",
    "policy, not observed crawler behavior.",
    "",
    "'not_mentioned' means that bot was not explicitly named in that domain's robots.txt - by robots.txt",
    "convention this generally means allowed by default, UNLESS 'wildcard_blocks_all' is True for that row,",
    "in which case a blanket rule blocks everything including unnamed bots.",
    "",
    "Raw data: see the 'Raw Data' sheet - one row per domain checked, fully auditable.",
]
for i, line in enumerate(notes, start=2):
    readme.cell(row=i, column=1, value=line).font = Font(name="Arial", size=10)
readme.column_dimensions["A"].width = 110

wb.save(EXCEL_PATH)
print(f"Saved Excel proof file: {EXCEL_PATH}")

# ---- Summary ----
total = len(df)
has_llms_txt = (df["llms_txt_status"] == 200).sum()
print(f"\n=== OVERALL SUMMARY ({total} domains) ===")
print(f"Have llms.txt: {has_llms_txt} ({round(100*has_llms_txt/total,1)}%)")
print(f"Blocked by wildcard 'User-agent: *': {df['wildcard_blocks_all'].sum()} ({round(100*df['wildcard_blocks_all'].sum()/total,1)}%)")
for bot in AI_BOTS:
    col = f"{bot}_directive"
    explicit = sum(df[col]=='disallowed') + sum(df[col]=='allowed')
    blocked_pct = round(100*sum(df[col]=='disallowed')/explicit, 1) if explicit else 0
    print(f"{bot}: disallowed={sum(df[col]=='disallowed')}, allowed={sum(df[col]=='allowed')}, not_mentioned={sum(df[col]=='not_mentioned')}  -> {blocked_pct}% blocked (of those who addressed it)")

print(f"\n=== LLMS.TXT ADOPTION BY RANK TIER ===")
tiers = [(1, 1000, "Top 1,000"), (1001, 10000, "1,001-10,000"), (10001, 100000, "10,001-100,000")]
for lo, hi, label in tiers:
    tier_df = df[(df["rank"] >= lo) & (df["rank"] <= hi)]
    if len(tier_df):
        pct = round(100 * (tier_df["llms_txt_status"]==200).sum() / len(tier_df), 1)
        print(f"{label}: {pct}% adoption (n={len(tier_df)})")

from google.colab import files
files.download(EXCEL_PATH)
