#!/usr/bin/env python3
"""
WGEA Screenshot Parser
----------------------
Uses Claude's vision to read each company screenshot from wgea_html/
and extract structured gender equality metrics.
Saves results to wgea_data.json.

Usage:
    python parse_wgea.py
"""

import anthropic
import base64
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SCREENSHOTS = {
    "Commonwealth Bank": Path("wgea_html/commonwealth_bank.png"),
    "Canva":             Path("wgea_html/canva.png"),
    "Rio Tinto":         Path("wgea_html/rio_tinto.png"),
    "BHP":               Path("wgea_html/bhp.png"),
    "ANZ":               Path("wgea_html/anz.png"),
    "Westpac":           Path("wgea_html/westpac.png"),
}

EXTRACT_PROMPT = """You are reading a screenshot from the WGEA (Workplace Gender Equality Agency)
Employer Data Explorer dashboard for a specific Australian company.

Extract the following data from the screenshot and return it as a valid JSON object.
If a value is not visible, use null.

Return ONLY the JSON object, nothing else:

{
  "company_name": "exact name shown in the dashboard",
  "abn": "the ABN number if shown",
  "total_employees": <integer>,
  "women_pct": <integer, % of total workforce that are women>,
  "men_pct": <integer, % of total workforce that are men>,
  "avg_total_remuneration_gpg_pct": <float, average total remuneration gender pay gap %>,
  "median_total_remuneration_gpg_pct": <float, median total remuneration gender pay gap %>,
  "avg_base_salary_gpg_pct": <float, average base salary gender pay gap %>,
  "upper_quartile_women_pct": <integer, % women in upper pay quartile>,
  "upper_middle_quartile_women_pct": <integer>,
  "lower_middle_quartile_women_pct": <integer>,
  "lower_quartile_women_pct": <integer>,
  "avg_total_remuneration": <integer, average total remuneration in dollars>,
  "has_equal_remuneration_policy": <true/false>,
  "conducted_gpg_analysis": <true/false>,
  "industry": "industry if visible",
  "employer_size": "size category if visible"
}"""


def image_to_base64(path: Path) -> str:
    return base64.standard_b64encode(path.read_bytes()).decode("utf-8")


def extract_from_screenshot(client: anthropic.Anthropic, label: str, path: Path) -> dict:
    print(f"  Extracting {label}…")
    img_b64 = image_to_base64(path)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_b64,
                        },
                    },
                    {"type": "text", "text": EXTRACT_PROMPT},
                ],
            }
        ],
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    data = json.loads(raw)
    data["label"] = label
    return data


def build_app_record(raw: dict, label: str) -> dict:
    """Convert raw WGEA metrics into the format app.py expects for company cards."""
    women_pct      = raw.get("women_pct") or 0
    upper_q_women  = raw.get("upper_quartile_women_pct") or 0
    gpg            = abs(raw.get("avg_total_remuneration_gpg_pct") or 0)
    has_policy     = raw.get("has_equal_remuneration_policy", False)
    conducted_gpg  = raw.get("conducted_gpg_analysis", False)

    # Derive 1-5 scores
    # Women in leadership: upper quartile women %  (50% = 3, 40% = 2, 60% = 4)
    women_leadership = round(min(5, max(1, upper_q_women / 12.5)), 1)

    # Gender equality: women % overall, policy, GPG analysis
    ge_base = women_pct / 20   # 50% = 2.5
    ge_bonus = (0.5 if has_policy else 0) + (0.5 if conducted_gpg else 0)
    gender_equality = round(min(5, max(1, ge_base + ge_bonus)), 1)

    # Pay equity: lower GPG = better score  (0% = 5, 30%+ = 1)
    pay_equity = round(min(5, max(1, 5 - (gpg / 8))), 1)

    # Overall rating
    rating = round((gender_equality + women_leadership + pay_equity) / 3, 1)

    total = raw.get("total_employees") or 0
    if total >= 50_000:
        emp_band = "50,000+ employees"
    elif total >= 10_000:
        emp_band = "10,000-50,000 employees"
    elif total >= 5_000:
        emp_band = "5,000-10,000 employees"
    elif total >= 1_000:
        emp_band = f"{total:,} employees"
    else:
        emp_band = f"{total:,} employees"

    highlights = []
    if women_pct:
        highlights.append(f"{women_pct}% women in workforce")
    if upper_q_women:
        highlights.append(f"{upper_q_women}% women in upper pay quartile")
    if gpg:
        highlights.append(f"{gpg:.1f}% average total remuneration gender pay gap")
    if has_policy:
        highlights.append("Has equal remuneration policy")
    if conducted_gpg:
        highlights.append("Conducted gender pay gap analysis")

    INDUSTRY_MAP = {
        "Commonwealth Bank": "Financial Services",
        "Canva":             "Technology",
        "Rio Tinto":         "Mining & Resources",
        "BHP":               "Mining & Resources",
        "ANZ":               "Financial Services",
        "Westpac":           "Financial Services",
    }

    return {
        "name":              label,
        "industry":          INDUSTRY_MAP.get(label, raw.get("industry", "Unknown")),
        "rating":            rating,
        "reviews":           raw.get("total_employees", 0) // 10,
        "gender_equality":   gender_equality,
        "women_leadership":  women_leadership,
        "pay_equity":        pay_equity,
        "location":          "Australia",
        "employees":         emp_band,
        "description":       f"WGEA data: {women_pct}% women, {gpg:.1f}% avg remuneration GPG.",
        "highlights":        highlights[:3],
        "wgea_data":         f"WGEA 2024-25 | {raw.get('company_name', label)}",
        # raw metrics for display
        "raw": {
            "women_pct":              raw.get("women_pct"),
            "men_pct":                raw.get("men_pct"),
            "total_employees":        raw.get("total_employees"),
            "avg_gpg_pct":            raw.get("avg_total_remuneration_gpg_pct"),
            "median_gpg_pct":         raw.get("median_total_remuneration_gpg_pct"),
            "upper_quartile_women":   raw.get("upper_quartile_women_pct"),
            "has_policy":             raw.get("has_equal_remuneration_policy"),
            "conducted_gpg_analysis": raw.get("conducted_gpg_analysis"),
        },
    }


def main():
    client = anthropic.Anthropic()
    all_raw  = {}
    app_data = {}

    for label, path in SCREENSHOTS.items():
        if not path.exists():
            print(f"  ⚠  {path} not found — skipping {label}")
            continue
        try:
            raw = extract_from_screenshot(client, label, path)
            all_raw[label]  = raw
            app_data[label] = build_app_record(raw, label)
            print(f"    → women={raw.get('women_pct')}%  GPG={raw.get('avg_total_remuneration_gpg_pct')}%  employees={raw.get('total_employees')}")
        except Exception as e:
            print(f"  ✗ {label}: {e}")

    # Save both raw and app-ready data
    Path("wgea_data.json").write_text(
        json.dumps({"raw": all_raw, "companies": app_data}, indent=2),
        encoding="utf-8",
    )
    print(f"\n✓ Saved wgea_data.json ({len(app_data)} companies)")


if __name__ == "__main__":
    main()
