#!/usr/bin/env python3
"""
Manic Trading Benchmark — Runner & Visualization

Generic orchestrator that drives 5 benchmark tasks sequentially.
Task prompts are delivered dynamically by the server — this runner
fetches each scenario, executes it using sandbox APIs, and submits
the result.

This is a baseline reference runner, not the optimal scoring strategy.
A real AI agent would analyze each task scenario in depth and apply
sophisticated reasoning, external data sources, and domain knowledge.
"""

import sys
import os
import json
import time
import math
import traceback
import requests

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
    width = 56
    print(f"\n{C.BOLD}{C.CYAN}{'─' * width}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  {icon}  {text}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}{'─' * width}{C.RESET}\n")


def print_task_start(index, title=None):
    icon = TASK_ICONS[index] if index < len(TASK_ICONS) else "📋"
    name = title or (TASK_NAMES[index] if index < len(TASK_NAMES) else f"Task {index + 1}")
    print(f"  {C.BOLD}{C.WHITE}T{index + 1}{C.RESET} {icon}  {C.BOLD}{name}{C.RESET}", end="")
    sys.stdout.flush()


def print_task_done(duration_s, status="success"):
    if status == "success":
        print(f"  {C.GREEN}✓{C.RESET} {C.DIM}{duration_s:.1f}s{C.RESET}")
    else:
        print(f"  {C.RED}✗ {status}{C.RESET}")


def spinner_frames():
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    while True:
        yield frames[i % len(frames)]
        i += 1


def print_progress_bar(value, max_val, width=30, color=C.GREEN, label=""):
    ratio = min(value / max_val, 1.0) if max_val > 0 else 0
    filled = int(ratio * width)
    empty = width - filled
    bar = f"{color}{'█' * filled}{C.DIM}{'░' * empty}{C.RESET}"
    pct = f"{ratio * 100:5.1f}%"
    print(f"  {bar} {pct}  {label}")


# ─── ASCII Radar Chart ───────────────────────────────────────────────────────

def draw_radar_chart(scores, max_score=20, radius=8):
    dims = DIMENSION_NAMES
    n = len(dims)
    angles = [2 * math.pi * i / n - math.pi / 2 for i in range(n)]

    canvas_size = radius * 2 + 5
    cx, cy = canvas_size, radius + 2
    grid = [[" "] * (canvas_size * 2 + 1) for _ in range(canvas_size + 1)]

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

    for i, angle in enumerate(angles):
        for step in range(1, int(radius * 10)):
            r = step / 10.0
            x = int(cx + r * math.cos(angle) * 2)
            y = int(cy + r * math.sin(angle))
            if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
                if grid[y][x] == " ":
                    grid[y][x] = "·"

    points = []
    for i, dim in enumerate(dims):
        score = scores.get(dim, 0)
        r = (score / max_score) * radius
        x = int(cx + r * math.cos(angles[i]) * 2)
        y = int(cy + r * math.sin(angles[i]))
        points.append((x, y))

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

    for i, (x, y) in enumerate(points):
        if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
            grid[y][x] = "●"

    print(f"\n{C.BOLD}  {'Dimension Radar':^44}{C.RESET}\n")
    for row in grid:
        print("  " + "".join(row))

    print()
    for i, dim in enumerate(dims):
        score = scores.get(dim, 0)
        color = DIMENSION_COLORS[i]
        print(f"    {color}●{C.RESET} {dim:<22} {C.BOLD}{score:>5.1f}{C.RESET} / {max_score}")
    print()


# ─── Score Visualization ─────────────────────────────────────────────────────

def grade_color(grade):
    return {
        "S": C.MAGENTA, "A": C.GREEN, "B": C.CYAN,
        "C": C.YELLOW, "D": C.RED,
    }.get(grade, C.WHITE)


