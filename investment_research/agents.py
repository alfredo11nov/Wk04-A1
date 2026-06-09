"""
Investment Research Team — three Claude agents in a two-stage pipeline.

Stage 1 (06:00 SGT)  Financial Analyst + Fund Manager → cached to disk
Stage 2 (08:00 SGT)  Admin loads cache → formats briefing → sends notification

run_research_team() executes all three stages in one shot (used for kickoff / manual runs).
"""

import json
import anthropic
from datetime import datetime
from pathlib import Path

from .config import MODEL, PORTFOLIO_FILE, WATCHLIST_FILE, CACHE_FILE

client = anthropic.Anthropic()


# ── System prompts ────────────────────────────────────────────────────────────

_ANALYST_SYSTEM = """\
You are a senior financial analyst covering global equities and macro markets.
Your job: every morning, scan international news and produce actionable research.

Key behaviours:
- Use web_search to get live data — never rely solely on training knowledge for prices or news.
- For regular watchlist items: give latest price action, news catalyst, and a Buy / Watch / Avoid call.
- For "special_research" fund deep-dives: do a thorough multi-search investigation to answer each
  listed research question as completely as possible. Cite sources.
- Be specific: numbers, percentages, named companies, named people.
- Organise output with clear headings."""

_FUND_MANAGER_SYSTEM = """\
You are an experienced fund manager running an aggressive-growth portfolio (SGD ~$105k).

Strategy context:
- 60% high-risk bucket: focused 1–3 growth stocks, 20–50% annual return target.
- 40% low-risk bucket: S&P 500 index (IVV or QQQ).
- Maximum 5 concentrated bets per year at SGD $5,000–$10,000 each.
  Exception: rare asymmetric opportunities may exceed the 5-bet limit.
- Protect capital; avoid noise trading.

Your job: receive the analyst's morning research, compare it against the current
portfolio, and produce clear prioritised recommendations. Be direct — name the
ticker, the action, and the sizing in SGD."""

_ADMIN_SYSTEM = """\
You are the investment team administrator.
You receive the analyst's research and the fund manager's recommendations.
Produce a polished Daily Investment Briefing using these EXACT section headings:

## Market Summary
## Key News Highlights
## Situational Awareness Fund — Research Update
## Watchlist Movers
## Portfolio Actions
## Risk Alerts

Rules:
- Keep the full briefing under 700 words.
- The "Situational Awareness Fund" section must appear even if the analyst found no new data — write "No new data today" if needed.
- End the briefing (after all sections) with one plain-text line:
  PUSH_NOTIFICATION: <≤160 chars: today's single most important action or insight>"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def _text(content) -> str:
    return "\n".join(b.text for b in content if getattr(b, "type", None) == "text")


def _call(system: str, user: str, tools: list | None = None) -> str:
    kwargs = dict(
        model=MODEL,
        max_tokens=8192,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    if tools:
        kwargs["tools"] = tools
    response = client.messages.create(**kwargs)
    return _text(response.content)


# ── Stage 1 agents ────────────────────────────────────────────────────────────

def run_financial_analyst() -> str:
    watchlist = _load(WATCHLIST_FILE)
    today = datetime.now().strftime("%A, %B %d, %Y")

    funds_text = "\n".join(
        f"• {f['symbol']} — {f['name']}: {f['interest']}"
        for f in watchlist["funds"]
    )
    themes_text = ", ".join(watchlist["themes"])

    # Build special research section
    special_items = watchlist.get("special_research", [])
    special_text = ""
    if special_items:
        special_text = "\n\n**Special Research Deep-Dives (answer every question listed):**\n"
        for item in special_items:
            qs = "\n".join(f"  {i+1}. {q}" for i, q in enumerate(item["research_questions"]))
            special_text += (
                f"\n### {item['name']} (founded by {item['founder']})\n"
                f"Background: {item['background']}\n"
                f"Research questions:\n{qs}\n"
            )

    prompt = f"""\
Date: {today}

**Task 1 — International Macro & Market News**
Search for the 5–7 most market-moving financial stories published today.
Cover: central bank signals, earnings surprises, geopolitical developments,
commodity moves, and anything affecting AI / semiconductor / China / EV sectors.

**Task 2 — Watchlist Assessment**
For each item, search for latest price movement, news, and sentiment.
Give a one-line Buy / Watch / Avoid rating with brief reasoning.

{funds_text}

