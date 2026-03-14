#!/usr/bin/env python3
"""
WGEA Employer Data Scraper
--------------------------
Visits https://www.wgea.gov.au/Data-Explorer/Employer, types each
company name into the "Employer Name (ABN)" combobox to filter it,
waits for Tableau to finish rendering, then saves HTML + screenshot
and extracts key metrics to wgea_data.json.

Usage:
    python scraper.py              # scrapes TARGET_COMPANIES
    python scraper.py --headless   # no browser window
"""

import asyncio
import json
import re
import sys
from pathlib import Path

from playwright.async_api import async_playwright, Page, Frame, TimeoutError as PWTimeout

# ── Config ────────────────────────────────────────────────────────────────────
WGEA_URL = "https://www.wgea.gov.au/Data-Explorer/Employer"
OUT_DIR  = Path("wgea_html")

# (display_label, search_term, match_substring)
TARGET_COMPANIES = [
    ("Commonwealth Bank", "Commonwealth Bank Of Australia",         "Commonwealth Bank Of Australia"),
    ("Canva",             "Canva Pty",                             "Canva Pty Ltd"),
    ("Rio Tinto",         "Rio Tinto Services",                    "Rio Tinto Services Limited"),
    ("BHP",               "BHP Group",                             "BHP Group"),
    ("ANZ",               "Australia and New Zealand Banking Group","Australia and New Zealand Banking Group"),
    ("Westpac",           "Westpac Banking Corporation",           "Westpac Banking Corporation"),
]

TABLEAU_INIT_WAIT_MS  = 15_000
FILTER_CHANGE_WAIT_MS =  9_000   # conservative wait after selection
SEARCH_WAIT_MS        =  2_000
GLASS_TIMEOUT_MS      = 25_000   # wait for Tableau overlay to clear


