import streamlit as st
import os
import csv
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─── WGEA data ────────────────────────────────────────────────────────────────
def load_wgea_data() -> dict:
    path = Path("wgea_data.json")
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())["companies"]
    except Exception:
        return {}

def wgea_to_card(label: str, d: dict) -> dict:
    """Convert raw WGEA metrics to the company card schema."""
    gpg        = abs(d.get("avg_total_remuneration_gpg_pct") or 0)
    women_pct  = d.get("women_pct") or 0
    upper_q    = d.get("upper_quartile_women_pct") or 0
    has_policy = d.get("has_equal_remuneration_policy", False)
    conducted  = d.get("conducted_gpg_analysis", False)

    # 1-5 scores
    gender_equality  = round(min(5, max(1, women_pct / 20 + (0.5 if has_policy else 0) + (0.5 if conducted else 0))), 1)
    women_leadership = round(min(5, max(1, upper_q / 12.5)), 1)
    pay_equity       = round(min(5, max(1, 5 - gpg / 8)), 1)
    rating           = round((gender_equality + women_leadership + pay_equity) / 3, 1)

    total = d.get("total_employees") or 0
    highlights = []
    if women_pct:   highlights.append(f"{women_pct}% women in workforce")
    if upper_q:     highlights.append(f"{upper_q}% women in upper pay quartile")
    if gpg:         highlights.append(f"{gpg:.1f}% avg remuneration gender pay gap")

    return {
        "name":             label,
        "industry":         d.get("industry", ""),
        "rating":           rating,
        "reviews":          max(1, total // 10),
        "gender_equality":  gender_equality,
        "women_leadership": women_leadership,
        "pay_equity":       pay_equity,
        "location":         d.get("location", "Australia"),
        "employees":        f"{total:,} employees" if total else "",
        "description":      f"{women_pct}% women overall · {upper_q}% in upper pay quartile · {gpg:.1f}% gender pay gap",
        "highlights":       highlights[:3],
        "wgea_data":        f"WGEA 2024–25 · ABN {d.get('abn', '')}",
        "_raw":             d,
    }

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WomenInTech — Empowering Careers",
    page_icon="👩‍💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown(
        """
<style>
/* ── Reset & base ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="collapsedControl"] { visibility: visible; }

/* ── Brand bar layout ── */
.brand-col { display: flex; align-items: center; }
.main .block-container {
    padding: 0 2rem 2rem;
    max-width: 1200px;
}

/* ── Brand nav ── */
.brand-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 18px 0 8px;
    border-bottom: 1px solid #E5E7EB;
    margin-bottom: 0;
}
.brand-icon {
    background: #7C3AED;
    width: 42px; height: 42px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
    flex-shrink: 0;
}
.brand-name {
    font-size: 18px;
    font-weight: 700;
    color: #111827;
    line-height: 1.2;
}
.brand-tagline {
    font-size: 12px;
    color: #6B7280;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: transparent;
    border-bottom: 2px solid #E5E7EB;
    padding: 0;
    margin-bottom: 24px;
}
.stTabs [data-baseweb="tab"] {
    height: 48px;
    padding: 0 24px;
    background: transparent !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
    color: #6B7280;
    font-weight: 500;
    font-size: 15px;
    border-radius: 0 !important;
}
.stTabs [data-baseweb="tab"]:hover { color: #7C3AED; }
.stTabs [aria-selected="true"] {
    color: #7C3AED !important;
    border-bottom: 3px solid #7C3AED !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ── Page headings ── */
.page-heading { font-size: 26px; font-weight: 700; color: #111827; margin-bottom: 4px; }
.page-subtitle { font-size: 15px; color: #6B7280; margin-bottom: 20px; }

/* ── Search row ── */
.stTextInput input {
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    box-shadow: none !important;
}
.stTextInput input:focus {
    border-color: #7C3AED !important;
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.1) !important;
}
.stSelectbox > div > div {
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
}
.stButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    border: none !important;
}
.stButton > button[kind="primary"], .stButton > button {
    background: #7C3AED !important;
    color: white !important;
    padding: 10px 24px !important;
}
.stButton > button:hover { background: #6D28D9 !important; }

/* ── Cards ── */
.card {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    transition: box-shadow 0.2s;
}
.card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }

.card-header { display: flex; align-items: flex-start; gap: 14px; margin-bottom: 12px; }
.company-logo {
    width: 48px; height: 48px;
    background: linear-gradient(135deg, #7C3AED22, #7C3AED44);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
    flex-shrink: 0;
}
.card-title { font-size: 16px; font-weight: 600; color: #111827; }
.card-subtitle { font-size: 13px; color: #6B7280; margin-top: 2px; }

.rating-row { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.stars { color: #F59E0B; font-size: 16px; letter-spacing: 1px; }
.review-count { font-size: 13px; color: #6B7280; }

.metrics { border-top: 1px solid #F3F4F6; padding-top: 12px; margin-bottom: 12px; }
.metric-row {
    display: flex; justify-content: space-between;
    padding: 4px 0;
    font-size: 13px;
}
.metric-label { color: #6B7280; }
.metric-value { font-weight: 600; color: #111827; }

.card-footer {
    display: flex; gap: 16px;
    font-size: 13px; color: #6B7280;
    border-top: 1px solid #F3F4F6;
    padding-top: 12px;
    flex-wrap: wrap;
}

/* ── Job cards ── */
.job-salary {
    font-size: 15px;
    font-weight: 700;
    color: #7C3AED;
    white-space: nowrap;
}
.equality-score {
    font-size: 13px;
    color: #6B7280;
    text-align: right;
}
.job-description { font-size: 13px; color: #374151; margin: 10px 0; line-height: 1.5; }
.job-meta { display: flex; gap: 14px; font-size: 12px; color: #6B7280; flex-wrap: wrap; margin-bottom: 10px; }

/* ── Tags ── */
.tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tag {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
}
.tag-blue   { background: #EFF6FF; color: #1D4ED8; }
.tag-pink   { background: #FDF2F8; color: #9D174D; }
.tag-green  { background: #F0FDF4; color: #166534; }
.tag-purple { background: #F5F3FF; color: #6D28D9; }
.tag-orange { background: #FFF7ED; color: #C2410C; }
.tag-gray   { background: #F3F4F6; color: #374151; }

/* ── Mentor cards ── */
.mentor-photo {
    width: 72px; height: 72px;
    border-radius: 50%;
    background: linear-gradient(135deg, #7C3AED44, #EC489966);
    display: flex; align-items: center; justify-content: center;
    font-size: 32px;
    margin: 0 auto 12px;
}
.mentor-card { text-align: center; }
.mentor-bio { font-size: 13px; color: #374151; line-height: 1.5; text-align: left; margin: 12px 0; }
.mentor-detail { font-size: 12px; color: #6B7280; display: flex; align-items: center; gap: 6px; margin: 4px 0; }

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #9CA3AF;
}
.empty-state .icon { font-size: 48px; margin-bottom: 12px; }
.empty-state p { font-size: 15px; margin: 0; }

/* ── Highlight box ── */
.fit-reason {
    background: #F5F3FF;
    border-left: 3px solid #7C3AED;
    padding: 8px 12px;
    font-size: 13px;
    color: #4C1D95;
    border-radius: 0 6px 6px 0;
    margin-top: 10px;
}

/* ── WGEA badge ── */
.wgea-badge {
    display: inline-block;
    background: #ECFDF5;
    color: #065F46;
    border: 1px solid #A7F3D0;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}

/* ── Coming soon ── */
.coming-soon {
    text-align: center;
    padding: 80px 20px;
}
.coming-soon .cs-icon { font-size: 64px; margin-bottom: 16px; }
.coming-soon h2 { color: #111827; font-size: 24px; margin-bottom: 8px; }
.coming-soon p { color: #6B7280; font-size: 15px; max-width: 400px; margin: 0 auto; }

/* ── Sidebar ── */
.sidebar-section { font-weight: 600; font-size: 14px; color: #111827; margin-bottom: 8px; }

/* ── Survey hover overlay ── */
.card-wrap {
    position: relative;
    margin-bottom: 16px;
}
.card-wrap .card {
    margin-bottom: 0;
}
.survey-overlay {
    position: absolute;
    inset: 0;
    background: rgba(124, 58, 237, 0.97);
    border-radius: 12px;
    color: white;
    padding: 16px;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s ease;
    overflow-y: auto;
    z-index: 10;
}
.card-wrap:hover .survey-overlay {
    opacity: 1;
    pointer-events: auto;
}
.survey-overlay h4 {
    font-size: 13px;
    font-weight: 700;
    margin: 0 0 10px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #EDE9FE;
}
.survey-overlay .s-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 5px 0;
    border-bottom: 1px solid rgba(255,255,255,0.12);
    font-size: 12px;
}
.survey-overlay .s-label { color: #DDD6FE; }
.survey-overlay .s-val {
    font-weight: 700;
    font-size: 13px;
    color: white;
}
.survey-overlay .s-bar-bg {
    flex: 1;
    height: 4px;
    background: rgba(255,255,255,0.2);
    border-radius: 2px;
    margin: 0 8px;
}
.survey-overlay .s-bar-fill {
    height: 100%;
    border-radius: 2px;
    background: #A78BFA;
}
.survey-overlay .s-no-data {
    text-align: center;
    padding: 20px 0;
    color: #DDD6FE;
    font-size: 13px;
}
.survey-overlay .s-count {
    font-size: 11px;
    color: #C4B5FD;
    margin-bottom: 10px;
}
.survey-overlay .s-comment {
    font-size: 11px;
    color: #EDE9FE;
    font-style: italic;
    border-top: 1px solid rgba(255,255,255,0.15);
    padding-top: 8px;
    margin-top: 6px;
    line-height: 1.4;
}
</style>
""",
        unsafe_allow_html=True,
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────
INDUSTRY_OPTIONS = [
    "All Industries", "Technology", "Finance", "Healthcare",
    "Government", "Clean Energy", "Data Analytics", "Cloud Computing",
    "Financial Technology", "Healthcare Technology", "Education", "Consulting",
]
LEVEL_OPTIONS = ["All Levels", "Entry", "Mid-level", "Senior", "Executive"]
TYPE_OPTIONS  = ["All Types", "Full-time", "Part-time", "Contract", "Internship"]
PRIORITY_OPTIONS = [
    "Pay equity", "Flexible / async hours", "Strong parental leave",
    "Women in leadership", "Mentorship programs", "Return-to-work support",
    "Salary transparency",
]

TAG_COLOURS = {
    "Remote": "tag-blue", "Hybrid": "tag-blue",
    "Women-friendly": "tag-pink", "Parental leave": "tag-pink",
    "Equal pay": "tag-green", "Salary transparent": "tag-green",
    "Flexible hours": "tag-orange", "Return-to-work": "tag-orange",
    "Mentorship": "tag-purple", "Diverse team": "tag-purple",
    "Women in leadership": "tag-pink",
}

EMOJI_MAP = {
    "Technology": "💻", "Finance": "💰", "Healthcare": "🏥",
    "Government": "🏛️", "Clean Energy": "🌱", "Data Analytics": "📊",
    "Cloud Computing": "☁️", "Financial Technology": "💳",
    "Healthcare Technology": "⚕️", "Education": "🎓",
    "Consulting": "🤝",
}

def tag_html(text: str) -> str:
    cls = TAG_COLOURS.get(text, "tag-gray")
    return f'<span class="tag {cls}">{text}</span>'

def stars_html(rating: float) -> str:
    full = min(int(round(rating)), 5)
    empty = 5 - full
    return "★" * full + "☆" * empty

def fmt_salary(job: dict) -> str:
    lo = job.get("salary_min")
    hi = job.get("salary_max")
    cur = job.get("salary_currency", "")
    if not lo and not hi:
        return "Salary not disclosed"
    sym = {"AUD": "A$", "USD": "$", "GBP": "£", "EUR": "€"}.get(cur, cur + " " if cur else "")
    def fmt(n):
        return f"{sym}{int(n)//1000}k" if n else ""
    return f"{fmt(lo)} – {fmt(hi)}" if lo and hi else fmt(lo) or fmt(hi)

def posted_label(days: int | None) -> str:
    if days is None:
        return "Recently"
    if days == 0:
        return "Today"
    if days == 1:
        return "1 day ago"
    return f"{days} days ago"



@st.cache_data(ttl=60)
def load_survey_data() -> dict:
    """Return {company_lower: [rows]} from survey_data.csv."""
    path = Path("survey_data.csv")
    if not path.exists():
        return {}
    result: dict = {}
    try:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = row.get("company", "").strip().lower()
                if key:
                    result.setdefault(key, []).append(row)
    except Exception:
        pass
    return result


def _survey_rows_for(company_name: str, survey_map: dict) -> list:
    """Fuzzy-match company name against survey keys (substring match)."""
    name_l = company_name.strip().lower()
    rows = survey_map.get(name_l, [])
    if not rows:
        # also try if any key is a substring of the card name or vice-versa
        for key, keyed_rows in survey_map.items():
            if key in name_l or name_l in key:
                rows = keyed_rows
                break
    return rows


def survey_overlay_html(company_name: str, survey_map: dict) -> str:
    """Build the purple hover-overlay HTML for survey results."""
    rows = _survey_rows_for(company_name, survey_map)
    if not rows:
        return (
            '<div class="survey-overlay">'
            '<h4>📝 Community Survey</h4>'
            '<div class="s-no-data">No survey responses yet for this company.<br>'
            'Be the first to share your experience!</div>'
            '</div>'
        )

    FIELDS = [
        ("speaking_up",    "Comfortable speaking up"),
        ("ideas_heard",    "Ideas heard equally"),
        ("parental_leave", "Comfortable taking parental leave"),
        ("promotion",      "Equal promotion opportunities"),
        ("pay_equity",     "Pay equity across genders"),
        ("recommend",      "Would recommend to other women"),
    ]
    n = len(rows)
    avgs = {}
    for field, _ in FIELDS:
        vals = [float(r[field]) for r in rows if r.get(field) not in (None, "")]
        avgs[field] = sum(vals) / len(vals) if vals else None

    # Team composition (last row for simplicity)
    last = rows[-1]
    team_w     = last.get("team_women_pct", "")
    co_w       = last.get("company_women_pct", "")
    lead_w     = last.get("leadership_women_pct", "")
    comments   = [r["comments"].strip() for r in rows if r.get("comments", "").strip()]

    rows_html = ""
    for field, label in FIELDS:
        avg = avgs.get(field)
        if avg is None:
            continue
        pct = (avg - 1) / 4 * 100          # map 1-5 → 0-100%
        rows_html += (
            f'<div class="s-row">'
            f'<span class="s-label">{label}</span>'
            f'<div class="s-bar-bg"><div class="s-bar-fill" style="width:{pct:.0f}%"></div></div>'
            f'<span class="s-val">{avg:.1f}/5</span>'
            f'</div>'
        )

    comp_html = ""
    if team_w or co_w or lead_w:
        comp_html = (
            f'<div class="s-row" style="margin-top:8px">'
            f'<span class="s-label">Team % women</span>'
            f'<span class="s-val">{team_w}%</span></div>'
            f'<div class="s-row"><span class="s-label">Company % women</span>'
            f'<span class="s-val">{co_w}%</span></div>'
            f'<div class="s-row"><span class="s-label">Leadership % women</span>'
            f'<span class="s-val">{lead_w}%</span></div>'
        )

    comment_html = ""
    if comments:
        snippet = comments[-1][:120] + ("…" if len(comments[-1]) > 120 else "")
        comment_html = f'<div class="s-comment">“{snippet}”</div>'

    return (
        '<div class="survey-overlay">'
        '<h4>📝 Community Survey Results</h4>'
        f'<div class="s-count">{n} response{"s" if n != 1 else ""} from women in this company</div>'
        + rows_html + comp_html + comment_html +
        '</div>'
    )


# ─── Card renderers ───────────────────────────────────────────────────────────
def render_wgea_card(c: dict, survey_map: dict | None = None):
    """Company card with real WGEA metrics — richer than AI-generated cards."""
    raw   = c.get("_raw", {})
    emoji = EMOJI_MAP.get(c.get("industry", ""), "🏢")
    gpg   = raw.get("avg_total_remuneration_gpg_pct")
    uq    = raw.get("upper_quartile_women_pct")
    tags_html = " ".join(tag_html(h) for h in c.get("highlights", [])[:3])

    gpg_colour = "#DC2626" if (gpg or 0) > 20 else "#D97706" if (gpg or 0) > 12 else "#16A34A"
    gpg_html   = f'<span style="color:{gpg_colour};font-weight:700">{gpg:.1f}%</span>' if gpg is not None else "—"

    overlay = survey_overlay_html(c.get("name", ""), survey_map) if survey_map is not None else ""

    st.markdown(
        f"""
<div class="card-wrap">
<div class="card">
  <div class="card-header">
    <div class="company-logo">{emoji}</div>
    <div style="flex:1">
      <div class="card-title">{c.get("name","")}</div>
      <div class="card-subtitle">{c.get("industry","")} <span class="wgea-badge">WGEA 2024–25</span></div>
    </div>
  </div>
  <div class="rating-row">
    <span class="stars">{stars_html(c.get("rating", 0))}</span>
    <span class="review-count">{c.get("employees","")}</span>
  </div>
  <div class="metrics">
    <div class="metric-row">
      <span class="metric-label">Women in workforce</span>
      <span class="metric-value">{raw.get("women_pct","—")}%</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Women in upper pay quartile</span>
      <span class="metric-value">{uq if uq is not None else "—"}%</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Avg remuneration pay gap</span>
      <span class="metric-value">{gpg_html}</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Gender Equality score</span>
      <span class="metric-value">{c.get("gender_equality","—")}/5</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Pay Equity score</span>
      <span class="metric-value">{c.get("pay_equity","—")}/5</span>
    </div>
  </div>
  <div class="card-footer">
    <span>📍 {c.get("location","")}</span>
  </div>
  <div class="tags" style="margin-top:10px">{tags_html}</div>
</div>
{overlay}
</div>""",
        unsafe_allow_html=True,
    )


def render_company_card(c: dict, survey_map: dict | None = None):
    emoji = EMOJI_MAP.get(c.get("industry", ""), "🏢")
    tags_html = " ".join(tag_html(h) for h in c.get("highlights", [])[:3])
    wgea = f'<span class="wgea-badge">WGEA Data</span>' if c.get("wgea_data") else ""

    overlay = survey_overlay_html(c.get("name", ""), survey_map) if survey_map is not None else ""

    st.markdown(
        f"""
<div class="card-wrap">
<div class="card">
  <div class="card-header">
    <div class="company-logo">{emoji}</div>
    <div style="flex:1">
      <div class="card-title">{c.get("name","")}</div>
      <div class="card-subtitle">{c.get("industry","")} {wgea}</div>
    </div>
  </div>
  <div class="rating-row">
    <span class="stars">{stars_html(c.get("rating", 0))}</span>
    <span class="review-count">({c.get("reviews", 0)} reviews)</span>
  </div>
  <div class="metrics">
    <div class="metric-row">
      <span class="metric-label">Gender Equality</span>
      <span class="metric-value">{c.get("gender_equality","—")}/5</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Women in Leadership</span>
      <span class="metric-value">{c.get("women_leadership","—")}/5</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Pay Equity</span>
      <span class="metric-value">{c.get("pay_equity","—")}/5</span>
    </div>
  </div>
  <div class="card-footer">
    <span>📍 {c.get("location","")}</span>
    <span>👥 {c.get("employees","")}</span>
  </div>
  <div class="tags" style="margin-top:10px">{tags_html}</div>
</div>
{overlay}
</div>""",
        unsafe_allow_html=True,
    )


def render_job_card(j: dict):
    tags_html = " ".join(tag_html(t) for t in j.get("tags", []))
    salary = fmt_salary(j)
    remote_icon = "🌐 Remote" if j.get("remote") else "🏢 On-site"
    fit = f'<div class="fit-reason">💡 {j["fit_reason"]}</div>' if j.get("fit_reason") else ""
    url_link = (
        f'<a href="{j["url"]}" target="_blank" style="font-size:12px;color:#7C3AED;">View listing →</a>'
        if j.get("url")
        else ""
    )
    st.markdown(
        f"""
<div class="card">
  <div style="display:flex; justify-content:space-between; align-items:flex-start;">
    <div class="card-header" style="margin-bottom:0">
      <div class="company-logo" style="width:40px;height:40px;font-size:18px;">💼</div>
      <div>
        <div class="card-title">{j.get("title","")}</div>
        <div class="card-subtitle">{j.get("company","")}</div>
      </div>
    </div>
    <div style="text-align:right; flex-shrink:0; margin-left:12px;">
      <div class="job-salary">{salary}</div>
      <div class="equality-score">
        <span style="color:#F59E0B">{stars_html(j.get("equality_score",0))}</span>
        {j.get("equality_score","—")} equality score
      </div>
    </div>
  </div>
  <div class="job-description">{j.get("description","")}</div>
  <div class="job-meta">
    <span>📍 {j.get("location","")}</span>
    <span>{remote_icon}</span>
    <span>🕐 {j.get("type","")}</span>
    <span>📊 {j.get("level","")}</span>
    <span>📅 {posted_label(j.get("posted_days_ago"))}</span>
  </div>
  <div class="tags">{tags_html}</div>
  {fit}
  <div style="margin-top:8px">{url_link}</div>
</div>""",
        unsafe_allow_html=True,
    )


MENTOR_AVATARS = ["👩‍💻", "👩‍💼", "👩‍🔬", "👩‍🏫", "👩‍⚕️", "🧑‍💻"]

def render_mentor_card(m: dict, idx: int = 0):
    avatar = MENTOR_AVATARS[idx % len(MENTOR_AVATARS)]
    tags_html = " ".join(tag_html(t) for t in m.get("expertise", [])[:3])
    st.markdown(
        f"""
<div class="card mentor-card">
  <div class="mentor-photo">{avatar}</div>
  <div class="card-title" style="text-align:center">{m.get("name","")}</div>
  <div class="card-subtitle" style="text-align:center">{m.get("title","")}</div>
  <div class="card-subtitle" style="text-align:center">{m.get("company","")}</div>
  <div class="rating-row" style="justify-content:center;margin-top:8px">
    <span class="stars">{stars_html(m.get("rating",0))}</span>
    <span class="review-count">({m.get("mentees",0)} mentees)</span>
  </div>
  <div class="mentor-bio">{m.get("bio","")}</div>
  <div class="mentor-detail">📅 {m.get("sessions_per_month","—")} sessions/month</div>
  <div class="mentor-detail">💼 {m.get("years_experience","—")} years experience</div>
  <div class="mentor-detail">🌐 {m.get("languages","—")}</div>
  <div class="tags" style="margin-top:10px">{tags_html}</div>
</div>""",
        unsafe_allow_html=True,
    )


# ─── Pages ────────────────────────────────────────────────────────────────────
def companies_page(profile: dict):
    st.markdown('<div class="page-heading">Company Ratings</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Discover companies committed to gender equality and supporting women in tech</div>',
        unsafe_allow_html=True,
    )

    col_search, col_industry, col_btn = st.columns([4, 2, 1])
    with col_search:
        query = st.text_input("", placeholder="Search companies or industries...", key="co_query", label_visibility="collapsed")
    with col_industry:
        industry = st.selectbox("", INDUSTRY_OPTIONS, key="co_industry", label_visibility="collapsed")
    with col_btn:
        search = st.button("Search", key="co_search", use_container_width=True)

    if search and query:
        with st.spinner("Searching for companies and their gender equality data…"):
            try:
                from agent import search_companies
                st.session_state.companies = search_companies(query, industry)
            except RuntimeError as e:
                st.error(f"⚠️ {e}")
            except Exception as e:
                st.error(f"Search failed: {e}")

    # ── WGEA real data section ────────────────────────────────────────────────
    wgea_raw = load_wgea_data()
    survey_map = load_survey_data()
    
    if wgea_raw:
        # Filter by industry if selected
        wgea_companies = [wgea_to_card(k, v) for k, v in wgea_raw.items()]
        if industry != "All Industries":
            wgea_companies = [c for c in wgea_companies if industry.lower() in c["industry"].lower()]

        # Filter by search query against WGEA set
        if query:
            q = query.lower()
            wgea_filtered = [c for c in wgea_companies if q in c["name"].lower() or q in c["industry"].lower()]
        else:
            wgea_filtered = wgea_companies

        if wgea_filtered:
            st.markdown(
                """<div style="display:flex;align-items:center;gap:10px;margin:16px 0 12px;">
                    <span class="wgea-badge" style="font-size:13px;padding:4px 10px;">🇦🇺 WGEA Verified Data</span>
                    <span style="font-size:13px;color:#6B7280;">Real Australian employer data from the Workplace Gender Equality Agency (2024–25)</span>
                </div>""",
                unsafe_allow_html=True,
            )
            cols = st.columns(3)
            for i, company in enumerate(wgea_filtered):
                with cols[i % 3]:
                    render_wgea_card(company, survey_map)

    # ── AI search results ─────────────────────────────────────────────────────
    ai_companies = st.session_state.get("companies", [])
    if ai_companies:
        st.markdown(
            '<div style="margin:24px 0 12px;font-weight:600;color:#111827;font-size:15px;">🔍 AI Search Results</div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(3)
        for i, company in enumerate(ai_companies):
            with cols[i % 3]:
                render_company_card(company, survey_map)

    # ── Empty state (no WGEA data and no search yet) ──────────────────────────
    if not wgea_raw and not ai_companies:
        st.markdown(
            """<div class="empty-state">
              <div class="icon">🏢</div>
              <p>Search for companies to see their gender equality ratings, women in leadership scores, and pay equity data.</p>
            </div>""",
            unsafe_allow_html=True,
        )


def jobs_page(profile: dict):
    st.markdown('<div class="page-heading">Job Opportunities</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Find positions at companies that value gender equality and diversity</div>',
        unsafe_allow_html=True,
    )

    col_search, col_level, col_type, col_btn = st.columns([4, 1.5, 1.5, 1])
    with col_search:
        query = st.text_input("", placeholder="Search jobs...", key="job_query", label_visibility="collapsed")
    with col_level:
        level = st.selectbox("", LEVEL_OPTIONS, key="job_level", label_visibility="collapsed")
    with col_type:
        job_type = st.selectbox("", TYPE_OPTIONS, key="job_type", label_visibility="collapsed")
    with col_btn:
        search = st.button("Search", key="job_search", use_container_width=True)

    if search and query:
        with st.spinner("Searching for female-friendly job listings…"):
            try:
                from agent import search_jobs
                st.session_state.jobs = search_jobs(query, level, job_type, profile)
            except RuntimeError as e:
                st.error(f"⚠️ {e}")
            except Exception as e:
                st.error(f"Search failed: {e}")

    jobs = st.session_state.get("jobs", [])

    if not jobs:
        st.markdown(
            """<div class="empty-state">
              <div class="icon">💼</div>
              <p>Search for jobs to find positions at companies rated highly for gender equality, pay transparency, and work-life balance.</p>
            </div>""",
            unsafe_allow_html=True,
        )
        return

    for job in jobs:
        render_job_card(job)


def mentors_page():
    st.markdown('<div class="page-heading">Find a Mentor</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Connect with experienced women leaders who can guide your career journey</div>',
        unsafe_allow_html=True,
    )

    # Static mentor data — real mentor matching is v2
    MENTORS = [
        {
            "name": "Sarah Chen", "title": "VP of Engineering", "company": "CloudNine Solutions",
            "rating": 4.9, "mentees": 28,
            "bio": "Passionate about helping women navigate tech careers. Led multiple engineering teams from startup to scale-up.",
            "sessions_per_month": 2, "years_experience": 15, "languages": "English, Mandarin",
            "expertise": ["Engineering Leadership", "Career Growth", "Technical Strategy"],
        },
        {
            "name": "Maya Patel", "title": "Senior Product Manager", "company": "TechVision Inc",
            "rating": 4.8, "mentees": 35,
            "bio": "Former engineer turned PM. Love helping others transition into product roles and build user-centric products.",
            "sessions_per_month": 4, "years_experience": 10, "languages": "English, Hindi",
            "expertise": ["Product Management", "AI/ML Products", "User Research"],
        },
        {
            "name": "Jennifer Martinez", "title": "Principal Software Engineer", "company": "DataFlow Systems",
            "rating": 4.9, "mentees": 42,
            "bio": "Specialised in distributed systems and mentoring women in engineering. Happy to help with interview prep and system design.",
            "sessions_per_month": 3, "years_experience": 12, "languages": "English, Spanish",
            "expertise": ["Software Architecture", "System Design", "Code Review"],
        },
        {
            "name": "Amelia Brooks", "title": "Head of Data Science", "company": "FinTech Forward",
            "rating": 4.7, "mentees": 19,
            "bio": "Building inclusive data teams and helping women break into data science from non-traditional backgrounds.",
            "sessions_per_month": 2, "years_experience": 9, "languages": "English",
            "expertise": ["Data Science", "Career Transition", "Salary Negotiation"],
        },
        {
            "name": "Priya Nair", "title": "Engineering Manager", "company": "GreenTech Innovations",
            "rating": 4.8, "mentees": 22,
            "bio": "Champion of return-to-work programs. Experienced helping women re-enter the workforce after career breaks.",
            "sessions_per_month": 3, "years_experience": 11, "languages": "English, Tamil",
            "expertise": ["Return-to-work", "Management", "Work-life Balance"],
        },
        {
            "name": "Lisa Wong", "title": "CTO", "company": "HealthTech Plus",
            "rating": 4.9, "mentees": 51,
            "bio": "One of few female CTOs in healthcare tech. Passionate about getting more women into leadership and exec roles.",
            "sessions_per_month": 2, "years_experience": 18, "languages": "English, Cantonese",
            "expertise": ["Executive Leadership", "Fundraising", "Board Presence"],
        },
    ]

    col_search, col_expertise = st.columns([4, 2])
    with col_search:
        search_q = st.text_input("Search mentors", placeholder="Search mentors by name, role, or expertise...", key="mentor_query", label_visibility="collapsed")
    with col_expertise:
        expertise_filter = st.selectbox(
            "Filter by expertise", ["All Expertise", "Engineering Leadership", "Product Management",
                 "Data Science", "Return-to-work", "Executive Leadership",
                 "Career Transition", "Software Architecture"],
            key="mentor_expertise", label_visibility="collapsed"
        )

    filtered = MENTORS
    if search_q:
        q = search_q.lower()
        filtered = [m for m in MENTORS if q in m["name"].lower() or q in m["title"].lower()
                    or q in m["company"].lower() or any(q in e.lower() for e in m["expertise"])]
    if expertise_filter != "All Expertise":
        filtered = [m for m in filtered if any(expertise_filter.lower() in e.lower() for e in m["expertise"])]

    if not filtered:
        st.markdown('<div class="empty-state"><div class="icon">👩‍🏫</div><p>No mentors found matching your search.</p></div>', unsafe_allow_html=True)
        return

    cols = st.columns(3)
    for i, mentor in enumerate(filtered):
        with cols[i % 3]:
            render_mentor_card(mentor, i)


def survey_page():
    st.markdown('<div class="page-heading">Share Your Experience</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Help other women by sharing anonymous data about your workplace</div>',
        unsafe_allow_html=True,
    )

    with st.form("dei_survey"):
        st.markdown("**About your workplace**")
        company = st.text_input("Company name (or leave blank to keep anonymous)")
        industry = st.selectbox("Industry", INDUSTRY_OPTIONS[1:])
        gender = st.selectbox("Your gender", ["Woman", "Non-binary", "Man", "Prefer not to say"])

        st.markdown("---")
        st.markdown("**Rate your experience (1 = Strongly disagree, 5 = Strongly agree)**")

        col1, col2 = st.columns(2)
        with col1:
            speaking_up    = st.slider("I felt comfortable speaking up in meetings", 1, 5, 3)
            ideas_heard    = st.slider("My ideas were heard and valued equally", 1, 5, 3)
            parental_leave = st.slider("I felt comfortable taking parental leave", 1, 5, 3)
        with col2:
            promotion      = st.slider("Promotion opportunities felt equal for all genders", 1, 5, 3)
            pay_equity     = st.slider("I believe pay was equitable across genders", 1, 5, 3)
            recommend      = st.slider("I would recommend this company to other women", 1, 5, 3)

        st.markdown("---")
        st.markdown("**Team composition (approximate %)**")
        col3, col4 = st.columns(2)
        with col3:
            team_women = st.number_input("% women on your direct team", 0, 100, 40)
            company_women = st.number_input("% women company-wide", 0, 100, 35)
        with col4:
            leadership_women = st.number_input("% women in leadership", 0, 100, 25)

        additional = st.text_area("Any other comments? (optional)")

        submitted = st.form_submit_button("Submit anonymously", use_container_width=True)

    if submitted:
        row = {
            "timestamp": datetime.utcnow().isoformat(),
            "company": company,
            "industry": industry,
            "gender": gender,
            "speaking_up": speaking_up,
            "ideas_heard": ideas_heard,
            "parental_leave": parental_leave,
            "promotion": promotion,
            "pay_equity": pay_equity,
            "recommend": recommend,
            "team_women_pct": team_women,
            "company_women_pct": company_women,
            "leadership_women_pct": leadership_women,
            "comments": additional,
        }
        csv_path = Path("survey_data.csv")
        write_header = not csv_path.exists()
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if write_header:
                writer.writeheader()
            writer.writerow(row)
        
        # Clear the cached survey data so the new entry reflects immediately on the companies page
        load_survey_data.clear()
        
        st.success("Thank you! Your response has been saved and will help other women make informed decisions.")


# ─── Profile persistence ──────────────────────────────────────────────────────
PROFILE_PATH = Path("profile.json")

PROFILE_DEFAULTS: dict = {
    "skills": "",
    "location": "",
    "career_stage": "Early",
    "priorities": [],
    "career_break": False,
    "break_reason": "",
}

# Map profile field names → Streamlit widget session-state keys
_PROFILE_WIDGET_KEYS: dict = {
    "skills":       "profile_skills",
    "location":     "profile_location",
    "career_stage": "profile_stage",
    "priorities":   "profile_priorities",
    "career_break": "profile_break",
    "break_reason": "profile_break_reason",
}

def load_profile() -> None:
    """Seed widget session-state keys from profile.json (runs once per session)."""
    if st.session_state.get("_profile_loaded"):
        return
    saved: dict = PROFILE_DEFAULTS.copy()
    if PROFILE_PATH.exists():
        try:
            saved.update(json.loads(PROFILE_PATH.read_text(encoding="utf-8")))
        except Exception:
            pass  # corrupt file — fall back to defaults
    for field, widget_key in _PROFILE_WIDGET_KEYS.items():
        if widget_key not in st.session_state:   # don't overwrite live widget state
            st.session_state[widget_key] = saved.get(field, PROFILE_DEFAULTS[field])
    st.session_state["_profile_loaded"] = True

def save_profile(profile: dict) -> None:
    """Persist current profile to profile.json."""
    try:
        PROFILE_PATH.write_text(
            json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass  # silently ignore write errors (e.g. read-only filesystem)


# ─── Sidebar: user profile ─────────────────────────────────────────────────────
def profile_sidebar() -> dict:
    with st.sidebar:
        st.markdown("## 👤 Your Profile")
        st.caption("Personalise your job search results")

        skills = st.text_area(
            "Skills & experience",
            placeholder="e.g. 5 years Python, led small teams, data analysis",
            key="profile_skills",
        )
        location = st.text_input("Location or 'Remote'", placeholder="e.g. Sydney, AU", key="profile_location")
        career_stage = st.selectbox("Career stage", ["Early", "Mid", "Senior", "Executive"], key="profile_stage")
        priorities = st.multiselect("Workplace priorities", PRIORITY_OPTIONS, key="profile_priorities")
        career_break = st.checkbox("I'm returning from a career break", key="profile_break")
        if career_break:
            break_reason = st.text_input("Reason (optional)", placeholder="e.g. caregiving, relocation", key="profile_break_reason")
        else:
            break_reason = ""

        profile = {
            "skills": skills,
            "location": location,
            "career_stage": career_stage,
            "priorities": priorities,
            "career_break": career_break,
            "break_reason": break_reason,
        }

        st.markdown("---")
        if st.button("💾 Save profile", key="save_profile_btn", use_container_width=True):
            save_profile(profile)
            st.success("Profile saved!")

        if not os.getenv("GOOGLE_API_KEY"):
            st.error("⚠️ GOOGLE_API_KEY not set.\nAdd it to a `.env` file to enable AI search.")

    return profile


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    inject_css()

    # ── Sidebar visibility state ──────────────────────────────────────────────
    load_profile()  # seed widget defaults from disk (no-op after first run)
    if "sidebar_open" not in st.session_state:
        st.session_state.sidebar_open = False

    # Inject CSS to show or hide the sidebar
    if st.session_state.sidebar_open:
        st.markdown(
            """
            <style>
            section[data-testid="stSidebar"] { display: flex !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            section[data-testid="stSidebar"] { display: none !important; }
            .main .block-container { margin-left: 0 !important; max-width: 100% !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )

    # ── Brand header (2 columns: brand left, toggle button right) ─────────────
    col_brand, col_btn = st.columns([10, 2])
    with col_brand:
        st.markdown(
            """
<div class="brand-bar" style="border-bottom:none; padding-bottom:0; margin-bottom:0">
  <div class="brand-icon">👩‍💼</div>
  <div>
    <div class="brand-name">WomenInTech</div>
    <div class="brand-tagline">Empowering careers</div>
  </div>
</div>""",
            unsafe_allow_html=True,
        )
    with col_btn:
        toggle_label = "✕ Profile" if st.session_state.sidebar_open else "☰ Profile"
        st.markdown(
            """
            <style>
            [data-testid="stBaseButton-secondary"][kind="secondary"]:has(+ *) { display:none; }
            div[data-testid="column"]:last-child .stButton > button {
                font-size: 12px !important;
                padding: 4px 10px !important;
                margin-top: 22px;
                background: #F5F3FF !important;
                color: #6D28D9 !important;
                border: 1px solid #DDD6FE !important;
                border-radius: 6px !important;
                font-weight: 600 !important;
                white-space: nowrap;
            }
            div[data-testid="column"]:last-child .stButton > button:hover {
                background: #EDE9FE !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        if st.button(toggle_label, key="sidebar_toggle"):
            st.session_state.sidebar_open = not st.session_state.sidebar_open
            st.rerun()

    st.markdown(
        "<hr style='margin:8px 0 0; border:none; border-top:1px solid #E5E7EB'>",
        unsafe_allow_html=True,
    )

    # ── Profile sidebar (always rendered so widget state is never dropped) ───────
    # Streamlit purges session_state keys for widgets that aren't rendered.
    # Calling profile_sidebar() unconditionally keeps the keys alive; CSS
    # handles the visual show/hide instead.
    profile = profile_sidebar()

    tab_co, tab_jobs, tab_mentors, tab_survey = st.tabs(
        ["🏢  Companies", "💼  Jobs", "👩‍🏫  Mentors", "📝  Share Your Experience"]
    )

    with tab_co:
        companies_page(profile)
    with tab_jobs:
        jobs_page(profile)
    with tab_mentors:
        mentors_page()
    with tab_survey:
        survey_page()


if __name__ == "__main__":
    main()
