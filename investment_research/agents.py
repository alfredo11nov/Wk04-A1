"""
Investment Research Team — three Claude agents working in sequence.

Financial Analyst  → searches live news + watchlist data
Fund Manager       → analyses portfolio vs research, makes recommendations
Admin              → formats the combined output into a polished daily briefing
"""

import json
import anthropic
from datetime import datetime

from .config import MODEL, PORTFOLIO_FILE, WATCHLIST_FILE

client = anthropic.Anthropic()

# ── System prompts ────────────────────────────────────────────────────────────

_ANALYST_SYSTEM = """\
You are an experienced financial analyst specialising in global markets.
Every morning you scan international news and research investment ideas.
Use the web_search tool to fetch the latest headlines and fund data.
Be specific: cite price moves, macro drivers, and earnings surprises where available.
Organise your report under clear headings."""

_FUND_MANAGER_SYSTEM = """\
You are a seasoned fund manager responsible for a moderate-risk portfolio.
You receive a fresh research report from your analyst each morning.
Your job is to compare it against the current holdings and available cash,
then produce clear, prioritised recommendations: rebalance, buy, hold, or trim.
Always justify each action with evidence from the analyst report.
Be conservative — protect capital first, then seek growth."""

_ADMIN_SYSTEM = """\
You are the investment team administrator.
You receive the analyst's research and the fund manager's recommendations.
Produce a polished, easy-to-read Daily Investment Briefing.
Structure it with these exact section headings:

## Market Summary
## Key News Highlights
## Watchlist Movers
## Portfolio Actions
## Risk Alerts

Keep the total briefing under 600 words.
At the very end add one line (no markdown) labelled exactly:
PUSH_NOTIFICATION: <max 160 chars summarising today's top action>"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load(path) -> dict:
    with open(path) as f:
        return json.load(f)


def _text(content) -> str:
    """Extract plain text blocks from an API response content list."""
    return "\n".join(b.text for b in content if getattr(b, "type", None) == "text")


def _call(system: str, user: str, tools: list | None = None) -> str:
    """Single Claude API call; returns extracted text."""
    kwargs = dict(
        model=MODEL,
        max_tokens=8192,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    if tools:
        kwargs["tools"] = tools

    # Server-side tools (web_search) are executed by Anthropic automatically;
    # the response may include tool_use / web_search_tool_result blocks before
    # the final text — _text() skips those and returns only text blocks.
    response = client.messages.create(**kwargs)
    return _text(response.content)


# ── Agent functions ───────────────────────────────────────────────────────────

def run_financial_analyst() -> str:
    """Research today's financial news and assess the watchlist."""
    watchlist = _load(WATCHLIST_FILE)
    today = datetime.now().strftime("%A, %B %d, %Y")

    funds_text = "\n".join(
        f"• {f['symbol']} — {f['name']}: {f['interest']}"
        for f in watchlist["funds"]
    )
    themes_text = ", ".join(watchlist["themes"])
    regions_text = ", ".join(watchlist["focus_regions"])

    prompt = f"""\
Date: {today}

**Task 1 — International News**
Search for and summarise the 5–7 most market-moving international financial news
stories published today. Focus on macro events, central bank signals, earnings
surprises, geopolitical developments, and commodity moves.

**Task 2 — Watchlist Deep-Dive**
For each item below, search for the latest price movement, news, and sentiment.
Give a one-line Buy / Watch / Avoid rating with reasoning.

{funds_text}

**Investment Themes to track:** {themes_text}
**Focus Regions:** {regions_text}
"""

    return _call(
        system=_ANALYST_SYSTEM,
        user=prompt,
        tools=[{"type": "web_search_20250305"}],
    )


def run_fund_manager(analyst_report: str) -> str:
    """Produce portfolio recommendations from the analyst report."""
    portfolio = _load(PORTFOLIO_FILE)
    today = datetime.now().strftime("%A, %B %d, %Y")

    holdings_text = "\n".join(
        f"• {h['symbol']} ({h['name']}): {h['shares']} shares @ avg ${h['avg_cost']:.2f}  [{h['sector']}]"
        for h in portfolio["holdings"]
    )

    prompt = f"""\
Date: {today}

**Current Portfolio**
{holdings_text}
Cash available: ${portfolio['cash']:,.2f}
Risk tolerance: {portfolio['risk_tolerance']}
Goals: {portfolio['investment_goals']}

**Analyst Research Report**
{analyst_report}

Please provide:
1. Portfolio Health — how is today's news affecting existing positions?
2. Rebalancing — any positions to trim or exit?
3. New Opportunities — which watchlist items warrant a buy now?
4. Top 3 Priority Actions — with specific sizing suggestions ($ or share count).
5. Risk Flags — immediate threats to any current holding.
"""

    return _call(system=_FUND_MANAGER_SYSTEM, user=prompt)


def run_admin(analyst_report: str, fund_manager_report: str) -> str:
    """Format the combined output into the daily briefing."""
    today = datetime.now().strftime("%A, %B %d, %Y")

    prompt = f"""\
Date: {today}

**Analyst Report**
{analyst_report}

**Fund Manager Recommendations**
{fund_manager_report}

Produce the Daily Investment Briefing now.
"""

    return _call(system=_ADMIN_SYSTEM, user=prompt)


# ── Pipeline ──────────────────────────────────────────────────────────────────

def extract_push_notification(briefing: str) -> str:
    """Pull the PUSH_NOTIFICATION line out of the admin briefing."""
    for line in briefing.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("PUSH_NOTIFICATION:"):
            return stripped.split(":", 1)[1].strip()[:160]
    return "Daily investment briefing ready — check Claude for full report."


def run_research_team() -> dict:
    """
    Orchestrate all three agents and return a results dict:
        analyst_report, fund_manager_report, briefing, push_notification
    """
    print("=" * 64)
    print("  Investment Research Team — Daily Briefing")
    print(f"  {datetime.now().strftime('%A, %B %d, %Y  %H:%M')}")
    print("=" * 64)

    print("\n[1/3] Financial Analyst — searching markets & watchlist…")
    analyst_report = run_financial_analyst()

    print("\n[2/3] Fund Manager — analysing portfolio…")
    fund_manager_report = run_fund_manager(analyst_report)

    print("\n[3/3] Admin — preparing briefing…")
    briefing = run_admin(analyst_report, fund_manager_report)

    push_notification = extract_push_notification(briefing)

    return {
        "analyst_report": analyst_report,
        "fund_manager_report": fund_manager_report,
        "briefing": briefing,
        "push_notification": push_notification,
    }