# ── Helpers ───────────────────────────────────────────────────────────────────
def safe_filename(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


async def find_tableau_frame(page: Page) -> Frame | None:
    for frame in page.frames:
        if "public.tableau.com" in frame.url:
            return frame
    return None


async def wait_for_glass_clear(ctx, timeout_ms: int = GLASS_TIMEOUT_MS):
    """Wait until Tableau's loading overlay is gone."""
    try:
        await ctx.wait_for_selector(
            ".tab-glass.clear-glass",
            state="hidden",
            timeout=timeout_ms,
        )
    except PWTimeout:
        pass  # overlay may have already gone or never appeared


async def find_employer_combobox(ctx):
    filters = await ctx.query_selector_all(".CategoricalFilter")
    for f in filters:
        h3 = await f.query_selector('h3[title="Employer name (ABN)"]')
        if h3:
            return await f.query_selector('span[role="combobox"]')
    return None


async def select_company(page: Page, ctx, search_term: str, match_text: str) -> bool:
    """Type search_term in the combobox, then click the matching option."""
    # Wait for any existing overlay to clear before interacting
    await wait_for_glass_clear(ctx)

    combobox = await find_employer_combobox(ctx)
    if not combobox:
        print("  ✗ Combobox not found")
        return False

    await combobox.click()
    await ctx.wait_for_timeout(600)

    # Clear existing text then type
    await page.keyboard.press("Control+a")
    await page.keyboard.press("Backspace")
    await ctx.wait_for_timeout(200)
    await page.keyboard.type(search_term, delay=60)
    await ctx.wait_for_timeout(SEARCH_WAIT_MS)

    # Find matching option
    opts = await ctx.query_selector_all('[role="option"]')
    target = None
    for opt in opts:
        text = (await opt.text_content() or "").strip()
        if match_text.lower() in text.lower():
            target = opt
            print(f"  → matched: {text!r}")
            break

    if not target:
        # Print what IS available so we can debug
        print(f"  ✗ No match for {match_text!r}. Available:")
        for opt in opts[:5]:
            print(f"      {(await opt.text_content() or '').strip()!r}")
        await page.keyboard.press("Escape")
        return False

    await target.click()
    # Wait for Tableau to re-render
    await ctx.wait_for_timeout(FILTER_CHANGE_WAIT_MS)
    await wait_for_glass_clear(ctx)
    return True


# ── Data extraction ───────────────────────────────────────────────────────────
async def extract_metrics(ctx, label: str) -> dict:
    """
    Pull key gender metrics out of the rendered Tableau DOM.
    All visible numbers are stored as text nodes in the frame.
    """
    data = {"company": label}

    # Extract all visible text from the dashboard area
    raw = await ctx.evaluate("""() => {
        const texts = [];
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null
        );
        let node;
        while ((node = walker.nextNode())) {
            const t = node.textContent.trim();
            if (t.length > 0 && t.length < 200) texts.push(t);
        }
        return texts;
    }""")

    # Join all text for regex parsing
    full_text = " ".join(raw)

    # % women/men in total workforce
    women_pct = re.search(r"(\d+)%\s*Women", full_text, re.I)
    men_pct   = re.search(r"(\d+)%\s*Men",   full_text, re.I)
    if women_pct:
        data["women_pct"] = int(women_pct.group(1))
    if men_pct:
        data["men_pct"] = int(men_pct.group(1))

    # Total employees
    emp_match = re.search(r"Total employees\s*([\d,]+)", full_text, re.I)
    if emp_match:
        data["total_employees"] = int(emp_match.group(1).replace(",", ""))

    # Gender pay gap (average total remuneration GPG %)
    gpg_matches = re.findall(r"(-?\d+\.?\d*)%", full_text)
    if gpg_matches:
        # The first prominent % near a GPG label
        data["raw_percentages"] = gpg_matches[:10]

    # Upper quartile women % (proxy for women in leadership)
    uq = re.search(r"Upper quartile\D{0,20}(\d+)%", full_text, re.I)
    if uq:
        data["upper_quartile_women_pct"] = int(uq.group(1))

    # Equal remuneration policy
    policy_yes = re.search(r"Yes\s+(\d+)%", full_text, re.I)
    if policy_yes:
        data["equal_remuneration_policy_yes_pct"] = int(policy_yes.group(1))

    return data


# ── Core scraper ──────────────────────────────────────────────────────────────
async def scrape(headless: bool = False):
    OUT_DIR.mkdir(exist_ok=True)
    all_data = {}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless, slow_mo=100)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        print(f"→ Loading {WGEA_URL}")
        await page.goto(WGEA_URL, wait_until="domcontentloaded", timeout=90_000)
        print(f"→ Waiting {TABLEAU_INIT_WAIT_MS // 1000}s for Tableau to initialise…")
        await page.wait_for_timeout(TABLEAU_INIT_WAIT_MS)

        tf = await find_tableau_frame(page)
        ctx = tf or page
        print(f"→ {'Tableau frame' if tf else 'Main page'} context ready\n")

        await page.screenshot(path=str(OUT_DIR / "_initial.png"), full_page=False)

        for i, (label, search_term, match_text) in enumerate(TARGET_COMPANIES, 1):
            print(f"[{i}/{len(TARGET_COMPANIES)}] {label}")

            ok = await select_company(page, ctx, search_term, match_text)
            if not ok:
                print(f"  ⚠  Skipping {label}")
                continue

            # Extract metrics from DOM
            metrics = await extract_metrics(ctx, label)
            all_data[label] = metrics
            print(f"  → metrics: {metrics}")

            # Save HTML
            html  = await page.content()
            fname = safe_filename(label)
            (OUT_DIR / f"{fname}.html").write_text(html, encoding="utf-8")

            # Save screenshot
            await page.screenshot(path=str(OUT_DIR / f"{fname}.png"), full_page=False)
            print(f"  ✓ saved {fname}.html + {fname}.png")

        # Write all extracted data to JSON
        json_path = Path("wgea_data.json")
        json_path.write_text(json.dumps(all_data, indent=2), encoding="utf-8")
        print(f"\n✓ Metrics saved to {json_path}")
        print(f"✓ HTML + screenshots in ./{OUT_DIR}/")

        await browser.close()


if __name__ == "__main__":
    headless = "--headless" in sys.argv
    asyncio.run(scrape(headless=headless))
