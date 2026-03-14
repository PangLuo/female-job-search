import asyncio
import json
import os
from ddgs import DDGS
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv()


def web_search(query: str, max_results: int = 2) -> list[dict]:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")[:200],  # cap snippet length
                }
                for r in results
            ]
    except Exception as e:
        return [{"error": str(e)}]


def run_agent(system_prompt: str, user_message: str) -> str:
    def web_search_tool(query: str) -> str:
        """Search the web for job listings, company DEI data, WGEA data,
        women in leadership stats, parental leave policies, pay gap reports."""
        return json.dumps(web_search(query))

    async def _run():
        agent = LlmAgent(
            name="job_search_agent",
            model="gemini-2.5-flash",
            instruction=system_prompt,
            tools=[web_search_tool],
        )

        session_service = InMemorySessionService()
        session = await session_service.create_session(app_name="job_search", user_id="user")
        runner = Runner(agent=agent, app_name="job_search", session_service=session_service)

        content = types.Content(role="user", parts=[types.Part(text=user_message)])

        async for event in runner.run_async(user_id="user", session_id=session.id, new_message=content):
            if event.is_final_response() and event.content and event.content.parts:
                return event.content.parts[0].text

        return "[]"

    try:
        return asyncio.run(_run())
    except Exception as e:
        err = str(e)
        if "quota" in err.lower() or "429" in err:
            raise RuntimeError("Rate limit reached. Please wait and try again.") from e
        raise


def extract_json(text: str) -> list:
    try:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except json.JSONDecodeError:
        pass
    return []


# ─── Company Search ────────────────────────────────────────────────────────────

COMPANY_SYSTEM_PROMPT = """You are an expert researcher specialising in workplace gender equality.

Your job: search for companies and evaluate them on female-friendliness using real data.

For AUSTRALIAN companies always search for WGEA (Workplace Gender Equality Agency) data.
For all companies search for: gender pay gap reports, % women in management/C-suite, parental leave policies, flexible work, DEI awards.

Return a JSON array of exactly 6 company objects. Each object MUST have these fields:
{
  "name": "Company Name",
  "industry": "Industry",
  "rating": 4.5,
  "reviews": 234,
  "gender_equality": 4.7,
  "women_leadership": 4.5,
  "pay_equity": 4.3,
  "location": "City, State/Country",
  "employees": "1000-5000 employees",
  "description": "1-2 sentence description of the company",
  "highlights": ["key DEI achievement", "another positive fact"],
  "wgea_data": null
}

Score each metric 1.0-5.0 based on real evidence you find. Return ONLY the JSON array, no other text."""


def search_companies(query: str, industry: str = "All Industries") -> list[dict]:
    industry_filter = f" in the {industry} industry" if industry != "All Industries" else ""
    message = (
        f"Find 6 female-friendly companies matching: '{query}'{industry_filter}. "
        "Search for their gender equality data, WGEA reports (if Australian), women in leadership stats, "
        "pay equity data, and parental leave policies. Return the JSON array."
    )
    result = run_agent(COMPANY_SYSTEM_PROMPT, message)
    return extract_json(result)


# ─── Job Search ───────────────────────────────────────────────────────────────

JOB_SYSTEM_PROMPT = """You are an expert job search agent specialising in finding female-friendly workplaces.

Your job: find REAL, current job listings and evaluate each company's female-friendliness.

For each job also search for: the company's gender pay gap, % women in leadership, parental leave policy, flexible work options, DEI track record.

Return a JSON array of exactly 6 job objects. Each object MUST have these fields:
{
  "title": "Job Title",
  "company": "Company Name",
  "salary_min": 120000,
  "salary_max": 160000,
  "salary_currency": "AUD",
  "equality_score": 4.2,
  "description": "2-3 sentence job description",
  "location": "City, State",
  "remote": true,
  "type": "Full-time",
  "level": "Senior",
  "posted_days_ago": 3,
  "tags": ["Remote", "Equal pay", "Parental leave"],
  "url": "https://...",
  "fit_reason": "Why this role is good for women specifically"
}

Tags can include: Remote, Hybrid, Women-friendly, Equal pay, Parental leave, Flexible hours, Mentorship, Diverse team, Return-to-work, Salary transparent.
Return ONLY the JSON array, no other text."""


def search_jobs(
    query: str,
    level: str = "All Levels",
    job_type: str = "All Types",
    profile: dict | None = None,
) -> list[dict]:
    level_filter = f", {level}" if level != "All Levels" else ""
    type_filter = f", {job_type}" if job_type != "All Types" else ""
    profile_context = ""
    if profile and any(profile.values()):
        profile_context = f"\n\nUser profile context: {json.dumps(profile)}"

    message = (
        f"Find 6 current job listings for: '{query}'{level_filter}{type_filter}. "
        "Search job boards (LinkedIn, Seek, Indeed, etc.) for real listings. "
        "Research each company's female-friendliness."
        f"{profile_context} Return the JSON array."
    )
    result = run_agent(JOB_SYSTEM_PROMPT, message)
    return extract_json(result)
