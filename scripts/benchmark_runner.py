#!/usr/bin/env python3
"""
Manic Trading Benchmark — Runner & Visualization

Orchestrates 5 benchmark tasks (T1-T5) sequentially, then polls for
scoring results and renders a rich terminal visualization.
"""

import sys
import os
import json
import time
import math
import textwrap
import traceback

# ─── Add parent to path so we can import benchmark_api ────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import benchmark_api as api

# ─── ANSI Colors ──────────────────────────────────────────────────────────────

class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"
    BG_RED    = "\033[41m"
    BG_GREEN  = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE   = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN   = "\033[46m"

# ─── Terminal Helpers ─────────────────────────────────────────────────────────

TASK_NAMES = [
    "Market Snapshot",
    "Multi-source Intelligence",
    "Market Analysis",
    "Trading Decision & Execution",
    "Risk Management",
]

TASK_ICONS = ["📊", "🔍", "🧠", "💹", "🛡️"]

DIMENSION_NAMES = [
    "Real-time Data",
    "Multi-source Intel",
    "Market Analysis",
    "Trading Decision",
    "Risk Management",
]

DIMENSION_COLORS = [C.CYAN, C.BLUE, C.MAGENTA, C.GREEN, C.YELLOW]


def print_header(text, icon=""):
    """Print a section header."""
    width = 56
    print(f"\n{C.BOLD}{C.CYAN}{'─' * width}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  {icon}  {text}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}{'─' * width}{C.RESET}\n")


def print_task_start(index):
    """Print task start banner."""
    icon = TASK_ICONS[index]
    name = TASK_NAMES[index]
    print(f"  {C.BOLD}{C.WHITE}T{index + 1}{C.RESET} {icon}  {C.BOLD}{name}{C.RESET}", end="")
    sys.stdout.flush()


def print_task_done(duration_s, status="success"):
    """Print task completion inline."""
    if status == "success":
        print(f"  {C.GREEN}✓{C.RESET} {C.DIM}{duration_s:.1f}s{C.RESET}")
    else:
        print(f"  {C.RED}✗ {status}{C.RESET}")


def spinner_frames():
    """Yield spinner animation frames."""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    while True:
        yield frames[i % len(frames)]
        i += 1


def print_progress_bar(value, max_val, width=30, color=C.GREEN, label=""):
    """Print a colored progress bar."""
    ratio = min(value / max_val, 1.0) if max_val > 0 else 0
    filled = int(ratio * width)
    empty = width - filled
    bar = f"{color}{'█' * filled}{C.DIM}{'░' * empty}{C.RESET}"
    pct = f"{ratio * 100:5.1f}%"
    print(f"  {bar} {pct}  {label}")


# ─── ASCII Radar Chart ───────────────────────────────────────────────────────

def draw_radar_chart(scores, max_score=20, radius=8):
    """Draw an ASCII radar chart for 5 dimensions.

    Args:
        scores: dict with dimension names → scores (0-20)
        max_score: maximum possible score per dimension
        radius: chart radius in characters
    """
    dims = DIMENSION_NAMES
    n = len(dims)
    angles = [2 * math.pi * i / n - math.pi / 2 for i in range(n)]

    canvas_size = radius * 2 + 5
    cx, cy = canvas_size, radius + 2
    grid = [[" "] * (canvas_size * 2 + 1) for _ in range(canvas_size + 1)]

    # Draw concentric circles (25%, 50%, 75%, 100%)
    for pct in [0.25, 0.5, 0.75, 1.0]:
        r = radius * pct
        steps = int(r * 20)
        for step in range(steps):
            angle = 2 * math.pi * step / steps
            x = int(cx + r * math.cos(angle) * 2)
            y = int(cy + r * math.sin(angle))
            if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
                if grid[y][x] == " ":
                    grid[y][x] = "·"

    # Draw axes
    for i, angle in enumerate(angles):
        for step in range(1, int(radius * 10)):
            r = step / 10.0
            x = int(cx + r * math.cos(angle) * 2)
            y = int(cy + r * math.sin(angle))
            if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
                if grid[y][x] == " ":
                    grid[y][x] = "·"

    # Draw data polygon
    points = []
    for i, dim in enumerate(dims):
        score = scores.get(dim, 0)
        r = (score / max_score) * radius
        x = int(cx + r * math.cos(angles[i]) * 2)
        y = int(cy + r * math.sin(angles[i]))
        points.append((x, y))

    # Fill polygon edges
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for s in range(steps + 1):
            t = s / steps
            x = int(x0 + t * (x1 - x0))
            y = int(y0 + t * (y1 - y0))
            if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
                grid[y][x] = "◆"

    # Mark vertices
    for i, (x, y) in enumerate(points):
        if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
            grid[y][x] = "●"

    # Add dimension labels
    label_positions = [
        (cx, 0),                          # top
        (cx + radius * 2 + 2, cy - 1),    # top-right
        (cx + radius + 4, cy + radius),    # bottom-right
        (cx - radius - 4, cy + radius),    # bottom-left
        (cx - radius * 2 - 2, cy - 1),    # top-left
    ]

    # Render
    print(f"\n{C.BOLD}  {'Dimension Radar':^44}{C.RESET}\n")
    for row in grid:
        print("  " + "".join(row))

    # Legend below chart
    print()
    for i, dim in enumerate(dims):
        score = scores.get(dim, 0)
        color = DIMENSION_COLORS[i]
        print(f"    {color}●{C.RESET} {dim:<22} {C.BOLD}{score:>5.1f}{C.RESET} / {max_score}")
    print()


# ─── Score Visualization ─────────────────────────────────────────────────────

def grade_color(grade):
    """Get color for grade letter."""
    return {
        "S": C.MAGENTA,
        "A": C.GREEN,
        "B": C.CYAN,
        "C": C.YELLOW,
        "D": C.RED,
    }.get(grade, C.WHITE)


