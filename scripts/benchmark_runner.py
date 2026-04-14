#!/usr/bin/env python3
"""
Manic Trading Benchmark — Runner & Visualization

Generic orchestrator that drives 5 benchmark tasks sequentially.
Task prompts are delivered dynamically by the server — this runner
fetches each scenario, executes it using sandbox APIs, and submits
the result. No task-specific strategy is hardcoded.
"""

import sys
import os
import json
import time
import math
import traceback

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
    meaning = meanings.get(grade, "")
    print(f"    {C.DIM}{meaning}{C.RESET}")
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
    total = stats.get("total_trades", 0)
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    win_rate = stats.get("win_rate", 0)
    net_pnl = stats.get("net_pnl", 0)
    pnl_usdc = net_pnl / 1_000_000 if abs(net_pnl) > 1000 else net_pnl
    pnl_color = C.GREEN if pnl_usdc >= 0 else C.RED
    pnl_sign = "+" if pnl_usdc >= 0 else ""
    print(f"  Trades: {total}  │  Wins: {C.GREEN}{wins}{C.RESET}  │  "
          f"Losses: {C.RED}{losses}{C.RESET}  │  "
          f"Win Rate: {win_rate:.0%}")
    print(f"  Net P&L: {pnl_color}{pnl_sign}{pnl_usdc:.2f} USDC{C.RESET}")


def print_final_results(result):
    data = result.get("data", result) if isinstance(result, dict) else result
    if not isinstance(data, dict):
        print(f"  {C.YELLOW}Unable to parse scoring result.{C.RESET}")
        return

    total_score = data.get("totalScore", data.get("total_score", 0))
    grade = data.get("grade", "D")

    dim_scores = {}
    dim_keys = [
        ("scoreData", "Real-time Data"),
        ("scoreIntel", "Multi-source Intel"),
        ("scoreAnalysis", "Market Analysis"),
        ("scoreDecision", "Trading Decision"),
        ("scoreRisk", "Risk Management"),
        ("score_data", "Real-time Data"),
        ("score_intel", "Multi-source Intel"),
        ("score_analysis", "Market Analysis"),
        ("score_decision", "Trading Decision"),
        ("score_risk", "Risk Management"),
    ]
    for key, dim_name in dim_keys:
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

    print(f"\n  {C.DIM}View full results at: {C.CYAN}https://benchmark.manic.trade{C.RESET}\n")


# ═══════════════════════════════════════════════════════════════════════════════
#                          SANDBOX API CALL HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _make_call_record(command, request_body=None, response=None,
                      http_status=200, request_ms=None, error=None):
    """Build an api_calls entry matching the server DTO (command-based)."""
    record = {"command": command, "httpStatus": http_status}
    if request_body is not None:
        record["request"] = request_body
    if response is not None:
        record["response"] = response
    if request_ms is not None:
        record["requestMs"] = request_ms
    if error is not None:
        record["response"] = {"error": str(error)}
        record["httpStatus"] = 0
    return record


def safe_call(fn, command, request_body=None, *args, **kwargs):
    """Call a sandbox API function and return (result_data, call_record).

    Always returns a tuple so callers can append to api_calls regardless
    of success/failure.
    """
    start = time.time()
    try:
        result = fn(*args, **kwargs)
        ms = int((time.time() - start) * 1000)
        data = result.get("data", result) if isinstance(result, dict) else result
        record = _make_call_record(command, request_body, data, 200, ms)
        return data, record
    except Exception as e:
        ms = int((time.time() - start) * 1000)
        record = _make_call_record(command, request_body, error=e, request_ms=ms)
        return None, record


def format_price(raw_price, exponent):
    """Convert raw Manic price to human-readable dollar amount."""
    if exponent and isinstance(raw_price, (int, float)) and abs(raw_price) > 1e6:
        return raw_price * (10 ** exponent)
    return raw_price


# ═══════════════════════════════════════════════════════════════════════════════
#                           GENERIC TASK EXECUTOR
# ═══════════════════════════════════════════════════════════════════════════════

