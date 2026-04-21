"""
Manic Trading Benchmark — Sandbox API Client

Provides HTTP wrappers for all benchmark-server endpoints:
  - Task orchestration (next / submit)
  - Sandbox trading (prices, account, positions)
  - Result polling (via public share endpoint)
"""

import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# ─── Configuration ────────────────────────────────────────────────────────────

BENCHMARK_API_KEY = os.getenv("BENCHMARK_API_KEY", "")
BENCHMARK_API_BASE = os.getenv("BENCHMARK_API_BASE", "https://bo-server-api-alpha.manic.trade/api/agent")
BENCHMARK_SERVER_BASE = os.getenv("BENCHMARK_SERVER_BASE", "https://bo-server-api-alpha.manic.trade")
BENCHMARK_SESSION_ID = os.getenv("BENCHMARK_SESSION_ID", "")

TASK_BASE = f"{BENCHMARK_SERVER_BASE}/api/benchmark"

# ─── HTTP Helpers ─────────────────────────────────────────────────────────────

def _agent_headers():
    """Headers for Agent-authenticated endpoints (bk- token)."""
    return {
        "Authorization": f"Bearer {BENCHMARK_API_KEY}",
        "Content-Type": "application/json",
    }


class ApiError(Exception):
    """Raised when the server returns a business error (code != 0) or HTTP error."""
    def __init__(self, code, msg, data=None, http_status=None):
        self.code = code
        self.msg = msg
        self.data = data
        self.http_status = http_status
        super().__init__(f"[{code}] {msg}")


def _request(method, url, headers=None, json_body=None, timeout=30):
    """Make HTTP request with error handling.

    The server uses a unified response format:
      Success: {"code": 0, "msg": "ok", "data": {...}}
      Error:   {"code": <int>, "msg": "<error text>", "data": null}

    Business correctness is determined by the response body `code`:
      - code == 0    -> success
      - code != 0    -> business error
    HTTP status is only used for transport/infrastructure failures.
    """
    try:
        resp = requests.request(
            method,
            url,
            headers=headers or _agent_headers(),
            json=json_body,
            timeout=timeout,
        )
        body = resp.json()
    except requests.exceptions.RequestException as e:
        raise ApiError(code=-1, msg=f"Network error on {method} {url}: {e}") from e
    except (ValueError, json.JSONDecodeError):
        if resp.status_code >= 400:
            raise ApiError(
                code=resp.status_code,
                msg=f"HTTP {resp.status_code}: {resp.text[:200]}",
                http_status=resp.status_code,
            )
        return resp.text

    if resp.status_code >= 400:
        code = body.get("code", resp.status_code) if isinstance(body, dict) else resp.status_code
        msg = body.get("msg", str(body)) if isinstance(body, dict) else str(body)
        raise ApiError(code=code, msg=msg, data=body, http_status=resp.status_code)

    if isinstance(body, dict) and "code" in body and body["code"] != 0:
        raise ApiError(
            code=body["code"],
            msg=body.get("msg", "Unknown business error"),
            data=body.get("data"),
            http_status=resp.status_code,
        )

    # Keep HTTP status for debugging/audit fields (api_calls).
    if isinstance(body, dict):
        body["_http_status"] = resp.status_code

    return body


# ─── Task Orchestration ──────────────────────────────────────────────────────

def get_next_task():
    """POST /benchmark/task/next — Get next task scenario."""
    return _request("POST", f"{TASK_BASE}/task/next")


def submit_task(task_index, status, agent_reasoning,
                api_calls=None, external_api_calls=None, duration_ms=None, context=None):
    """POST /benchmark/task/submit — Submit task result."""
    body = {
        "task_index": task_index,
        "status": status,
        "agent_reasoning": agent_reasoning,
    }
    if api_calls is not None:
        body["api_calls"] = api_calls
    if external_api_calls is not None:
        body["external_api_calls"] = external_api_calls
    if duration_ms is not None:
        body["duration_ms"] = duration_ms
    if context is not None:
        body["context"] = context
    return _request("POST", f"{TASK_BASE}/task/submit", json_body=body)


# ─── Sandbox: Price Data ─────────────────────────────────────────────────────

def get_prices():
    """GET /agent/asset/prices — Get all asset prices."""
    return _request("GET", f"{BENCHMARK_API_BASE}/asset/prices")


def get_price(asset):
    """GET /agent/asset/price/:asset — Get single asset price."""
    return _request("GET", f"{BENCHMARK_API_BASE}/asset/price/{asset.lower()}")


# ─── Sandbox: Account ────────────────────────────────────────────────────────

def get_account():
    """GET /agent/account — Get virtual account info."""
    return _request("GET", f"{BENCHMARK_API_BASE}/account")


# ─── Sandbox: Trading ────────────────────────────────────────────────────────

def open_position(asset, side, amount, duration, target_multiplier=2.0):
    """POST /agent/open-position — Open a sandbox position.

    Args:
        asset: Asset symbol (btc, eth, sol, etc.)
        side: 'call' (bullish) or 'put' (bearish)
        amount: Amount in base units (e.g. 10000000 = 10 USDC)
        duration: Duration in seconds (30/60/120/180/240/300)
        target_multiplier: 1.0 ~ 100.0
    """
    return _request("POST", f"{BENCHMARK_API_BASE}/open-position", json_body={
        "asset": asset.lower(),
        "side": side,
        "amount": amount,
        "mode": {"type": "Single", "duration": duration},
        "target_multiplier": target_multiplier,
    })