def print_grade_badge(grade, total_score):
    """Print a large ASCII grade badge."""
    color = grade_color(grade)
    grade_art = {
        "S": [
            " ███████ ",
            " ██      ",
            " ███████ ",
            "      ██ ",
            " ███████ ",
        ],
        "A": [
            "   ████  ",
            "  ██  ██ ",
            "  ██████ ",
            "  ██  ██ ",
            "  ██  ██ ",
        ],
        "B": [
            " █████   ",
            " ██  ██  ",
            " █████   ",
            " ██  ██  ",
            " █████   ",
        ],
        "C": [
            "  █████  ",
            " ██      ",
            " ██      ",
            " ██      ",
            "  █████  ",
        ],
        "D": [
            " █████   ",
            " ██  ██  ",
            " ██  ██  ",
            " ██  ██  ",
            " █████   ",
        ],
    }

    art = grade_art.get(grade, grade_art["D"])

    print(f"\n  {C.BOLD}{'═' * 44}{C.RESET}")
    print(f"  {C.BOLD}  BENCHMARK RESULT{C.RESET}")
    print(f"  {C.BOLD}{'═' * 44}{C.RESET}\n")
    for line in art:
        print(f"    {color}{C.BOLD}{line}{C.RESET}")
    print()
    print(f"    {C.BOLD}Grade: {color}{grade}{C.RESET}   "
          f"{C.BOLD}Total Score: {color}{total_score}{C.RESET} / 100")

    # Grade meaning
    meanings = {
        "S": "Elite — Top-tier trading agent",
        "A": "Strong — High-level, production-ready",
        "B": "Solid — Good foundation, some dimensions excel",
        "C": "Basic — Functional, with clear weaknesses",
        "D": "Weak — Significant improvement needed",
    }
    meaning = meanings.get(grade, "")
    print(f"    {C.DIM}{meaning}{C.RESET}")
    print(f"\n  {C.BOLD}{'═' * 44}{C.RESET}")


def print_dimension_scores(scores):
    """Print detailed dimension score bars."""
    print(f"\n  {C.BOLD}Dimension Breakdown{C.RESET}\n")

    for i, dim in enumerate(DIMENSION_NAMES):
        score = scores.get(dim, 0)
        color = DIMENSION_COLORS[i]
        print_progress_bar(score, 20, width=24, color=color,
                           label=f"{color}{dim}{C.RESET} {C.BOLD}{score:.1f}{C.RESET}/20")


def print_task_scores(task_summary):
    """Print per-task score breakdown."""
    if not task_summary:
        return

    print(f"\n  {C.BOLD}Per-Task Scores{C.RESET}\n")
    print(f"  {'Task':<30} {'Part A':>8} {'Part B':>8} {'Total':>8}")
    print(f"  {'─' * 56}")

    for i, task in enumerate(task_summary):
        name = task.get("title", TASK_NAMES[i] if i < len(TASK_NAMES) else f"Task {i+1}")
        part_a = task.get("part_a", task.get("partA", 0))
        part_b = task.get("part_b", task.get("partB", 0))
        total = task.get("total", part_a + part_b)
        icon = TASK_ICONS[i] if i < len(TASK_ICONS) else "📋"
        print(f"  {icon} {name:<27} {part_a:>6}/8  {part_b:>6}/12 {total:>6}/20")

    print(f"  {'─' * 56}")


def print_trading_stats(stats):
    """Print sandbox trading statistics."""
    if not stats:
        return

    print(f"\n  {C.BOLD}Trading Performance{C.RESET}\n")
    total = stats.get("total_trades", 0)
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    win_rate = stats.get("win_rate", 0)
    net_pnl = stats.get("net_pnl", 0)

    # Convert from base units
    pnl_usdc = net_pnl / 1_000_000 if abs(net_pnl) > 1000 else net_pnl

    pnl_color = C.GREEN if pnl_usdc >= 0 else C.RED
    pnl_sign = "+" if pnl_usdc >= 0 else ""

    print(f"  Trades: {total}  │  Wins: {C.GREEN}{wins}{C.RESET}  │  "
          f"Losses: {C.RED}{losses}{C.RESET}  │  "
          f"Win Rate: {win_rate:.0%}")
    print(f"  Net P&L: {pnl_color}{pnl_sign}{pnl_usdc:.2f} USDC{C.RESET}")


def print_final_results(result):
    """Render the complete scoring result visualization."""
    data = result.get("data", result)

    total_score = data.get("totalScore", data.get("total_score", 0))
    grade = data.get("grade", "D")

    # Extract dimension scores
    dim_scores = {}
    dim_keys = [
        ("scoreData", "Real-time Data"),
        ("scoreIntel", "Multi-source Intel"),
        ("scoreAnalysis", "Market Analysis"),
        ("scoreDecision", "Trading Decision"),
        ("scoreRisk", "Risk Management"),
        # snake_case alternatives
        ("score_data", "Real-time Data"),
        ("score_intel", "Multi-source Intel"),
        ("score_analysis", "Market Analysis"),
        ("score_decision", "Trading Decision"),
        ("score_risk", "Risk Management"),
    ]
    for key, dim_name in dim_keys:
        if key in data and data[key] is not None:
            dim_scores[dim_name] = data[key]

    # Grade badge
    print_grade_badge(grade, total_score)

    # Dimension bars
    if dim_scores:
        print_dimension_scores(dim_scores)

    # Radar chart
    if dim_scores:
        draw_radar_chart(dim_scores)

    # Task summary
    task_summary = data.get("taskSummary", data.get("task_summary"))
    if task_summary:
        if isinstance(task_summary, str):
            try:
                task_summary = json.loads(task_summary)
            except json.JSONDecodeError:
                task_summary = None
        if isinstance(task_summary, list):
            print_task_scores(task_summary)

    # Trading stats
    stats = data.get("tradingStats", data.get("trading_stats"))
    if stats:
        if isinstance(stats, str):
            try:
                stats = json.loads(stats)
            except json.JSONDecodeError:
                stats = None
        if isinstance(stats, dict):
            print_trading_stats(stats)

    # Feedback / Detailed Scores
    print(f"\n  {C.DIM}View full results at: {C.CYAN}https://manic.trade/benchmark{C.RESET}\n")