**Themes to track:** {themes_text}
{special_text}
"""

    return _call(
        system=_ANALYST_SYSTEM,
        user=prompt,
        tools=[{"type": "web_search_20250305"}],
    )


def run_fund_manager(analyst_report: str) -> str:
    portfolio = _load(PORTFOLIO_FILE)
    today = datetime.now().strftime("%A, %B %d, %Y")

    holdings_text = "\n".join(
        f"• {h['symbol']} ({h['name']}): {h['shares']} shares "
        f"@ avg {h['currency']} ${h['avg_cost']:.2f}  [{h['sector']}]"
        for h in portfolio["holdings"]
    )
    strat = portfolio["strategy"]

    prompt = f"""\
Date: {today}

**Current Portfolio (SGD ~$105k)**
{holdings_text}
Cash available: SGD ${portfolio['cash_sgd']:,.2f}

Strategy:
- High-risk bucket ({strat['high_risk_pct']}%): {strat['high_risk_notes']}
- Low-risk bucket ({strat['low_risk_pct']}%): {strat['low_risk_notes']}
- Annual bet allowance: {strat['bets_per_year']} trades × SGD ${strat['min_bet_sgd']:,}–${strat['max_bet_sgd']:,}

**Analyst Research Report**
{analyst_report}

Please provide:
1. **Portfolio Health** — how does today's news affect each holding?
2. **Rebalancing** — any position to trim or exit?
3. **New Opportunities** — watchlist items that match our concentrated-bet criteria?
4. **Top 3 Priority Actions** — ticker, action, SGD size, and one-sentence rationale.
5. **Risk Flags** — immediate threats to any current holding.
6. **Situational Awareness Fund Insight** — based on the analyst's deep-dive,
   is there anything in that fund's portfolio that overlaps with or challenges our thesis?
"""

    return _call(system=_FUND_MANAGER_SYSTEM, user=prompt)


# ── Stage 2 agent ─────────────────────────────────────────────────────────────

def run_admin(analyst_report: str, fund_manager_report: str) -> str:
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


# ── Cache helpers ─────────────────────────────────────────────────────────────

def save_research_cache(analyst_report: str, fund_manager_report: str) -> None:
    cache = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "generated_at": datetime.now().isoformat(),
        "analyst_report": analyst_report,
        "fund_manager_report": fund_manager_report,
    }
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)
    print(f"Research cached to {CACHE_FILE}")


def load_research_cache() -> tuple[str, str]:
    """Load today's research cache. Raises FileNotFoundError if missing."""
    with open(CACHE_FILE) as f:
        cache = json.load(f)
    today = datetime.now().strftime("%Y-%m-%d")
    if cache.get("date") != today:
        raise ValueError(f"Cache is from {cache['date']}, not today ({today}). Run Stage 1 first.")
    return cache["analyst_report"], cache["fund_manager_report"]


# ── Pipeline entry-points ─────────────────────────────────────────────────────

def extract_push_notification(briefing: str) -> str:
    for line in briefing.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("PUSH_NOTIFICATION:"):
            return stripped.split(":", 1)[1].strip()[:160]
    return "Daily investment briefing ready — check Claude for full report."


def run_stage1() -> None:
    """06:00 SGT — Research stage: Analyst + Fund Manager → cache."""
    print("=" * 64)
    print(f"  Stage 1: Background Research  [{datetime.now().strftime('%H:%M SGT')}]")
    print("=" * 64)

    print("\n[1/2] Financial Analyst — searching markets & watchlist…")
    analyst_report = run_financial_analyst()

    print("\n[2/2] Fund Manager — analysing portfolio…")
    fund_manager_report = run_fund_manager(analyst_report)

    save_research_cache(analyst_report, fund_manager_report)
    print("\nStage 1 complete. Research cached for 08:00 delivery.")


def run_stage2() -> dict:
    """08:00 SGT — Delivery stage: Admin formats & sends notification."""
    print("=" * 64)
    print(f"  Stage 2: Report Delivery  [{datetime.now().strftime('%H:%M SGT')}]")
    print("=" * 64)

    analyst_report, fund_manager_report = load_research_cache()

    print("\nAdmin — preparing briefing…")
    briefing = run_admin(analyst_report, fund_manager_report)
    push_notification = extract_push_notification(briefing)

    return {
        "analyst_report": analyst_report,
        "fund_manager_report": fund_manager_report,
        "briefing": briefing,
        "push_notification": push_notification,
    }


def run_research_team() -> dict:
    """All-in-one run: stages 1 + 2 sequentially (kickoff / manual trigger)."""
    print("=" * 64)
    print("  Investment Research Team — Full Run")
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