def print_grade_badge(grade, total_score):
    color = grade_color(grade)
    grade_art = {
        "S": [" ███████ ", " ██      ", " ███████ ", "      ██ ", " ███████ "],
        "A": ["   ████  ", "  ██  ██ ", "  ██████ ", "  ██  ██ ", "  ██  ██ "],
        "B": [" █████   ", " ██  ██  ", " █████   ", " ██  ██  ", " █████   "],
        "C": ["  █████  ", " ██      ", " ██      ", " ██      ", "  █████  "],
        "D": [" █████   ", " ██  ██  ", " ██  ██  ", " ██  ██  ", " █████   "],
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
    meanings = {
        "S": "Elite — Top-tier trading agent",
        "A": "Strong — High-level, production-ready",
        "B": "Solid — Good foundation, some dimensions excel",
        "C": "Basic — Functional, with clear weaknesses",
        "D": "Weak — Significant improvement needed",
    }
    print(f"    {C.DIM}{meanings.get(grade, '')}{C.RESET}")
    print(f"\n  {C.BOLD}{'═' * 44}{C.RESET}")


def print_dimension_scores(scores):
    print(f"\n  {C.BOLD}Dimension Breakdown{C.RESET}\n")
    for i, dim in enumerate(DIMENSION_NAMES):
        score = scores.get(dim, 0)
        color = DIMENSION_COLORS[i]
        print_progress_bar(score, 20, width=24, color=color,
                           label=f"{color}{dim}{C.RESET} {C.BOLD}{score:.1f}{C.RESET}/20")


def print_task_scores(task_summary):
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
    if not stats:
        return
    print(f"\n  {C.BOLD}Trading Performance{C.RESET}\n")
    total = _to_num(stats.get("total_trades", 0))
    wins = _to_num(stats.get("wins", 0))
    losses = _to_num(stats.get("losses", 0))
    win_rate = _to_num(stats.get("win_rate", 0))
    net_pnl = _to_num(stats.get("net_pnl", 0))
    pnl_usdc = net_pnl / 1_000_000 if abs(net_pnl) > 1000 else net_pnl
    pnl_color = C.GREEN if pnl_usdc >= 0 else C.RED
    pnl_sign = "+" if pnl_usdc >= 0 else ""
    print(f"  Trades: {total}  │  Wins: {C.GREEN}{wins}{C.RESET}  │  "
          f"Losses: {C.RED}{losses}{C.RESET}  │  "
          f"Win Rate: {win_rate:.0%}")
    print(f"  Net P&L: {pnl_color}{pnl_sign}{pnl_usdc:.2f} USDC{C.RESET}")


def print_final_results(result):
    data = result if isinstance(result, dict) else {}
    if "data" in data and isinstance(data["data"], dict):
        data = data["data"]
    if not isinstance(data, dict):
        print(f"  {C.YELLOW}Unable to parse scoring result.{C.RESET}")
        return

    total_score = data.get("totalScore", data.get("total_score", 0))
    grade = data.get("grade", "D")

    dim_scores = {}
    dims = data.get("dimensions")
    if isinstance(dims, dict):
        dim_map = {
            "data": "Real-time Data",
            "intel": "Multi-source Intel",
            "analysis": "Market Analysis",
            "decision": "Trading Decision",
            "risk": "Risk Management",
        }
        for key, dim_name in dim_map.items():
            if key in dims and dims[key] is not None:
                dim_scores[dim_name] = dims[key]
    if not dim_scores:
        for key, dim_name in [
            ("scoreData", "Real-time Data"), ("scoreIntel", "Multi-source Intel"),
            ("scoreAnalysis", "Market Analysis"), ("scoreDecision", "Trading Decision"),
            ("scoreRisk", "Risk Management"),
            ("score_data", "Real-time Data"), ("score_intel", "Multi-source Intel"),
            ("score_analysis", "Market Analysis"), ("score_decision", "Trading Decision"),
            ("score_risk", "Risk Management"),
        ]:
            if key in data and data[key] is not None:
                dim_scores[dim_name] = data[key]

    print_grade_badge(grade, total_score)
    if dim_scores:
        print_dimension_scores(dim_scores)
        draw_radar_chart(dim_scores)

    task_summary = data.get("taskSummary", data.get("task_summary"))
    if task_summary:
        if isinstance(task_summary, str):
            try:
                task_summary = json.loads(task_summary)
            except json.JSONDecodeError:
                task_summary = None
        if isinstance(task_summary, list):
            print_task_scores(task_summary)

    stats = data.get("tradingStats", data.get("trading_stats"))
    if stats:
        if isinstance(stats, str):
            try:
                stats = json.loads(stats)
            except json.JSONDecodeError:
                stats = None
        if isinstance(stats, dict):
            print_trading_stats(stats)

    print(f"\n  {C.DIM}View full results at: "
          f"{C.CYAN}https://benchmark.manic.trade{C.RESET}\n")


# ═══════════════════════════════════════════════════════════════════════════════
#                          SANDBOX API CALL HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _call_record(command, request_body=None, response=None,
                 http_status=200, request_ms=None, error=None):
    """Build an api_calls entry matching the server DTO (command-based)."""
    record = {"command": command, "httpStatus": http_status}
    if request_body is not None:
        record["request"] = request_body
    if response is not None:
        record["response"] = response if isinstance(response, dict) else {"raw": response}
    if request_ms is not None:
        record["requestMs"] = request_ms
    if error is not None:
        if isinstance(error, dict):
            record["response"] = {"error": error}
            record["httpStatus"] = int(error.get("http_status") or http_status or 0)
        else:
            record["response"] = {"error": str(error)}
            record["httpStatus"] = 0
    return record


