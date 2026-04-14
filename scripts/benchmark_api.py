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
BENCHMARK_API_BASE = os.getenv("BENCHMARK_API_BASE", "https://benchmark-api.manic.trade/agent")
BENCHMARK_SERVER_BASE = os.getenv("BENCHMARK_SERVER_BASE", "https://benchmark-api.manic.trade")
BENCHMARK_SESSION_ID = os.getenv("BENCHMARK_SESSION_ID", "")

TASK_BASE = f"{BENCHMARK_SERVER_BASE}/benchmark"

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
      Error:   {"code": <int>, "msg": "<message>", "data": null}

    Business errors are returned as HTTP 200 with a non-zero code.
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
    return _request(
        "GET",
        f"{TASK_BASE}/share/{sid}",
        headers={"Content-Type": "application/json"},
    )


def _try_extract_session_id():
    """Try to discover session_id via the account endpoint.

    The account response may contain session metadata we can use.
    Falls back to None if not available.
    """
    try:
        result = _request("GET", f"{BENCHMARK_API_BASE}/account")
        data = result.get("data", result) if isinstance(result, dict) else {}
        if isinstance(data, dict):
            return data.get("sessionId", data.get("session_id"))
    except (ApiError, Exception):
        pass
    return None


def poll_result(session_id=None, timeout=120, interval=3):
    """Poll for scoring results after all tasks are submitted.

    Strategy:
    1. Try the public share endpoint if session ID is available
    2. Use task/next as a status probe (works during 'scoring' state)
    3. When 401 indicates scoring is done, try share endpoint
    4. If no session ID at all, wait for scoring then report timeout
       with guidance to check the web UI
    """
    sid = session_id or BENCHMARK_SESSION_ID
    start = time.time()
    scoring_detected = False

    while time.time() - start < timeout:
        # Try public share endpoint
        if sid:
            try:
                result = get_share_result(sid)
                data = result.get("data") if isinstance(result, dict) else None
                if data and isinstance(data, dict):
                    total = data.get("totalScore", data.get("total_score"))
                    if total is not None:
                        return data
            except ApiError:
                pass

        # Use task/next as a status probe (works during 'scoring' state)
        try:
            _request("POST", f"{TASK_BASE}/task/next")
        except ApiError as e:
            if e.code == 2002:
                # SESSION_INVALID_STATUS — scoring in progress
                scoring_detected = True
            elif e.code == 2203:
                # ALL_TASKS_COMPLETED — scoring may be done
                scoring_detected = True
            elif e.http_status == 401:
                # bk- token rejected — session completed
                scoring_detected = True
                if sid:
                    try:
                        result = get_share_result(sid)
                        data = result.get("data") if isinstance(result, dict) else None
                        if data and isinstance(data, dict):
                            return data
                    except ApiError:
                        pass
                elif not sid:
                    # Session completed but we don't have session_id
                    # Try to discover it (unlikely to work since bk- is now invalid)
                    pass

        # If we detected scoring but don't have sid, try to discover it
        if scoring_detected and not sid:
            sid = _try_extract_session_id()

        time.sleep(interval)

    raise TimeoutError(f"Scoring did not complete within {timeout}s")