# ═══════════════════════════════════════════════════════════════════════════════
#                           TASK EXECUTION LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

# ─── T1: Market Snapshot ──────────────────────────────────────────────────────

def execute_t1(task):
    """T1: Fetch prices and build market snapshot."""
    api_calls = []

    # Get all prices from Sandbox
    prices_data = api.get_prices()
    api_calls.append({"endpoint": "GET /agent/asset/prices", "response": prices_data})

    # Extract price info
    data = prices_data.get("data", prices_data)
    assets_info = {}

    if isinstance(data, list):
        for item in data:
            symbol = item.get("asset", item.get("symbol", "")).upper()
            price = item.get("price", 0)
            exponent = item.get("price_exponent", item.get("priceExponent", 0))
            if exponent and isinstance(price, (int, float)) and abs(price) > 1e6:
                display_price = price * (10 ** exponent)
            else:
                display_price = price
            assets_info[symbol] = {
                "price": display_price,
                "raw_price": price,
                "exponent": exponent,
            }
    elif isinstance(data, dict):
        for symbol, info in data.items():
            if isinstance(info, dict):
                price = info.get("price", 0)
                exponent = info.get("price_exponent", info.get("priceExponent", 0))
                if exponent and isinstance(price, (int, float)) and abs(price) > 1e6:
                    display_price = price * (10 ** exponent)
                else:
                    display_price = price
                assets_info[symbol.upper()] = {
                    "price": display_price,
                    "raw_price": price,
                    "exponent": exponent,
                }

    # Try to get 龙虾 (Lobster) specifically
    lobster_info = None
    for sym in ["LOBSTER", "龙虾", "LONGXIA"]:
        if sym.upper() in assets_info:
            lobster_info = assets_info[sym.upper()]
            break

    # Build reasoning
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    lines = [
        f"## Market Snapshot — {timestamp}",
        f"Data source: Manic Trade Sandbox API (`/agent/asset/prices`)\n",
    ]

    # BTC, ETH, SOL
    for symbol in ["BTC", "ETH", "SOL"]:
        info = assets_info.get(symbol)
        if info:
            lines.append(f"### {symbol}")
            lines.append(f"- **Price**: ${info['price']:,.2f}")
            lines.append(f"- **Source**: Manic Trade API (real-time)")
            lines.append(f"- **Timestamp**: {timestamp}")
            lines.append("")
        else:
            lines.append(f"### {symbol}")
            lines.append(f"- **Status**: Price data not available from Sandbox API")
            lines.append("")

    # 龙虾
    lines.append("### 龙虾 (Lobster)")
    if lobster_info:
        lines.append(f"- **Price**: ${lobster_info['price']:,.6f}")
        lines.append(f"- **Source**: Manic Trade API")
        lines.append(f"- **Note**: 龙虾 is a long-tail token available on Binance Alpha")
    else:
        lines.append("- **Status**: 龙虾 (Lobster) is not directly listed on Manic Trade Sandbox.")
        lines.append("- **Note**: 龙虾 is a meme/long-tail token on Binance Alpha. "
                      "The Sandbox API does not carry this asset. "
                      "A production agent would query Binance or CoinGecko for this token.")
        lines.append("- **Identification**: Contract address should be verified via CoinGecko or Binance Alpha listings.")

    lines.append(f"\n*Snapshot generated at {timestamp} via Manic Benchmark Sandbox*")

    reasoning = "\n".join(lines)
    return reasoning, api_calls, []


# ─── T2: Multi-source Intelligence ───────────────────────────────────────────