def close_position(position_id, asset):
    """POST /agent/close-position — Close a position early."""
    return _request("POST", f"{BENCHMARK_API_BASE}/close-position", json_body={
        "position_id": position_id,
        "asset": asset.lower(),
    })


# ─── Sandbox: Position History ────────────────────────────────────────────────

def get_position_history():
    """GET /agent/position-history — Get all positions for this session."""
    return _request("GET", f"{BENCHMARK_API_BASE}/position-history")


# ─── Result Polling ──────────────────────────────────────────────────────────

def get_share_result(session_id=None):
    """GET /benchmark/share/:sessionId — Public endpoint, no auth needed.

    Returns scoring data for a completed session.
    """
    sid = session_id or BENCHMARK_SESSION_ID
    if not sid:
        raise ApiError(code=-1, msg="No session ID available for result polling")
    return _request("GET", f"{TASK_BASE}/share/{sid}", headers={})


def poll_result(session_id=None, timeout=120, interval=3):
    """Poll for scoring results after all tasks are submitted.

    Strategy:
    1. Try the public share endpoint (requires session ID from .env)
    2. Use task/next as a status probe to detect scoring state
    3. Return results once scoring is complete
    """
    sid = session_id or BENCHMARK_SESSION_ID
    if not sid:
        raise ApiError(code=-1, msg=(
            "No BENCHMARK_SESSION_ID configured. "
            "Re-run 'npx manic-trading-benchmark init' to set up a new session."
        ))

    start = time.time()

    while time.time() - start < timeout:
        try:
            result = get_share_result(sid)
            data = result.get("data") if isinstance(result, dict) else None
            if data and isinstance(data, dict):
                total = data.get("totalScore", data.get("total_score"))
                if total is not None:
                    return data
        except ApiError:
            pass

        try:
            _request("POST", f"{TASK_BASE}/task/next")
        except ApiError as e:
            if e.code in (2002, 2203) or e.http_status == 401:
                pass

        time.sleep(interval)

    raise TimeoutError(f"Scoring did not complete within {timeout}s")


# ─── CLI Entry Point ────────────────────────────────────────────────────────

def _cli():
    """Command-line interface for benchmark API calls."""
    import argparse

    parser = argparse.ArgumentParser(description="Manic Trading Benchmark API CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # Task orchestration
    sub.add_parser("next-task", help="Get next task scenario")

    sp_submit = sub.add_parser("submit-task", help="Submit task result")
    sp_submit.add_argument("--task-index", type=int, required=True)
    sp_submit.add_argument("--status", default="success")
    sp_submit.add_argument("--reasoning", required=True)
    sp_submit.add_argument("--api-calls", default=None, help="JSON array of API calls")
    sp_submit.add_argument("--external-api-calls", default=None, help="JSON array of external API calls")
    sp_submit.add_argument("--duration-ms", type=int, default=None)

    # Sandbox: prices
    sub.add_parser("get-prices", help="Get all asset prices")
    sp_price = sub.add_parser("get-price", help="Get single asset price")
    sp_price.add_argument("--asset", required=True)

    # Sandbox: account
    sub.add_parser("get-account", help="Get virtual account info")

    # Sandbox: trading
    sp_open = sub.add_parser("open-position", help="Open a sandbox position")
    sp_open.add_argument("--asset", required=True)
    sp_open.add_argument("--side", required=True, choices=["call", "put"])
    sp_open.add_argument("--amount", type=int, required=True)
    sp_open.add_argument("--duration", type=int, default=60)
    sp_open.add_argument("--multiplier", type=float, default=2.0)

    sp_close = sub.add_parser("close-position", help="Close a position early")
    sp_close.add_argument("--position-id", required=True)
    sp_close.add_argument("--asset", required=True)

    sp_history = sub.add_parser("position-history", help="Get position history")
    sp_history.add_argument("--page", type=int, default=1)
    sp_history.add_argument("--limit", type=int, default=10)

    # Result polling
    sub.add_parser("poll-result", help="Poll for scoring results")

    args = parser.parse_args()

    try:
        if args.command == "next-task":
            result = get_next_task()
        elif args.command == "submit-task":
            api_calls = json.loads(args.api_calls) if args.api_calls else None
            ext_calls = json.loads(args.external_api_calls) if args.external_api_calls else None
            result = submit_task(
                task_index=args.task_index,
                status=args.status,
                agent_reasoning=args.reasoning,
                api_calls=api_calls,
                external_api_calls=ext_calls,
                duration_ms=args.duration_ms,
            )
        elif args.command == "get-prices":
            result = get_prices()
        elif args.command == "get-price":
            result = get_price(args.asset)
        elif args.command == "get-account":
            result = get_account()
        elif args.command == "open-position":
            result = open_position(args.asset, args.side, args.amount, args.duration, args.multiplier)
        elif args.command == "close-position":
            result = close_position(args.position_id, args.asset)
        elif args.command == "position-history":
            result = get_position_history()
        elif args.command == "poll-result":
            result = poll_result()
        else:
            parser.print_help()
            return

        print(json.dumps(result, indent=2, default=str))
    except ApiError as e:
        print(json.dumps({"error": True, "code": e.code, "msg": e.msg}, indent=2), file=__import__("sys").stderr)
        __import__("sys").exit(1)
    except TimeoutError as e:
        print(json.dumps({"error": True, "msg": str(e)}, indent=2), file=__import__("sys").stderr)
        __import__("sys").exit(1)


if __name__ == "__main__":
    _cli()
