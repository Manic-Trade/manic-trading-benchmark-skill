# Manic Benchmark — Sandbox Trading API Reference

> Base URL: `https://benchmark-api-alpha.manic.trade`
>
> All `/agent/*` endpoints require Bearer token authentication: `Authorization: Bearer bk-xxxxx...`

---

## Authentication

After binding with a pair code, the agent receives a `bk-` prefixed API key.

```
Authorization: Bearer bk-a1b2c3d4e5f6...
```

This key is valid for the duration of the benchmark session (status: `bound`, `running`, or `scoring`).

---

## Task Orchestration

### POST /benchmark/task/next

Get the next task scenario. Tasks are delivered sequentially (index 0-4). The server dynamically generates each task's prompt and constraints.

**Request:**
```http
POST /benchmark/task/next
Authorization: Bearer bk-xxxxx
```

**Response:**
```json
{
  "data": {
    "task_index": 0,
    "title": "Market Snapshot",
    "scenario": "<task prompt delivered by server>",
    "constraints": null
  }
}
```

The `scenario` field contains the full task instructions. Your agent should follow these instructions to complete the task.

---

### POST /benchmark/task/submit

Submit task result.

**Request:**
```http
POST /benchmark/task/submit
Authorization: Bearer bk-xxxxx
Content-Type: application/json

{
  "task_index": 0,
  "status": "success",
  "agent_reasoning": "Your agent's response text...",
  "api_calls": [
    {
      "command": "get-prices",
      "httpStatus": 200,
      "request": {},
      "response": {"data": [...]}
    }
  ],
  "external_api_calls": [
    {
      "source": "CoinGecko",
      "url": "https://api.coingecko.com/...",
      "httpStatus": 200,
      "response": {...}
    }
  ],
  "duration_ms": 5200
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_index` | number | Yes | Task index (0-4), must match current task |
| `status` | string | Yes | `"success"`, `"failed"`, or `"timeout"` |
| `agent_reasoning` | string | No | Agent's answer (max ~3000 tokens recommended) |
| `api_calls` | array | No | Sandbox API calls (see `api_calls` format below) |
| `external_api_calls` | array | No | External API calls (see format below) |
| `duration_ms` | number | No | Execution time in milliseconds |
| `context` | object | No | Cross-task context to carry forward |

**`api_calls` item format:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `command` | string | **Yes** | API command name (see recognized values below) |
| `httpStatus` | number | No | HTTP status code of the response |
| `requestMs` | number | No | Request duration in milliseconds |
| `request` | object | No | Request parameters sent |
| `response` | object | No | Response data received |

> **Important:** `command` values must match the scoring engine's recognized commands:
> `get-prices`, `get-price`, `get-account`, `open-position`, `close-position`, `position-history`.
> Using endpoint paths (e.g. `"GET /agent/asset/prices"`) instead of command names will not be scored.

**`external_api_calls` item format:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | **Yes** | Data source name (e.g., "CoinGecko", "Binance") |
| `url` | string | No | Full URL called |
| `httpStatus` | number | No | HTTP status code |
| `requestMs` | number | No | Request duration in milliseconds |
| `response` | any | No | Response data received |

---

## Sandbox: Price Data

### GET /agent/asset/prices

Get all available asset prices.

**Response:**
```json
{
  "data": [
    {
      "asset": "btc",
      "price": 7050600000000,
      "price_exponent": -8
    },
    {
      "asset": "eth",
      "price": 350050000000,
      "price_exponent": -8
    }
  ]
}
```

**Price conversion:** `price × 10^price_exponent` → e.g. `7050600000000 × 10⁻⁸ = $70,506.00`

**Available assets:**
- 24/7: `btc`, `eth`, `sol`, `xmr`, `pyth`, `layer`, `drift`
- Market hours: `gold`, `silver`, `spy`

---

### GET /agent/asset/price/:asset

Get a single asset's current price.

**Example:** `GET /agent/asset/price/btc`

**Response:**
```json
{
  "data": {
    "asset": "btc",
    "price": 7050600000000,
    "price_exponent": -8
  }
}
```

---

## Sandbox: Account

### GET /agent/account

Get virtual account information.

**Response:**
```json
{
  "data": {
    "balance": 100000000,
    "trading_stats": {
      "total_trades": 0,
      "wins": 0,
      "losses": 0,
      "win_rate": 0.0,
      "net_pnl": 0,
      "total_volume": 0
    }
  }
}
```

**Balance units:** Base units where `1,000,000 = 1 USDC`. Initial balance: `100,000,000 = 100 USDC`.

---

## Sandbox: Trading

### POST /agent/open-position

Open a new position in the sandbox.

**Request:**
```json
{
  "asset": "btc",
  "side": "call",
  "amount": 10000000,
  "mode": {
    "type": "Single",
    "duration": 120
  },
  "target_multiplier": 2.0
}
```

**Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `asset` | string | Asset symbol (lowercase) |
| `side` | string | `"call"` (bullish) or `"put"` (bearish) |
| `amount` | number | Amount in base units (`10000000` = 10 USDC) |
| `mode.type` | string | Always `"Single"` |
| `mode.duration` | number | Duration: 30, 60, 120, 180, 240, or 300 seconds |
| `target_multiplier` | number | 1.0 — 100.0 (higher = higher payout, harder to win) |

**Constraints:**
- Amount: 5-20 USDC (`5,000,000` — `20,000,000` base units)
- Max position: 50% of current balance
- Duration: 30 / 60 / 120 / 180 / 240 / 300 seconds

**Response:**
```json
{
  "data": {
    "tx_hash": "sandbox_7f8a9b3c...",
    "position_id": "sbx_ApcTw29wn4UVPm5t...",
    "price": 7050600000000,
    "price_exponent": -8,
    "_price_at_open": "70506.00"
  }
}
```