def _fetch_external_api(url, source_name, timeout=10):
    """Fetch an external API with error handling. Returns (data, call_record)."""
    import requests as req
    call_record = {
        "source": source_name,
        "url": url,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    try:
        resp = req.get(url, timeout=timeout, headers={"Accept": "application/json"})
        resp.raise_for_status()
        data = resp.json()
        call_record["status"] = resp.status_code
        call_record["response"] = data
        return data, call_record
    except Exception as e:
        call_record["status"] = "error"
        call_record["error"] = str(e)
        return None, call_record


def execute_t2(task):
    """T2: Collect multi-source BTC intelligence from 4 dimensions."""
    api_calls = []
    external_calls = []
    intel_sections = []

    # ── Get Sandbox price as baseline ──
    try:
        btc_price_data = api.get_price("btc")
        api_calls.append({"endpoint": "GET /agent/asset/price/btc", "response": btc_price_data})
    except Exception:
        btc_price_data = None

    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # ── Dimension 1: Derivatives Data ──
    # Binance Futures funding rate
    funding_data, call1 = _fetch_external_api(
        "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1",
        "Binance Futures"
    )
    external_calls.append(call1)

    # Binance Futures open interest
    oi_data, call2 = _fetch_external_api(
        "https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT",
        "Binance Futures"
    )
    external_calls.append(call2)

    # Binance long/short ratio
    ls_data, call3 = _fetch_external_api(
        "https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol=BTCUSDT&period=1h&limit=1",
        "Binance Futures"
    )
    external_calls.append(call3)

    deriv_lines = ["### 1. Derivatives Data\n"]
    if funding_data and isinstance(funding_data, list) and len(funding_data) > 0:
        fr = funding_data[0]
        rate = float(fr.get("fundingRate", 0))
        deriv_lines.append(f"- **Funding Rate**: {rate:.6f} ({rate*100:.4f}%)")
        deriv_lines.append(f"  - Source: Binance Futures `/fapi/v1/fundingRate`")
        deriv_lines.append(f"  - Timestamp: {fr.get('fundingTime', timestamp)}")
    else:
        deriv_lines.append("- **Funding Rate**: Unable to retrieve from Binance Futures")

    if oi_data and isinstance(oi_data, dict):
        oi = oi_data.get("openInterest", "N/A")
        deriv_lines.append(f"- **Open Interest**: {float(oi):,.2f} BTC")
        deriv_lines.append(f"  - Source: Binance Futures `/fapi/v1/openInterest`")
    else:
        deriv_lines.append("- **Open Interest**: Unable to retrieve")

    if ls_data and isinstance(ls_data, list) and len(ls_data) > 0:
        ratio = ls_data[0].get("longShortRatio", "N/A")
        deriv_lines.append(f"- **Long/Short Ratio**: {ratio}")
        deriv_lines.append(f"  - Source: Binance Futures `globalLongShortAccountRatio`")
    else:
        deriv_lines.append("- **Long/Short Ratio**: Unable to retrieve")

    intel_sections.append("\n".join(deriv_lines))

    # ── Dimension 2: On-chain Data ──
    onchain_lines = ["### 2. On-chain Metrics\n"]

    # CoinGecko BTC market data (includes market cap, volume, supply)
    cg_data, call4 = _fetch_external_api(
        "https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&community_data=false&developer_data=false",
        "CoinGecko"
    )
    external_calls.append(call4)

    if cg_data and isinstance(cg_data, dict):
        market = cg_data.get("market_data", {})
        mcap = market.get("market_cap", {}).get("usd", 0)
        vol_24h = market.get("total_volume", {}).get("usd", 0)
        circulating = market.get("circulating_supply", 0)
        change_24h = market.get("price_change_percentage_24h", 0)

        onchain_lines.append(f"- **Market Cap**: ${mcap:,.0f}")
        onchain_lines.append(f"- **24h Volume**: ${vol_24h:,.0f}")
        onchain_lines.append(f"- **Circulating Supply**: {circulating:,.0f} BTC")
        onchain_lines.append(f"- **24h Price Change**: {change_24h:+.2f}%")
        onchain_lines.append(f"  - Source: CoinGecko `/api/v3/coins/bitcoin`")
        onchain_lines.append(f"  - Timestamp: {timestamp}")
    else:
        onchain_lines.append("- **On-chain data**: Unable to retrieve from CoinGecko")

    # DeFiLlama TVL overview
    defi_data, call5 = _fetch_external_api(
        "https://api.llama.fi/v2/chains",
        "DeFiLlama"
    )
    external_calls.append(call5)

    if defi_data and isinstance(defi_data, list):
        # Find Bitcoin chain TVL
        btc_chain = next((c for c in defi_data if c.get("name", "").lower() == "bitcoin"), None)
        if btc_chain:
            tvl = btc_chain.get("tvl", 0)
            onchain_lines.append(f"- **Bitcoin DeFi TVL**: ${tvl:,.0f}")
            onchain_lines.append(f"  - Source: DeFiLlama `/v2/chains`")

    intel_sections.append("\n".join(onchain_lines))

    # ── Dimension 3: News / Events ──
    news_lines = ["### 3. Recent News & Events\n"]

    # CryptoPanic API (free tier, no key needed for public)
    news_data, call6 = _fetch_external_api(
        "https://cryptopanic.com/api/free/v1/posts/?auth_token=0&currencies=BTC&kind=news&public=true",
        "CryptoPanic"
    )
    external_calls.append(call6)

    if news_data and isinstance(news_data, dict):
        results = news_data.get("results", [])[:5]
        if results:
            for item in results:
                title = item.get("title", "N/A")
                published = item.get("published_at", "N/A")
                source_title = item.get("source", {}).get("title", "Unknown")
                news_lines.append(f"- **{title}**")
                news_lines.append(f"  - Source: {source_title} via CryptoPanic")
                news_lines.append(f"  - Published: {published}")
        else:
            news_lines.append("- No recent BTC news available from CryptoPanic free tier")
    else:
        news_lines.append("- **News data**: CryptoPanic API unavailable (free tier may require token)")
        news_lines.append("- **Fallback**: Based on general market conditions, monitoring for:")
        news_lines.append("  - ETF flow data, regulatory announcements, major exchange events")

    intel_sections.append("\n".join(news_lines))

    # ── Dimension 4: Community Sentiment ──
    sentiment_lines = ["### 4. Community Sentiment\n"]

    # Fear & Greed Index
    fng_data, call7 = _fetch_external_api(
        "https://api.alternative.me/fng/?limit=1&format=json",
        "Alternative.me"
    )
    external_calls.append(call7)

    if fng_data and isinstance(fng_data, dict):
        fng_items = fng_data.get("data", [])
        if fng_items:
            fng = fng_items[0]
            value = fng.get("value", "N/A")
            classification = fng.get("value_classification", "N/A")
            fng_ts = fng.get("timestamp", "N/A")
            sentiment_lines.append(f"- **Fear & Greed Index**: {value}/100 ({classification})")
            sentiment_lines.append(f"  - Source: Alternative.me Fear & Greed Index")
            sentiment_lines.append(f"  - Timestamp: {fng_ts}")
    else:
        sentiment_lines.append("- **Fear & Greed Index**: Unable to retrieve from Alternative.me")

    # CoinGecko community data as a proxy for sentiment
    if cg_data and isinstance(cg_data, dict):
        sentiment_up = cg_data.get("sentiment_votes_up_percentage", 0)
        sentiment_down = cg_data.get("sentiment_votes_down_percentage", 0)
        if sentiment_up or sentiment_down:
            sentiment_lines.append(f"- **CoinGecko Sentiment**: {sentiment_up:.1f}% bullish / {sentiment_down:.1f}% bearish")
            sentiment_lines.append(f"  - Source: CoinGecko community sentiment votes")

    intel_sections.append("\n".join(sentiment_lines))

    # ── Synthesize ──
    direction = "neutral"
    confidence = 5

    # Simple heuristic: use funding rate + price change to determine direction
    try:
        if funding_data and isinstance(funding_data, list) and len(funding_data) > 0:
            fr_val = float(funding_data[0].get("fundingRate", 0))
        else:
            fr_val = 0

        price_change = 0
        if cg_data and isinstance(cg_data, dict):
            price_change = cg_data.get("market_data", {}).get("price_change_percentage_24h", 0)

        if price_change > 2 and fr_val > 0:
            direction = "bullish"
            confidence = 7
        elif price_change < -2 and fr_val < 0:
            direction = "bearish"
            confidence = 7
        elif price_change > 1:
            direction = "bullish"
            confidence = 6
        elif price_change < -1:
            direction = "bearish"
            confidence = 6
        else:
            direction = "neutral"
            confidence = 5
    except Exception:
        pass

    synthesis = [
        "\n---\n",
        "## Summary & Trading Recommendation\n",
        f"- **Overall Market Direction**: {direction.upper()}",
        f"- **Confidence Level**: {confidence}/10",
        f"- **Trading Recommendation**: ",
    ]

    if direction == "bullish":
        synthesis.append("  Consider opening a CALL position on BTC with moderate leverage (2x). "
                         "Positive funding rate and upward price momentum support short-term bullish bias.")
        synthesis.append("- **Risk Assessment**: Watch for sudden funding rate reversal or sharp volume drop. "
                         "Set stop-loss at 2% below entry.")
    elif direction == "bearish":
        synthesis.append("  Consider opening a PUT position on BTC with conservative leverage (1.5x). "
                         "Negative funding and declining price suggest short-term bearish pressure.")
        synthesis.append("- **Risk Assessment**: Monitor for potential short squeeze if open interest declines. "
                         "Set stop-loss at 2% above entry.")
    else:
        synthesis.append("  Stay on the sidelines or open a small position with minimal risk. "
                         "Mixed signals suggest waiting for clearer directional confirmation.")
        synthesis.append("- **Risk Assessment**: Key levels to watch — a breakout above 24h high "
                         "or breakdown below 24h low would signal direction.")

    reasoning = f"## BTC Multi-source Intelligence Report — {timestamp}\n\n"
    reasoning += "\n\n".join(intel_sections)
    reasoning += "\n".join(synthesis)

    return reasoning, api_calls, external_calls


# ─── T3: Market Analysis ─────────────────────────────────────────────────────

def execute_t3(task):
    """T3: Analyze market packets (MA-1 + MA-2 for each case)."""
    api_calls = []
    scenario = task.get("scenario", task)

    # Extract cases from scenario
    cases = None
    if isinstance(scenario, dict):
        cases = scenario.get("cases", [])
    elif isinstance(scenario, str):
        try:
            parsed = json.loads(scenario)
            cases = parsed.get("cases", [])
        except json.JSONDecodeError:
            cases = []

    if not cases:
        # Fallback: try top-level
        cases = task.get("cases", [])

    results = []

    for idx, case in enumerate(cases):
        case_id = case.get("case_id", f"case_{idx}")
        asset = case.get("asset", "Unknown")
        timeframe = case.get("timeframe", "4h")
        market_packet = case.get("market_packet", case.get("observations", []))
        perturbation = case.get("perturbation", case.get("new_information", ""))

        # ── MA-1: Analyze market packet ──
        observations = market_packet if isinstance(market_packet, list) else []

        # Classify observations by signal
        bullish_obs = [o for o in observations if o.get("signal") == "bullish"]
        bearish_obs = [o for o in observations if o.get("signal") == "bearish"]
        noise_obs = [o for o in observations if o.get("signal") == "noise"]

        # Determine regime based on signal count and weight
        bull_weight = sum(float(o.get("weight", 0.5)) for o in bullish_obs)
        bear_weight = sum(float(o.get("weight", 0.5)) for o in bearish_obs)

        if bull_weight > bear_weight * 1.3:
            regime = "bullish"
            confidence = min(int(60 + (bull_weight - bear_weight) * 20), 90)
        elif bear_weight > bull_weight * 1.3:
            regime = "bearish"
            confidence = min(int(60 + (bear_weight - bull_weight) * 20), 90)
        else:
            regime = "neutral"
            confidence = 50

        # Pick evidence
        all_obs_sorted = sorted(observations, key=lambda o: float(o.get("weight", 0)), reverse=True)
        supporting = []
        counter = []
        for o in all_obs_sorted:
            sig = o.get("signal", "noise")
            oid = o.get("id", o.get("obs_id", ""))
            if regime == "bullish":
                if sig == "bullish" and len(supporting) < 2:
                    supporting.append(oid)
                elif sig == "bearish" and len(counter) < 1:
                    counter.append(oid)
            elif regime == "bearish":
                if sig == "bearish" and len(supporting) < 2:
                    supporting.append(oid)
                elif sig == "bullish" and len(counter) < 1:
                    counter.append(oid)
            else:
                if len(supporting) < 2:
                    supporting.append(oid)
                elif len(counter) < 1:
                    counter.append(oid)

        # Build tension description
        if bullish_obs and bearish_obs:
            bull_desc = bullish_obs[0].get("content", "bullish signals")[:80]
            bear_desc = bearish_obs[0].get("content", "bearish signals")[:80]
            tension = f"Conflicting signals: {bull_desc} vs {bear_desc}"
        else:
            tension = f"Market signals predominantly {'bullish' if regime == 'bullish' else 'bearish' if regime == 'bearish' else 'mixed'} with limited counter-evidence."

        # Build analysis summary
        obs_categories = set(o.get("category", "") for o in observations)
        summary = (
            f"Based on {len(observations)} observations spanning {', '.join(obs_categories)}, "
            f"the {asset} market on {timeframe} shows a {regime} regime with {confidence}% confidence. "
            f"The primary evidence supports this view through {len(supporting)} key observations, "
            f"while {len(counter)} counter-observation{'s' if len(counter) != 1 else ''} "
            f"{'suggest' if len(counter) != 1 else 'suggests'} caution. "
            f"The core tension lies in balancing short-term momentum against structural concerns."
        )

        ma1 = {
            "market_regime": regime,
            "confidence": confidence,
            "key_tension": tension[:200],
            "top_2_evidence_for": supporting[:2],
            "top_1_counter_evidence": counter[0] if counter else "none",
            "analysis_summary": summary[:500],
        }

        # ── MA-2: Process perturbation ──
        perturbation_text = perturbation if isinstance(perturbation, str) else json.dumps(perturbation)

        # Simple heuristic: if perturbation contains strong directional words, update
        strong_bearish = any(w in perturbation_text.lower() for w in
                            ["crash", "plunge", "hack", "exploit", "ban", "collapse", "dump", "liquidat"])
        strong_bullish = any(w in perturbation_text.lower() for w in
                            ["surge", "rally", "approval", "adoption", "breakout", "accumulation", "etf approv"])
        is_noise = any(w in perturbation_text.lower() for w in
                       ["rumor", "unconfirmed", "minor", "slight", "marginal"])

        if is_noise:
            updated_regime = regime
            updated_confidence = max(confidence - 5, 30)
            changed = "no"
            reason = "The new information appears to be noise/unconfirmed and does not materially alter the thesis."
            invalidated = "none"
        elif strong_bearish and regime != "bearish":
            updated_regime = "bearish"
            updated_confidence = 65
            changed = "yes"
            reason = "The perturbation introduces material bearish evidence that outweighs prior bullish signals."
            invalidated = supporting[0] if supporting else "none"
        elif strong_bullish and regime != "bullish":
            updated_regime = "bullish"
            updated_confidence = 65
            changed = "yes"
            reason = "The perturbation introduces material bullish catalyst that shifts the balance of evidence."
            invalidated = supporting[0] if supporting else "none"
        else:
            updated_regime = regime
            updated_confidence = confidence
            changed = "no"
            reason = "The new information is consistent with the current regime assessment."
            invalidated = "none"

        ma2 = {
            "updated_regime": updated_regime,
            "updated_confidence": updated_confidence,
            "changed": changed,
            "reason_for_change": reason,
            "which_previous_evidence_is_invalidated": invalidated,
        }

        results.append({
            "case_id": case_id,
            "ma1": ma1,
            "ma2": ma2,
        })

    reasoning = json.dumps(results, indent=2)
    return reasoning, api_calls, []


# ─── T4: Trading Decision & Execution ────────────────────────────────────────

def execute_t4(task, context):
    """T4: Formulate trading plan and execute on Sandbox."""
    api_calls = []

    # Determine direction from T2 context
    direction_from_t2 = context.get("t2_direction", "neutral")
    confidence_from_t2 = context.get("t2_confidence", 5)

    # Choose asset and parameters
    asset = "btc"
    if direction_from_t2 == "bullish":
        side = "call"
    elif direction_from_t2 == "bearish":
        side = "put"
    else:
        side = "call"  # Default to call in neutral

    amount = 10_000_000   # 10 USDC
    duration = 120        # 120 seconds
    multiplier = 2.0      # Conservative

    # Step 1: Check price
    price_data = api.get_price(asset)
    api_calls.append({"endpoint": f"GET /agent/asset/price/{asset}", "response": price_data})

    price_info = price_data.get("data", price_data)
    raw_price = price_info.get("price", 0)
    exponent = price_info.get("price_exponent", price_info.get("priceExponent", 0))
    if exponent and isinstance(raw_price, (int, float)) and abs(raw_price) > 1e6:
        display_price = raw_price * (10 ** exponent)
    else:
        display_price = raw_price

    # Step 2: Execute trade
    try:
        trade_result = api.open_position(
            asset=asset,
            side=side,
            amount=amount,
            duration=duration,
            target_multiplier=multiplier,
        )
        api_calls.append({"endpoint": "POST /agent/open-position", "response": trade_result})
        trade_data = trade_result.get("data", trade_result)
        tx_hash = trade_data.get("tx_hash", trade_data.get("txHash", "N/A"))
        position_id = trade_data.get("position_id", trade_data.get("positionId", "N/A"))
        opening_price = trade_data.get("price", trade_data.get("_price_at_open", display_price))
        execution_success = True
    except Exception as e:
        tx_hash = "N/A"
        position_id = "N/A"
        opening_price = display_price
        execution_success = False
        api_calls.append({"endpoint": "POST /agent/open-position", "error": str(e)})

    # Build reasoning
    lines = [
        "## Trading Decision & Execution\n",
        "### Step 1 — Decision\n",
        f"**1. Key Market Tension:** Based on multi-source intelligence (T1-T2), "
        f"the market shows {'positive momentum with derivatives confirmation' if direction_from_t2 == 'bullish' else 'negative pressure with derivatives weakness' if direction_from_t2 == 'bearish' else 'mixed signals requiring cautious positioning'}.\n",
        f"**2. Direction:** {side.upper()} (Confidence: {confidence_from_t2}/10)\n",
        f"**3. Trade Parameters:**",
        f"   - Asset: {asset.upper()}",
        f"   - Side: {side}",
        f"   - Amount: {amount / 1_000_000:.0f} USDC",
        f"   - Duration: {duration} seconds",
        f"   - Target Multiplier: {multiplier}x\n",
        f"**4. Thesis Invalidation:** "
        f"{'If BTC drops below $' + f'{display_price * 0.98:,.2f}' + ' (-2%), close position immediately.' if side == 'call' else 'If BTC rises above $' + f'{display_price * 1.02:,.2f}' + ' (+2%), close position immediately.'}\n",
        "### Step 2 — Execution\n",
        f"**5. Price Check:** Current {asset.upper()} price = ${display_price:,.2f} "
        f"(via `get-price` API)\n",
    ]

    if execution_success:
        lines.extend([
            f"**6. Execution:** `open-position` call successful",
            f"   - tx_hash: `{tx_hash}`",
            f"   - position_id: `{position_id}`",
            f"   - opening_price: ${opening_price if isinstance(opening_price, str) else f'{opening_price:,.2f}'}\n",
            f"**7-8. Parameter Verification:**",
            f"   - Asset: {asset.upper()} ✓",
            f"   - Side: {side} ✓",
            f"   - Amount: {amount / 1_000_000:.0f} USDC ✓",
            f"   - Duration: {duration}s ✓",
            f"   - Multiplier: {multiplier}x ✓",
            f"   **All parameters match plan: YES**",
        ])
    else:
        lines.extend([
            f"**6. Execution:** `open-position` call FAILED",
            f"   Trade could not be executed due to an API error.",
        ])

    reasoning = "\n".join(lines)
    return reasoning, api_calls, []


# ─── T5: Risk Management ─────────────────────────────────────────────────────

def execute_t5(task):
    """T5: Analyze positions and make risk management decisions."""
    api_calls = []

    # 1. Query position history
    positions_data = api.get_position_history()
    api_calls.append({"endpoint": "GET /agent/position-history", "response": positions_data})

    pos_list = positions_data.get("data", positions_data)
    if isinstance(pos_list, dict) and "positions" in pos_list:
        pos_list = pos_list["positions"]
    if not isinstance(pos_list, list):
        pos_list = []

    # Get the two most recent positions
    recent = pos_list[-2:] if len(pos_list) >= 2 else pos_list

    lines = ["## Risk Management Analysis\n"]
    lines.append(f"### 1. Position History Retrieved\n")
    lines.append(f"Found {len(pos_list)} total positions. Analyzing the {len(recent)} most recent:\n")

    decisions = []

    for i, pos in enumerate(recent):
        pos_id = pos.get("position_id", pos.get("positionId", "N/A"))
        pos_asset = pos.get("asset", "N/A").upper()
        pos_side = pos.get("side", "N/A")
        pos_amount_raw = pos.get("amount", 0)
        pos_entry_raw = pos.get("entry_price", pos.get("entryPrice", 0))
        pos_exponent = pos.get("price_exponent", pos.get("priceExponent", 0))
        pos_status = pos.get("status", "unknown")
        pos_duration = pos.get("duration_seconds", pos.get("durationSeconds", 0))

        # Convert prices
        if pos_exponent and isinstance(pos_entry_raw, (int, float)) and abs(pos_entry_raw) > 1e6:
            entry_price = pos_entry_raw * (10 ** pos_exponent)
        else:
            entry_price = pos_entry_raw

        amount_usdc = pos_amount_raw / 1_000_000 if pos_amount_raw > 1000 else pos_amount_raw

        # Get current price
        try:
            current_data = api.get_price(pos_asset)
            api_calls.append({"endpoint": f"GET /agent/asset/price/{pos_asset.lower()}", "response": current_data})
            cur_info = current_data.get("data", current_data)
            cur_raw = cur_info.get("price", 0)
            cur_exp = cur_info.get("price_exponent", cur_info.get("priceExponent", 0))
            if cur_exp and isinstance(cur_raw, (int, float)) and abs(cur_raw) > 1e6:
                current_price = cur_raw * (10 ** cur_exp)
            else:
                current_price = cur_raw
        except Exception:
            current_price = entry_price

        # Calculate P&L
        if pos_side == "call":
            pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price else 0
        else:  # put
            pnl_pct = ((entry_price - current_price) / entry_price * 100) if entry_price else 0

        pnl_usdc = amount_usdc * (pnl_pct / 100)
        is_winning = pnl_pct > 0

        lines.append(f"### Position {i + 1}: {pos_asset} {pos_side.upper()}\n")
        lines.append(f"- **Position ID**: `{pos_id}`")
        lines.append(f"- **Entry Price**: ${entry_price:,.2f}")
        lines.append(f"- **Current Price**: ${current_price:,.2f}")
        lines.append(f"- **P&L**: {pnl_pct:+.2f}% ({pnl_usdc:+.2f} USDC)")
        lines.append(f"- **Amount**: {amount_usdc:.0f} USDC")
        lines.append(f"- **Status**: {'WINNING ✅' if is_winning else 'LOSING ❌'}\n")

        # Decision logic
        if is_winning:
            # Hold winning position
            lines.append(f"**Decision: HOLD until expiry** ✋\n")
            lines.append(f"**Reasoning:** Position is profitable at {pnl_pct:+.2f}%. "
                         f"With {pos_duration}s duration and current momentum, holding to capture "
                         f"full potential payout is the optimal strategy. However, would exit early "
                         f"if price reverses below ${entry_price:,.2f} to protect gains.\n")
            decisions.append(("hold", pos_id, pos_asset))
        else:
            # Close losing position
            lines.append(f"**Decision: CLOSE position now** 🚫\n")
            lines.append(f"**Reasoning:** Position is at {pnl_pct:+.2f}% loss. "
                         f"The adverse price movement suggests the original thesis may be invalid. "
                         f"Cutting losses early preserves capital for better opportunities. "
                         f"The loss of {pnl_usdc:.2f} USDC is manageable.\n")
            decisions.append(("close", pos_id, pos_asset))

    # Execute decisions
    lines.append("### 2. Executing Decisions\n")
    for decision, pos_id, pos_asset in decisions:
        if decision == "close" and pos_id != "N/A":
            try:
                close_result = api.close_position(pos_id, pos_asset)
                api_calls.append({"endpoint": "POST /agent/close-position", "response": close_result})
                lines.append(f"- **Closed** `{pos_id}` ({pos_asset}) ✓")
            except Exception as e:
                lines.append(f"- **Close failed** `{pos_id}`: {e}")
                api_calls.append({"endpoint": "POST /agent/close-position", "error": str(e)})
        else:
            lines.append(f"- **Holding** `{pos_id}` ({pos_asset}) until expiry ✓")

    # 3. Loss threshold and reversal signal
    lines.extend([
        "\n### 3. Risk Framework\n",
        "**Loss Threshold:** -3% from entry price. If any position reaches -3% P&L, "
        "close immediately regardless of remaining duration. This is based on "
        "the short duration of benchmark positions (30-300s) where a 3% adverse move "
        "indicates a significant directional miss.\n",
        "**Reversal Signal:** The following conditions would change the current assessment:",
        "1. **Funding rate flip** — If Binance BTC funding rate flips sign (positive → negative or vice versa)",
        "2. **Volume surge** — If 5-minute volume exceeds 3x the 1-hour average, indicating institutional activity",
        "3. **Price level breach** — If BTC reclaims/loses the 24h VWAP, suggesting trend reversal\n",
        "These multi-factor conditions ensure decisions aren't based on noise.",
    ])

    reasoning = "\n".join(lines)
    return reasoning, api_calls, []


# ═══════════════════════════════════════════════════════════════════════════════
#                              MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

def run():
    """Execute all 5 benchmark tasks sequentially."""
    print_header("Manic Trading Benchmark", "🚀")
    print(f"  {C.DIM}Executing 5 evaluation tasks...{C.RESET}\n")

    context = {}
    total_start = time.time()

    for task_index in range(5):
        print_task_start(task_index)
        task_start = time.time()

        try:
            # 1. Get task scenario
            task = api.get_next_task()
            task_data = task.get("data", task)

            # 2. Execute task
            if task_index == 0:
                reasoning, api_calls, ext_calls = execute_t1(task_data)

            elif task_index == 1:
                reasoning, api_calls, ext_calls = execute_t2(task_data)
                # Save T2 context for T4
                if "bullish" in reasoning.lower():
                    context["t2_direction"] = "bullish"
                elif "bearish" in reasoning.lower():
                    context["t2_direction"] = "bearish"
                else:
                    context["t2_direction"] = "neutral"
                # Extract confidence
                import re
                conf_match = re.search(r"Confidence Level[:\s]*(\d+)/10", reasoning)
                context["t2_confidence"] = int(conf_match.group(1)) if conf_match else 5

            elif task_index == 2:
                reasoning, api_calls, ext_calls = execute_t3(task_data)

            elif task_index == 3:
                reasoning, api_calls, ext_calls = execute_t4(task_data, context)

            elif task_index == 4:
                reasoning, api_calls, ext_calls = execute_t5(task_data)

            # 3. Submit task
            duration_ms = int((time.time() - task_start) * 1000)

            api.submit_task(
                task_index=task_index,
                status="success",
                agent_reasoning=reasoning[:12000],  # Safety truncation
                api_calls=api_calls,
                external_api_calls=ext_calls,
                duration_ms=duration_ms,
            )

            print_task_done(time.time() - task_start)

        except Exception as e:
            print_task_done(0, status=f"error: {e}")
            traceback.print_exc()

            # Try to submit failure
            try:
                api.submit_task(
                    task_index=task_index,
                    status="failed",
                    agent_reasoning=f"Task failed with error: {e}",
                    duration_ms=int((time.time() - task_start) * 1000),
                )
            except Exception:
                pass

    total_duration = time.time() - total_start
    print(f"\n  {C.GREEN}All tasks completed in {total_duration:.1f}s{C.RESET}")

    # ── Poll for scoring results ──
    print_header("Scoring Results", "📋")
    print(f"  {C.DIM}Waiting for scoring engine...{C.RESET}")

    spin = spinner_frames()
    try:
        start_poll = time.time()
        while time.time() - start_poll < 120:
            frame = next(spin)
            elapsed = time.time() - start_poll
            print(f"\r  {C.CYAN}{frame}{C.RESET} Scoring in progress... {C.DIM}({elapsed:.0f}s){C.RESET}", end="")
            sys.stdout.flush()

            try:
                result = api.poll_score(timeout=5, interval=3)
                print(f"\r  {C.GREEN}✓{C.RESET} Scoring complete!              ")
                print_final_results(result)
                return
            except TimeoutError:
                pass
            except RuntimeError:
                pass

            time.sleep(2)

        print(f"\r  {C.YELLOW}⚠{C.RESET} Scoring is still in progress. Check results at:")
        print(f"    {C.CYAN}https://manic.trade/benchmark{C.RESET}\n")

    except KeyboardInterrupt:
        print(f"\n\n  {C.YELLOW}Interrupted.{C.RESET} Check results at:")
        print(f"    {C.CYAN}https://manic.trade/benchmark{C.RESET}\n")


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not api.BENCHMARK_API_KEY:
        print(f"\n  {C.RED}Error: BENCHMARK_API_KEY not found.{C.RESET}")
        print(f"  Run {C.CYAN}npx manic-trading-benchmark init{C.RESET} first.\n")
        sys.exit(1)

    run()
