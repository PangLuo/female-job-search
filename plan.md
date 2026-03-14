# Female-Friendly Job Search — Product Plan

## Problem

Standard job boards don't surface the information women actually need to make informed decisions: gender ratios in teams, parental leave policies, pay equity, and whether a company has a real track record of promoting women — not just DEI marketing copy.

---

## Core Concept

A job search tool that goes beyond keyword matching. The user provides a personal profile, and an AI agent searches for real job listings and evaluates each opportunity through female-friendliness lenses: gender ratios, women in leadership, pay transparency, parental leave, and culture signals. Results are ranked and explained in terms of what matters to that specific user.

---

## Features

### 1. User Profile (Input)

Rather than uploading a CV, the user answers a short set of questions:

- **Skills & experience** — free text description (e.g. "5 years Python, led small teams, data analysis")
- **Industry preference** — Tech, Finance, Healthcare, Government, Other
- **Location** — city or remote
- **Career stage** — Early, Mid, Senior, Executive
- **Workplace priorities** — user selects what matters most:
  - Pay equity
  - Flexible / async hours
  - Strong parental leave
  - Women in leadership
  - Mentorship programs
  - Return-to-work support
  - Salary transparency
- **Career break flag** — if returning from a break (caregiving, health, relocation), the user can flag this and optionally state the reason. The app will surface roles and companies with formal return-to-work programs.

---

### 2. Female-Specific Company Ratings

Each company in the results is evaluated on:

| Signal | Source |
|---|---|
| % women in management | WGEA (Australia), LinkedIn data, web search |
| % women in executive / C-suite | WGEA, company reports |
| Gender pay gap status | WGEA reporting, press mentions |
| Parental leave policy | Job posting, company website |
| Flexible / remote work culture | Job posting, Glassdoor reviews |
| Pay transparency | Whether salary band is published |
| DEI track record | Press coverage, public reports |

Each job result includes a **Female-Friendliness Score (1–5)** with bullet-point evidence, not just a number.

---

### 3. WGEA Data Integration (Australia)

For Australian employers, the app uses data from the [Workplace Gender Equality Agency (WGEA)](https://www.wgea.gov.au/Data-Explorer/) — the most authoritative public dataset on gender equality in Australian workplaces. This includes:

- Percentage of women in management and executive roles
- Whether the company reports its gender pay gap
- Parental leave benchmarks relative to industry

This is surfaced automatically when the user searches in an Australian location.

---

### 4. Gender Ratio Intelligence

Beyond company-level data, the app estimates team-level gender ratios where possible by:

- Analysing LinkedIn team pages (photos + names → AI gender estimation)
- Aggregating signals from multiple sources (job postings, team pages, press)
- Flagging teams or departments with particularly high or low representation

This is a differentiating feature from standard job boards, which show no team composition data.

---

### 5. Live Job Search

The agent searches the web in real time for current job listings matching the user's profile. It does not rely on a pre-indexed database of jobs, so results are always fresh. For each promising listing, the agent performs a second search to gather company culture and DEI data.

---

### 6. Career Gap Support

A dedicated mode for women returning to work after a career break:

- Finds companies with formal return-to-work programs (e.g. structured re-entry internships)
- Can reframe skills from non-traditional experience (caregiving, community work) in terms employers value
- Surfaces roles that explicitly welcome career restarters
- Removes the information penalty women face when their CV has a gap

---

### 7. Salary Confidence Tools

Women are statistically more likely to undervalue themselves in salary negotiations. The app addresses this by:

- Showing market rate ranges by role, location, and experience level
- Surfacing only companies that publicly post salary bands (removing pre-negotiation information asymmetry)
- Flagging roles where the salary band is not disclosed

---

### 8. Ranked Results with Explanations

Results are ranked first by female-friendliness score, then by skills match. Each result includes:

1. Job title, company, direct link
2. Why it matches this user's skills and experience
3. Female-friendliness score with supporting evidence
4. WGEA data (if Australian employer)
5. A one-sentence "why this is a good fit for you specifically" tailored to the user's stated priorities

---

## Data Sources

| Source | Data provided | Status |
|---|---|---|
| WGEA Data Explorer | AU employer gender equality data | Available (public) |
| Web search (live) | Job listings, company culture, DEI news | Available via AI agent |
| LinkedIn team pages | Team gender ratios (via AI estimation) | Requires crawler |
| Glassdoor | Gender ratings, parental leave reviews | No public API; web search fallback |
| Company careers pages | Parental leave, flexible work policies | Available via web search |
| DEI APIs | Structured DEI metrics | Not currently available |

---

## Out of Scope (v1)

- Mentor / community matching (connecting users to women at target companies)
- Saved searches or job tracking
- Resume parsing or upload
- Interview prep for bias-heavy questions
- Employer dashboard / company profiles

---

## Technical Approach

- **Frontend:** Streamlit (fast to build, visual enough for a prototype)
- **AI agent:** Claude (claude-sonnet-4-6) via Anthropic API, using the web_search tool for live data
- **Architecture:** User fills profile → agent searches for jobs and company DEI data → ranked results rendered in UI
- **3 files:** `app.py` (UI), `agent.py` (AI logic), `requirements.txt`