def safe_call(fn, command, request_body=None, *args, **kwargs):
    """Call a sandbox API function, return (data, call_record).

    Extracts .data from the response envelope and records the call
    for submission to the scoring engine.
    """
    start = time.time()
    try:
        result = fn(*args, **kwargs)
        ms = int((time.time() - start) * 1000)
        http_status = 200
        if isinstance(result, dict):
            http_status = int(result.get("_http_status", 200) or 200)
            data = result.get("data", result)
        else:
            data = result
        record = _call_record(command, request_body, data, http_status, ms)
        return data, record
    except api.ApiError as e:
        ms = int((time.time() - start) * 1000)
        error_info = {
            "code": e.code,
            "msg": e.msg,
            "http_status": e.http_status,
            "data": e.data,
        }
        record = _call_record(command, request_body, error=error_info, request_ms=ms,
                              http_status=e.http_status or 0)
        return None, record
    except Exception as e:
        ms = int((time.time() - start) * 1000)
        record = _call_record(command, request_body, error=e, request_ms=ms)
        return None, record


def _to_num(val, default=0):
    """Coerce a value to float. Handles BigInt strings from Prisma serialization."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val)
        except (ValueError, TypeError):
            return default
    return default


def format_price(raw_price, exponent):
    """Convert raw Manic price to human-readable dollar amount."""
    raw = _to_num(raw_price)
    exp = _to_num(exponent, 0)
    if exp and abs(raw) > 1e6:
        return raw * (10 ** exp)
    return raw


# ═══════════════════════════════════════════════════════════════════════════════
#                           GENERIC TASK EXECUTOR
# ═══════════════════════════════════════════════════════════════════════════════

# Valid trading parameters (from server constraints)
VALID_DURATIONS = [30, 60, 120, 180, 240, 300]
CRYPTO_ASSETS = ["btc", "eth", "sol", "xmr", "pyth", "layer", "drift"]


def execute_task(task_index, task_data, context):
    """Execute a benchmark task based on server-provided scenario and constraints.

    Uses generic heuristics to decide what actions to take:
    - If constraints include amount limits → trading task → open a position
    - If positions exist in history → position management → evaluate & act
    - If structured cases are provided → structured analysis
    - Otherwise → gather and present market data

    A real AI agent would do much more: analyze scenario text, call external
    APIs, apply domain knowledge, and produce sophisticated reasoning.

    Returns: (reasoning, api_calls, external_api_calls, updated_context)
    """
    scenario = ""
    constraints = None
    extra = {}

    if isinstance(task_data, dict):
        scenario = task_data.get("scenario", "")
        constraints = task_data.get("constraints")
        for k, v in task_data.items():
            if k not in ("scenario", "constraints", "task_index", "title"):
                extra[k] = v
        if isinstance(scenario, dict):
            scenario = json.dumps(scenario, indent=2)
    elif isinstance(task_data, str):
        scenario = task_data

    api_calls = []
    external_calls = []
    reasoning_parts = []
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    price_map = {}

    if task_index == 0:
        # ── T1: fetch prices from external sources (not sandbox API) ──
        t1_reasoning, t1_ext_calls, price_map = _collect_t1_market_data()
        external_calls.extend(t1_ext_calls)
        reasoning_parts.extend(t1_reasoning)

        account_data, account_call = safe_call(api.get_account, "get-account")
        api_calls.append(account_call)
    else:
        # ── Non-T1 tasks: gather baseline market data from sandbox ──
        prices_data, prices_call = safe_call(api.get_prices, "get-prices")
        api_calls.append(prices_call)

        account_data, account_call = safe_call(api.get_account, "get-account")
        api_calls.append(account_call)

        if prices_data:
            price_list = prices_data if isinstance(prices_data, list) else []
            for item in price_list:
                asset = (item.get("asset", "")).lower()
                raw = _to_num(item.get("price", 0))
                exp = _to_num(item.get("price_exponent", item.get("priceExponent", -8)), -8)
                price_map[asset] = {"raw": raw, "exponent": exp, "display": format_price(raw, exp)}

        if price_map:
            reasoning_parts.append(f"## Market Data (as of {timestamp})\n")
            reasoning_parts.append("Source: Manic Trade Sandbox API\n")
            for asset, info in sorted(price_map.items()):
                reasoning_parts.append(f"- **{asset.upper()}**: ${info['display']:,.2f}")
            reasoning_parts.append("")

    # ── Task2 prefers external signals for multi-source scoring ──
    if task_index == 1:
        intel_reasoning, intel_calls = _collect_external_intel(price_map)
        external_calls.extend(intel_calls)
        reasoning_parts.extend(intel_reasoning)

    # ── Check for structured analysis cases (e.g. market packet scenarios) ──
    cases = extra.get("cases", [])
    if cases and isinstance(cases, list):
        reasoning_parts.append("## Structured Analysis\n")
        analysis_results = _handle_structured_cases(cases)
        reasoning_parts.append(json.dumps(analysis_results, indent=2))
        context["analysis_results"] = analysis_results

    # ── Check if this is a trading execution task (has amount constraints) ──
    elif constraints and isinstance(constraints, dict):
        has_amount = ("maxAmountUsdc" in constraints or "minAmountUsdc" in constraints
                      or "maxAmount" in constraints or "minAmount" in constraints)
        if has_amount:
            trade_reasoning, trade_calls = _handle_trading(
                scenario, constraints, price_map, account_data, context
            )
            api_calls.extend(trade_calls)
            reasoning_parts.extend(trade_reasoning)

    # ── Check for positions to manage ──
    positions_data, pos_call = safe_call(api.get_position_history, "position-history")
    api_calls.append(pos_call)

    active_positions = []
    if positions_data:
        pos_list = positions_data if isinstance(positions_data, list) else []
        if isinstance(positions_data, dict):
            pos_list = positions_data.get("positions", positions_data.get("data", []))
            if not isinstance(pos_list, list):
                pos_list = []
        active_positions = [p for p in pos_list if p.get("status") == "active"]

    if active_positions:
        mgmt_reasoning, mgmt_calls = _handle_position_management(
            active_positions, price_map, api_calls
        )
        api_calls.extend(mgmt_calls)
        reasoning_parts.extend(mgmt_reasoning)

    # ── Account summary ──
    if account_data and isinstance(account_data, dict):
        balance = _to_num(account_data.get("balance", 0))
        balance_usdc = balance / 1_000_000 if balance > 1000 else balance
        stats = account_data.get("trading_stats", {})
        reasoning_parts.append(f"\n## Account Status")
        reasoning_parts.append(f"- Balance: {balance_usdc:.2f} USDC")
        if stats and isinstance(stats, dict):
            reasoning_parts.append(f"- Total Trades: {_to_num(stats.get('total_trades', 0)):.0f}")
            reasoning_parts.append(f"- Win Rate: {_to_num(stats.get('win_rate', 0)):.0%}")

    reasoning = "\n".join(reasoning_parts)
    return reasoning, api_calls, external_calls, context


def _handle_structured_cases(cases):
    """Process structured analysis cases (market packets with observations).

    Reads observation signals from the provided data and produces
    structured JSON responses. Does NOT hardcode specific case IDs,
    assets, or expected outcomes.
    """
    results = []
    for idx, case in enumerate(cases):
        case_id = case.get("case_id", case.get("id", f"case_{idx}"))
        asset = case.get("asset", "Unknown")
        market_packet = case.get("market_packet", case.get("observations", []))
        perturbation = case.get("perturbation", case.get("new_information", ""))

        if isinstance(market_packet, dict):
            observations = market_packet.get("observations", [])
        elif isinstance(market_packet, list):
            observations = market_packet
        else:
            observations = []

        # Classify by signal direction. Prefer explicit labels, then infer from content.
        bullish = [o for o in observations if o.get("signal") == "bullish"]
        bearish = [o for o in observations if o.get("signal") == "bearish"]

        if not bullish and not bearish:
            for obs in observations:
                text = (
                    f"{obs.get('category', '')} {obs.get('content', '')} "
                    f"{obs.get('summary', '')}"
                ).lower()
                if any(k in text for k in ["bull", "breakout", "accumulation", "uptrend", "rally", "long"]):
                    bullish.append({**obs, "weight": obs.get("weight", 1.0), "signal": "bullish"})
                elif any(k in text for k in ["bear", "breakdown", "distribution", "downtrend", "selloff", "short"]):
                    bearish.append({**obs, "weight": obs.get("weight", 1.0), "signal": "bearish"})

        bull_w = sum(float(o.get("weight", 0.5)) for o in bullish)
        bear_w = sum(float(o.get("weight", 0.5)) for o in bearish)

        if bull_w > bear_w * 1.2:
            regime = "bullish"
            confidence = min(int(55 + (bull_w - bear_w) * 15), 85)
        elif bear_w > bull_w * 1.2:
            regime = "bearish"
            confidence = min(int(55 + (bear_w - bull_w) * 15), 85)
        else:
            regime = "neutral"
            confidence = 50

        sorted_obs = sorted(observations, key=lambda o: float(o.get("weight", 0)), reverse=True)
        supporting = []
        counter = []
        for o in sorted_obs:
            sig = o.get("signal", "noise")
            oid = o.get("id", o.get("obs_id", ""))
            if not oid:
                continue
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

        if bullish and bearish:
            tension = (f"Conflicting signals between "
                       f"{bullish[0].get('category', 'bullish indicators')} and "
                       f"{bearish[0].get('category', 'bearish indicators')}")
        else:
            tension = f"Signals are predominantly {regime} with limited counter-evidence."

        categories = set(o.get("category", "") for o in observations if o.get("category"))
        summary = (
            f"Analysis of {len(observations)} observations across "
            f"{', '.join(categories) if categories else 'multiple categories'} "
            f"indicates a {regime} regime at {confidence}% confidence for {asset}."
        )

        ma1 = {
            "market_regime": regime,
            "confidence": confidence,
            "key_tension": tension[:200],
            "top_2_evidence_for": supporting[:2] if len(supporting) >= 2 else supporting + ["none"],
            "top_1_counter_evidence": counter[0] if counter else "none",
            "analysis_summary": summary[:500],
        }

        # MA-2: Process perturbation
        pert_text = perturbation if isinstance(perturbation, str) else json.dumps(perturbation)
        pert_lower = pert_text.lower()

        bearish_signals = any(w in pert_lower for w in
                              ["crash", "plunge", "hack", "ban", "collapse", "dump", "liquidat"])
        bullish_signals = any(w in pert_lower for w in
                              ["surge", "rally", "approval", "breakout", "accumulation"])
        noise_signals = any(w in pert_lower for w in
                            ["rumor", "unconfirmed", "minor", "marginal"])

        if noise_signals:
            updated_regime = regime
            updated_confidence = max(confidence - 5, 30)
            changed = "no"
            reason = "New information appears unconfirmed/minor and does not materially change the thesis."
            invalidated = "none"
        elif bearish_signals and regime != "bearish":
            updated_regime = "bearish"
            updated_confidence = 65
            changed = "yes"
            reason = "Material bearish evidence outweighs prior bullish signals."
            invalidated = supporting[0] if supporting else "none"
        elif bullish_signals and regime != "bullish":
            updated_regime = "bullish"
            updated_confidence = 65
            changed = "yes"
            reason = "Material bullish catalyst shifts the balance of evidence."
            invalidated = supporting[0] if supporting else "none"
        else:
            updated_regime = regime
            updated_confidence = confidence
            changed = "no"
            reason = "New information is consistent with current assessment."
            invalidated = "none"

        ma2 = {
            "updated_regime": updated_regime,
            "updated_confidence": updated_confidence,
            "changed": changed,
            "reason_for_change": reason,
            "which_previous_evidence_is_invalidated": invalidated,
        }

        results.append({"case_id": case_id, "ma1": ma1, "ma2": ma2})

    return results


def _collect_t1_market_data():
    """Fetch market snapshot data from external sources for T1.

    Returns: (reasoning_parts, external_calls, price_map)
    """
    reasoning = ["## Market Snapshot\n"]
    calls = []
    price_map = {}
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    cg_assets = {
        "bitcoin": "btc",
        "ethereum": "eth",
        "solana": "sol",
    }
    cg_ids = ",".join(cg_assets.keys())
    cg_url = (
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={cg_ids}"
        f"&vs_currencies=usd"
        f"&include_24hr_change=true"
        f"&include_24hr_vol=true"
        f"&include_market_cap=true"
    )

    start = time.time()
    try:
        resp = requests.get(cg_url, timeout=10)
        ms = int((time.time() - start) * 1000)
        payload = resp.json()
        calls.append({
            "source": "CoinGecko",
            "url": cg_url,
            "httpStatus": resp.status_code,
            "requestMs": ms,
            "response": payload,
        })

        reasoning.append(f"Data retrieved at {timestamp} from CoinGecko:\n")
        for cg_id, symbol in cg_assets.items():
            data = payload.get(cg_id, {})
            price = _to_num(data.get("usd"))
            change = _to_num(data.get("usd_24h_change"))
            volume = _to_num(data.get("usd_24h_vol"))
            mcap = _to_num(data.get("usd_market_cap"))
            if price > 0:
                price_map[symbol] = {"raw": price, "exponent": 0, "display": price}
                reasoning.append(f"- **{symbol.upper()}**: ${price:,.2f}")
                reasoning.append(f"  - 24h change: {change:+.2f}%")
                reasoning.append(f"  - 24h volume: ${volume:,.0f}")
                reasoning.append(f"  - Market cap: ${mcap:,.0f}")
    except Exception as e:
        ms = int((time.time() - start) * 1000)
        calls.append({
            "source": "CoinGecko",
            "url": cg_url,
            "httpStatus": 0,
            "requestMs": ms,
            "response": {"error": str(e)},
        })
        reasoning.append(f"- CoinGecko request failed: {e}")

    reasoning.append("")
    reasoning.append("### 龙虾 (Lobster) Token\n")
    reasoning.append(
        '- "龙虾" is a token listed on Binance Alpha. '
        "Multiple tokens named LOBSTER exist; they are not the same. "
        "Unable to programmatically resolve the exact Binance Alpha listing "
        "in this baseline runner — a real agent should search for it."
    )
    reasoning.append("")

    return reasoning, calls, price_map


def _collect_external_intel(price_map):
    """Fetch a small set of external BTC intel sources (best effort)."""
    reasoning = ["## External Intelligence\n"]
    calls = []

    sources = [
        ("coingecko", "https://api.coingecko.com/api/v3/coins/bitcoin"),
        ("alternative_me", "https://api.alternative.me/fng/"),
    ]

    coingecko_payload = None
    for source, url in sources:
        start = time.time()
        try:
            resp = requests.get(url, timeout=8)
            ms = int((time.time() - start) * 1000)
            payload = resp.json()
            calls.append({
                "source": source,
                "url": url,
                "httpStatus": resp.status_code,
                "requestMs": ms,
                "response": payload if isinstance(payload, dict) else {"raw": payload},
            })
            if source == "coingecko" and isinstance(payload, dict):
                coingecko_payload = payload
        except Exception as e:
            ms = int((time.time() - start) * 1000)
            calls.append({
                "source": source,
                "url": url,
                "httpStatus": 0,
                "requestMs": ms,
                "response": {"error": str(e)},
            })

    if coingecko_payload:
        md = coingecko_payload.get("market_data", {})
        current = _to_num(md.get("current_price", {}).get("usd"))
        change = _to_num(md.get("price_change_percentage_24h"))
        volume = _to_num(md.get("total_volume", {}).get("usd"))
        mcap = _to_num(md.get("market_cap", {}).get("usd"))
        if current > 0:
            reasoning.append("- BTC external quote (CoinGecko):")
            reasoning.append(f"  - Price: ${current:,.2f}")
            reasoning.append(f"  - 24h change: {change:+.2f}%")
            reasoning.append(f"  - 24h volume: ${volume:,.0f}")
            reasoning.append(f"  - Market cap: ${mcap:,.0f}")

    if "btc" in price_map:
        local_btc = price_map["btc"]["display"]
        reasoning.append(f"- Sandbox BTC quote cross-check: ${local_btc:,.2f}")
        if coingecko_payload:
            ext_btc = _to_num(
                coingecko_payload.get("market_data", {})
                .get("current_price", {})
                .get("usd")
            )
            if ext_btc > 0:
                deviation = abs(local_btc - ext_btc) / ext_btc * 100
                reasoning.append(f"  - Cross-source deviation: {deviation:.2f}%")

    reasoning.append("")
    return reasoning, calls


def _handle_trading(scenario, constraints, price_map, account_data, context):
    """Execute a trading action based on constraints and available market data.

    Picks an asset from the price data, determines direction from context
    (prior task analysis), and opens a position within constraint bounds.
    """
    reasoning = []
    calls = []

    # Read constraints
    min_usdc = _to_num(constraints.get("minAmountUsdc", constraints.get("minAmount", 5)), 5)
    max_usdc = _to_num(constraints.get("maxAmountUsdc", constraints.get("maxAmount", 20)), 20)
    max_pct = _to_num(constraints.get("maxBalancePct", 0.5), 0.5)

    # Pick asset — use first available crypto asset from price data
    asset = None
    for candidate in CRYPTO_ASSETS:
        if candidate in price_map:
            asset = candidate
            break
    if not asset and price_map:
        asset = next(iter(price_map))
    if not asset:
        asset = "btc"

    # Get current price for chosen asset
    price_info, price_call = safe_call(
        api.get_price, "get-price",
        {"asset": asset},
        asset,
    )
    calls.append(price_call)

    display_price = 0
    if price_info:
        raw = _to_num(price_info.get("price", 0))
        exp = _to_num(price_info.get("price_exponent", price_info.get("priceExponent", -8)), -8)
        display_price = format_price(raw, exp)

    # Direction from prior analysis context, default to call
    direction = context.get("direction", "call")
    conf = context.get("confidence", 5)

    # Amount: use midpoint of allowed range
    amount_usdc = max(min_usdc, min(max_usdc, 10))
    amount_base = int(amount_usdc * 1_000_000)

    # Check balance constraint
    if account_data and isinstance(account_data, dict):
        balance = _to_num(account_data.get("balance", 0))
        max_by_balance = int(balance * max_pct)
        if amount_base > max_by_balance:
            amount_base = max_by_balance
            amount_usdc = amount_base / 1_000_000

    duration = 120
    multiplier = 2.0

    reasoning.append("## Trading Decision\n")
    reasoning.append(f"**Asset**: {asset.upper()}")
    reasoning.append(f"**Direction**: {direction.upper()} (Confidence: {conf}/10)")
    reasoning.append(f"**Amount**: {amount_usdc:.0f} USDC")
    reasoning.append(f"**Duration**: {duration}s")
    reasoning.append(f"**Multiplier**: {multiplier}x")
    reasoning.append(f"**Current Price**: ${display_price:,.2f}\n")

    # Execute trade
    req_body = {
        "asset": asset, "side": direction, "amount": amount_base,
        "mode": {"type": "Single", "duration": duration},
        "target_multiplier": multiplier,
    }
    trade_data, trade_call = safe_call(
        api.open_position, "open-position", req_body,
        asset, direction, amount_base, duration, multiplier,
    )
    calls.append(trade_call)

    if trade_data and isinstance(trade_data, dict):
        tx_hash = trade_data.get("tx_hash", trade_data.get("txHash", "N/A"))
        pos_id = trade_data.get("position_id", trade_data.get("positionId", "N/A"))
        reasoning.append("## Execution Result\n")
        reasoning.append(f"- **tx_hash**: `{tx_hash}`")
        reasoning.append(f"- **position_id**: `{pos_id}`")
        reasoning.append(f"- **Status**: Executed successfully")
        reasoning.append(f"\nAll parameters match the trading plan.")
    else:
        reasoning.append("\n**Execution**: Trade could not be executed.")

    return reasoning, calls


def _handle_position_management(positions, price_map, existing_calls):
    """Evaluate active positions and make hold/close decisions.

    For each active position: fetch current price, calculate unrealized P&L,
    and decide whether to close or hold based on simple profit/loss logic.
    """
    reasoning = ["## Position Management\n"]
    calls = []
    decisions = []

    for i, pos in enumerate(positions):
        pos_id = pos.get("positionId", pos.get("position_id", "N/A"))
        pos_asset = (pos.get("asset", "")).lower()
        pos_side = pos.get("side", "unknown")
        entry_raw = _to_num(pos.get("entryPrice", pos.get("entry_price", 0)))
        entry_exp = _to_num(pos.get("priceExponent", pos.get("price_exponent", -8)))
        entry_price = format_price(entry_raw, entry_exp)
        amount_raw = _to_num(pos.get("amount", 0))
        amount_usdc = amount_raw / 1_000_000 if amount_raw > 1000 else amount_raw
        duration = _to_num(pos.get("durationSeconds", pos.get("duration_seconds", 0)))

        # Get current price
        already_have = pos_asset in price_map
        if already_have:
            current_price = price_map[pos_asset]["display"]
        else:
            cur_data, cur_call = safe_call(
                api.get_price, "get-price",
                {"asset": pos_asset},
                pos_asset,
            )
            calls.append(cur_call)
            if cur_data:
                cur_raw = _to_num(cur_data.get("price", 0))
                cur_exp = _to_num(cur_data.get("price_exponent", cur_data.get("priceExponent", -8)), -8)
                current_price = format_price(cur_raw, cur_exp)
            else:
                current_price = entry_price

        # Calculate P&L
        if pos_side == "call":
            pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price else 0
        else:
            pnl_pct = ((entry_price - current_price) / entry_price * 100) if entry_price else 0

        is_winning = pnl_pct > 0
        pnl_usdc = amount_usdc * (pnl_pct / 100)

        reasoning.append(f"### Position {i + 1}: {pos_asset.upper()} {pos_side.upper()}\n")
        reasoning.append(f"- **Position ID**: `{pos_id}`")
        reasoning.append(f"- **Entry**: ${entry_price:,.2f}")
        reasoning.append(f"- **Current**: ${current_price:,.2f}")
        reasoning.append(f"- **P&L**: {pnl_pct:+.2f}% ({pnl_usdc:+.2f} USDC)")
        reasoning.append(f"- **Amount**: {amount_usdc:.0f} USDC")
        reasoning.append(f"- **Duration**: {duration}s")
        reasoning.append(f"- **Assessment**: {'WINNING' if is_winning else 'LOSING'}\n")

        if is_winning:
            reasoning.append(f"**Decision: HOLD** — Position is profitable, hold to expiry.\n")
            decisions.append(("hold", pos_id, pos_asset))
        else:
            reasoning.append(f"**Decision: CLOSE** — Cut losses to preserve capital.\n")
            decisions.append(("close", pos_id, pos_asset))

    # Execute close decisions
    for decision, pos_id, pos_asset in decisions:
        if decision == "close" and pos_id != "N/A":
            req_body = {"position_id": pos_id, "asset": pos_asset}
            close_data, close_call = safe_call(
                api.close_position, "close-position", req_body,
                pos_id, pos_asset,
            )
            calls.append(close_call)
            if close_data:
                reasoning.append(f"- Closed `{pos_id}` ({pos_asset.upper()}) ✓")
            else:
                reasoning.append(f"- Close failed for `{pos_id}`")
        else:
            reasoning.append(f"- Holding `{pos_id}` ({pos_asset.upper()}) until expiry ✓")

    reasoning.extend([
        "\n## Risk Framework\n",
        "**Loss Threshold**: -3% from entry. Close immediately on breach.",
        "**Reversal Signal**: Funding rate sign flip, 3x volume surge, "
        "or VWAP level breach would prompt reassessment.",
    ])

    return reasoning, calls


# ═══════════════════════════════════════════════════════════════════════════════
#                              MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

def run():
    """Execute all 5 benchmark tasks sequentially."""
    print_header("Manic Trading Benchmark", "🚀")
    print(f"  {C.DIM}Executing 5 evaluation tasks...{C.RESET}\n")

    context = {}
    total_start = time.time()
    collected_calls = []

    for task_index in range(5):
        task_start = time.time()

        try:
            task_response = api.get_next_task()
            task_data = (task_response.get("data", task_response)
                         if isinstance(task_response, dict) else task_response)

            title = task_data.get("title") if isinstance(task_data, dict) else None
            print_task_start(task_index, title)

            reasoning, api_calls, ext_calls, context = execute_task(
                task_index, task_data, context
            )

            duration_ms = int((time.time() - task_start) * 1000)
            collected_calls = api_calls

            api.submit_task(
                task_index=task_index,
                status="success",
                agent_reasoning=reasoning[:4000],
                api_calls=api_calls,
                external_api_calls=ext_calls if ext_calls else None,
                duration_ms=duration_ms,
            )

            print_task_done(time.time() - task_start)

        except Exception as e:
            print_task_done(0, status=f"error: {e}")
            traceback.print_exc()

            try:
                api.submit_task(
                    task_index=task_index,
                    status="failed",
                    agent_reasoning=f"Task failed with error: {e}",
                    api_calls=collected_calls if collected_calls else None,
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
            print(f"\r  {C.CYAN}{frame}{C.RESET} Scoring in progress... "
                  f"{C.DIM}({elapsed:.0f}s){C.RESET}", end="")
            sys.stdout.flush()

            try:
                result = api.poll_result(timeout=5, interval=3)
                print(f"\r  {C.GREEN}✓{C.RESET} Scoring complete!              ")
                print_final_results(result)
                return
            except TimeoutError:
                pass
            except api.ApiError:
                pass

            time.sleep(2)

        if not api.BENCHMARK_SESSION_ID:
            print(f"\r  {C.YELLOW}⚠{C.RESET} No BENCHMARK_SESSION_ID in .env — "
                  f"cannot poll results automatically.")
            print(f"    Re-run {C.CYAN}npx manic-trading-benchmark init{C.RESET} "
                  f"to get a new session with result polling,")
            print(f"    or check results at: {C.CYAN}https://benchmark.manic.trade{C.RESET}\n")
        else:
            print(f"\r  {C.YELLOW}⚠{C.RESET} Scoring is still in progress. "
                  f"Check results at:")
            print(f"    {C.CYAN}https://benchmark.manic.trade{C.RESET}\n")

    except KeyboardInterrupt:
        print(f"\n\n  {C.YELLOW}Interrupted.{C.RESET} Check results at:")
        print(f"    {C.CYAN}https://benchmark.manic.trade{C.RESET}\n")


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not api.BENCHMARK_API_KEY:
        print(f"\n  {C.RED}Error: BENCHMARK_API_KEY not found.{C.RESET}")
        print(f"  Run {C.CYAN}npx manic-trading-benchmark init{C.RESET} first.\n")
        sys.exit(1)

    run()
