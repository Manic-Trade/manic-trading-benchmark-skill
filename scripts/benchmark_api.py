"""
Manic Trading Benchmark — Sandbox API Client

Provides HTTP wrappers for all benchmark-server endpoints:
  - Task orchestration (next / submit)
  - Sandbox trading (prices, account, positions)
"""

import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# ─── Configuration ────────────────────────────────────────────────────────────

BENCHMARK_API_KEY = os.getenv("BENCHMARK_API_KEY", "")
BENCHMARK_API_BASE = os.getenv("BENCHMARK_API_BASE", "https://benchmark-api.manic.trade/agent")
BENCHMARK_SERVER_BASE = os.getenv("BENCHMARK_SERVER_BASE", "https://benchmark-api.manic.trade")

TASK_BASE = f"{BENCHMARK_SERVER_BASE}/benchmark"

# ─── HTTP Helpers ─────────────────────────────────────────────────────────────

def _agent_headers():
    """Headers for Agent-authenticated endpoints (bk- token)."""
    return {
        "Authorization": f"Bearer {BENCHMARK_API_KEY}",
        "Content-Type": "application/json",
    }


def _request(method, url, headers=None, json_body=None, timeout=30):
    """Make HTTP request with error handling."""
    try:
        resp = requests.request(
            method,
            url,
            headers=headers or _agent_headers(),
            json=json_body,
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise RuntimeError(
            f"API error {resp.status_code} on {method} {url}: {detail}"
        ) from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network error on {method} {url}: {e}") from e


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


# ─── Session Status ───────────────────────────────────────────────────────────

def get_session_status(session_id):
    """GET /benchmark/session/:id/status — Poll session status (requires JWT, used for reference)."""
    return _request("GET", f"{TASK_BASE}/session/{session_id}/status")


def poll_score(timeout=120, interval=3):
    """Poll task/next until scoring is complete, or use session status.

    After T5 submit, keep calling task/next. When status becomes 'completed',
    the response will contain final scores.
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            result = _request("POST", f"{TASK_BASE}/task/next")
            data = result.get("data", result)
            if data.get("status") == "completed" or data.get("totalScore") is not None:
                return data
            if data.get("status") == "scoring":
                time.sleep(interval)
                continue
        except RuntimeError:
            pass
        time.sleep(interval)
    raise TimeoutError(f"Scoring did not complete within {timeout}s")