def execute_task(task_index, task_data, context):
    """Execute a benchmark task generically based on the server scenario.

    This function does NOT contain task-specific strategies. It reads the
    scenario from task_data and uses sandbox APIs to gather relevant data,
    then returns the gathered information as the agent's reasoning.

    A real AI agent would replace this with intelligent analysis of the
    scenario and sophisticated use of both sandbox and external APIs.

    Returns: (reasoning, api_calls, external_api_calls, updated_context)
    """
    scenario = ""
    if isinstance(task_data, dict):
        scenario = task_data.get("scenario", "")
        if isinstance(scenario, dict):
            scenario = json.dumps(scenario, indent=2)
    elif isinstance(task_data, str):
        scenario = task_data

    api_calls = []
    external_calls = []
    reasoning_parts = []
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Gather sandbox data based on what's available
    prices_data, prices_call = safe_call(api.get_prices, "get-prices")
    api_calls.append(prices_call)

    account_data, account_call = safe_call(api.get_account, "get-account")
    api_calls.append(account_call)

    # Format price data for reasoning
    if prices_data:
        reasoning_parts.append(f"## Market Data (as of {timestamp})\n")
        price_list = prices_data if isinstance(prices_data, list) else []
        for item in price_list:
            asset = item.get("asset", "").upper()
            price = item.get("price", 0)
            exponent = item.get("price_exponent", item.get("priceExponent", -8))
            display = format_price(price, exponent)
            reasoning_parts.append(f"- **{asset}**: ${display:,.2f}")
        reasoning_parts.append(f"\nSource: Manic Trade Sandbox API\n")

    # Check positions (relevant for later tasks)
    positions_data, positions_call = safe_call(
        api.get_position_history, "position-history"
    )
    api_calls.append(positions_call)

    if positions_data:
        pos_list = positions_data if isinstance(positions_data, list) else []
        if isinstance(positions_data, dict):
            pos_list = positions_data.get("positions", [])

        if pos_list:
            reasoning_parts.append("## Current Positions\n")
            for pos in pos_list:
                pos_asset = pos.get("asset", "?").upper()
                pos_side = pos.get("side", "?")
                pos_status = pos.get("status", "?")
                entry_raw = pos.get("entry_price", pos.get("entryPrice", 0))
                entry_exp = pos.get("price_exponent", pos.get("priceExponent", -8))
                entry_display = format_price(entry_raw, entry_exp)

                # Get current price for P&L
                cur_data, cur_call = safe_call(
                    api.get_price, "get-price",
                    {"asset": pos_asset.lower()},
                    pos_asset,
                )
                api_calls.append(cur_call)

                cur_display = entry_display
                if cur_data:
                    cur_raw = cur_data.get("price", 0)
                    cur_exp = cur_data.get("price_exponent", cur_data.get("priceExponent", -8))
                    cur_display = format_price(cur_raw, cur_exp)

                reasoning_parts.append(
                    f"- **{pos_asset} {pos_side.upper()}** | "
                    f"Entry: ${entry_display:,.2f} | "
                    f"Current: ${cur_display:,.2f} | "
                    f"Status: {pos_status}"
                )
            reasoning_parts.append("")

    # Build the response based on gathered data
    reasoning_parts.append(f"## Task Response\n")
    reasoning_parts.append(
        "Based on the market data gathered from the Sandbox API, "
        "the above information represents the current state of the market "
        "and any active positions."
    )

    # Account info
    if account_data:
        balance = account_data.get("balance", 0)
        balance_usdc = balance / 1_000_000 if balance > 1000 else balance
        stats = account_data.get("trading_stats", {})
        reasoning_parts.append(f"\n## Account Status")
        reasoning_parts.append(f"- Balance: {balance_usdc:.2f} USDC")
        if stats:
            reasoning_parts.append(f"- Trades: {stats.get('total_trades', 0)}")
            reasoning_parts.append(f"- Win Rate: {stats.get('win_rate', 0):.0%}")

    reasoning = "\n".join(reasoning_parts)
    return reasoning, api_calls, external_calls, context


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
        task_start = time.time()

        try:
            task_response = api.get_next_task()
            task_data = task_response.get("data", task_response) if isinstance(task_response, dict) else task_response

            title = task_data.get("title") if isinstance(task_data, dict) else None
            print_task_start(task_index, title)

            reasoning, api_calls, ext_calls, context = execute_task(
                task_index, task_data, context
            )

            duration_ms = int((time.time() - task_start) * 1000)

            api.submit_task(
                task_index=task_index,
                status="success",
                agent_reasoning=reasoning[:12000],
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
                result = api.poll_score(timeout=5, interval=3)
                print(f"\r  {C.GREEN}✓{C.RESET} Scoring complete!              ")
                print_final_results(result)
                return
            except TimeoutError:
                pass
            except api.ApiError:
                pass

            time.sleep(2)

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