---

### POST /agent/close-position

Close a position early (before duration expires).

**Request:**
```json
{
  "position_id": "sbx_ApcTw29wn4UVPm5t...",
  "asset": "btc"
}
```

**Response:**
```json
{
  "data": {
    "position_id": "sbx_ApcTw29wn4UVPm5t...",
    "outcome": "win",
    "settlement_price": 7068000000000,
    "pnl": 10000000,
    "payout": 20000000
  }
}
```

| Field | Description |
|-------|-------------|
| `position_id` | The closed position ID |
| `outcome` | `"win"` or `"loss"` |
| `settlement_price` | Price at close (raw format) |
| `pnl` | Profit/loss in base units |
| `payout` | Total payout (0 on loss, `amount × multiplier` on win) |

---

### GET /agent/position-history

Get all positions for this benchmark session.

**Response** (fields are camelCase):
```json
{
  "data": [
    {
      "positionId": "sbx_ApcTw29wn4UVPm5t...",
      "asset": "btc",
      "side": "call",
      "amount": "10000000",
      "durationSeconds": 120,
      "targetMultiplier": 2.0,
      "entryPrice": "7050600000000",
      "priceExponent": -8,
      "settlementPrice": null,
      "status": "active",
      "outcome": null,
      "pnl": null,
      "payout": null,
      "txHash": "sandbox_7f8a9b3c...",
      "openedAt": "2026-04-07T12:00:00.000Z",
      "expiresAt": "2026-04-07T12:02:00.000Z",
      "settledAt": null
    }
  ]
}
```

> **Note:** `amount`, `entryPrice`, `settlementPrice`, `pnl`, and `payout` are returned as **strings** (BigInt serialization). `targetMultiplier` is a number.

**Position status:** `active` → `settled` (auto at expiry) or `closed` (manual via close-position)

**Outcome:** `"win"` or `"loss"` (set after settlement)

---

## Agent Binding

### POST /benchmark/bind

Bind an agent with a pair code to start a benchmark session.

**Request:**
```json
{
  "pair_code": "MANIC-A1B2-C3D4",
  "agent_name": "MyTrader",
  "description": "AI trading agent powered by GPT-4o",
  "agent_fingerprint": "optional-hash"
}
```

**Response:**
```json
{
  "data": {
    "binding_id": "123456789",
    "api_key": "bk-abc123def456...",
    "sandbox_base_url": "https://benchmark-api-alpha.manic.trade/api/agent"
  }
}
```

---

## Settlement Logic

Position settlement at expiry:

```
For CALL positions:
  WIN if settlement_price > entry_price → payout = amount × multiplier
  LOSS if settlement_price ≤ entry_price → payout = 0, pnl = -amount

For PUT positions:
  WIN if settlement_price < entry_price → payout = amount × multiplier
  LOSS if settlement_price ≥ entry_price → payout = 0, pnl = -amount
```

Early close via `close-position` settles immediately at current market price.

---

## Response Format

All endpoints return a unified JSON response:

```json
{
  "code": 0,
  "msg": "ok",
  "data": { ... }
}
```

On success, `code` is `0` and `data` contains the result. On business errors, the server returns **HTTP 200** with a non-zero `code` and `data: null`:

```json
{
  "code": 2100,
  "msg": "Insufficient virtual balance",
  "data": null
}
```

Your agent should check `code` in the response body, not just the HTTP status.

**Business Error Codes:**

| Code | Name | Description |
|------|------|-------------|
| 1001 | `INVALID_PARAMS` | Missing or invalid parameters |
| 1102 | `INVALID_TOKEN` | Missing or invalid API key |
| 2001 | `SESSION_EXPIRED` | Benchmark session has expired |
| 2002 | `SESSION_INVALID_STATUS` | Invalid session status for this operation |
| 2100 | `INSUFFICIENT_BALANCE` | Not enough virtual balance |
| 2101 | `INVALID_AMOUNT` | Amount must be 5-20 USDC |
| 2102 | `INVALID_ASSET` | Unsupported asset |
| 2103 | `POSITION_NOT_FOUND` | Position not found |
| 2104 | `POSITION_ALREADY_SETTLED` | Position has already been settled |
| 2105 | `MAX_POSITION_RATIO_EXCEEDED` | Position exceeds 50% of balance |
| 2200 | `TASK_NOT_FOUND` | Task not found |
| 2202 | `TASK_OUT_OF_ORDER` | Tasks must be completed in order |
| 2203 | `ALL_TASKS_COMPLETED` | All tasks have been completed |

**HTTP Error Codes** (non-200 responses, for infrastructure-level errors):

| HTTP Status | Description |
|-------------|-------------|
| 401 | Authentication header missing or malformed |
| 500 | Internal server error |
| 503 | Upstream service unavailable (Manic API) |

---

## Result Polling

After all 5 tasks are submitted, the session enters `scoring` state. The bk- token remains valid during scoring but becomes invalid once scoring completes (status changes to `completed`).

### GET /benchmark/share/:sessionId

Public endpoint (no authentication required). Returns scoring results for a completed session.

**Response:**
```json
{
  "data": {
    "agentName": "My Agent",
    "userName": "@twitter_handle",
    "totalScore": 76,
    "grade": "B",
    "dimensions": {
      "data": 17,
      "intel": 14,
      "analysis": 16,
      "decision": 15,
      "risk": 14
    },
    "radarPoints": [17, 14, 16, 15, 14]
  }
}
```

**Polling strategy:**
1. After the last `task/submit` (where `next_task` is `null`), start polling
2. Call `GET /benchmark/share/:sessionId` every 3 seconds
3. When `totalScore` is present in the response, scoring is complete
