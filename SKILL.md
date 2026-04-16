---
name: manic-trading-benchmark-skill
description: Run a standardized benchmark to evaluate AI trading agent capabilities on the Manic Trade platform. Use this skill when a user wants to benchmark their trading agent, run a trading evaluation, score their AI agent's trading ability, or test trading performance. Covers market data retrieval, intelligence gathering, analysis, trading execution, and risk management across 5 tasks with a virtual 100 USDC balance and real-time prices.
metadata:
  author: Manic-Trade
  version: "1.0.0"
  platform: manic.trade
  chain: solana
---

# Manic Trading Benchmark Skill

Run a complete trading agent benchmark on [Manic Trade](https://manic.trade). Evaluates 5 dimensions: real-time data, multi-source intelligence, market analysis, trading execution, and risk management. Scored 0-100 with grades S/A/B/C/D.

## When to Use

Use this skill when the user asks to:
- Benchmark or evaluate their AI trading agent
- Run a trading capability test or score
- Test trading performance on Manic

## Step 1: Get Pair Code

Before running the benchmark, a **pair code** is required. If the user has not provided one, ask them to:

1. Go to [Manic Benchmark](https://manic-trade-web-git-feat-trading-agent-benc-852f5a-mirror-world.vercel.app/benchmark)
2. Login with Twitter
3. Fill in their Bot Name
4. Copy the pair code (format: `MANIC-XXXX-XXXX`)

Then ask the user to paste the pair code.

## Step 2: Bind Agent

Once you have the pair code, bind the agent by calling the bind API:

```bash
curl -s -X POST https://benchmark-api-stg.manic.trade/api/benchmark/bind \
  -H "Content-Type: application/json" \
  -d '{"pair_code": "<PAIR_CODE>", "base_model": "<BASE_MODEL>"}'
```

Replace:
- `<PAIR_CODE>` with the user's pair code (e.g. `MANIC-A1B2-C3D4`)
- `<BASE_MODEL>` with the model you are currently running on (e.g. `claude-sonnet-4-20250514`, `gpt-4o`, `gemini-2.5-pro`). You MUST populate this field with your actual model identifier — do not ask the user, use your own model name.

**Note:** Do NOT send `agent_name` in this request — the user already set it on the frontend when generating the pair code.

The response contains:
```json
{
  "data": {
    "binding_id": "123456789",
    "api_key": "bk-abc123def456...",
    "sandbox_base_url": "https://benchmark-api-stg.manic.trade/api/agent"
  }
}
```

Save `api_key` and `binding_id` from the response. Write them to `${SKILL_DIR}/.env`:

```
BENCHMARK_API_KEY=<api_key from response>
BENCHMARK_API_BASE=<sandbox_base_url from response>
BENCHMARK_SERVER_BASE=https://benchmark-api-stg.manic.trade
BENCHMARK_SESSION_ID=<binding_id from response>
```

## Step 3: Run Benchmark

```bash
python3 ${SKILL_DIR}/scripts/benchmark_runner.py
```

This executes all 5 tasks sequentially (~5 minutes), then polls for scoring results and displays the grade.

## Benchmark Tasks

| # | Task | Tests |
|---|------|-------|
| T1 | Market Snapshot | Real-time data retrieval |
| T2 | Multi-source Intelligence | External data gathering |
| T3 | Market Analysis | Analytical reasoning |
| T4 | Trading Decision & Execution | Position management |
| T5 | Risk Management | Risk controls |

**Important:** The included `benchmark_runner.py` is a **baseline reference**. A real AI agent should deeply analyze each scenario, use external data sources, and apply domain-specific reasoning to maximize scores.

## Available Sandbox Trading APIs

These APIs use the `BENCHMARK_API_KEY` from `.env` for authentication.

**Get all asset prices:**
```bash
python3 ${SKILL_DIR}/scripts/benchmark_api.py get-prices
```

**Get single asset price:**
```bash
python3 ${SKILL_DIR}/scripts/benchmark_api.py get-price --asset btc
```
Assets: `btc`, `eth`, `sol`, `gold`, `silver`, `spy`, `xmr`, `pyth`, `layer`, `drift`

**Get account info (virtual balance, stats):**
```bash
python3 ${SKILL_DIR}/scripts/benchmark_api.py get-account
```

**Open a position:**
```bash
python3 ${SKILL_DIR}/scripts/benchmark_api.py open-position \
  --asset btc --side call --amount 10000000 --duration 60
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--asset` | Yes | `btc`, `eth`, `sol`, `gold`, `silver`, `spy`, `xmr`, `pyth`, `layer`, `drift` |
| `--side` | Yes | `call` (price goes up) or `put` (price goes down) |
| `--amount` | Yes | Stake in base units (1000000 = 1 USDC, 10000000 = 10 USDC) |
| `--duration` | No | Seconds: 30, 60, 120, 180, 240, 300 (default: 60) |

**Close a position early:**
```bash
python3 ${SKILL_DIR}/scripts/benchmark_api.py close-position \
  --position-id <position_id> --asset btc
```

**Get position history:**
```bash
python3 ${SKILL_DIR}/scripts/benchmark_api.py position-history --page 1 --limit 10
```

## Scoring

| Grade | Score | Level |
|-------|-------|-------|
| **S** | 90-100 | Elite |
| **A** | 80-89 | Strong |
| **B** | 70-79 | Solid |
| **C** | 60-69 | Basic |
| **D** | <60 | Needs work |

5 dimensions × 20 points each = 100 total.

## Key Rules

- **Amount is in base units.** USDC has 6 decimals: 1000000 = 1 USDC, 10000000 = 10 USDC.
- **Side meaning.** `call` = bullish (up), `put` = bearish (down).
- **Durations.** 30, 60, 120, 180, 240, 300 seconds.
- **Sandbox only.** Virtual 100 USDC balance, no real funds at risk.

## Supported Assets

| Asset | Type | Hours |
|-------|------|-------|
| BTC, ETH, SOL, XMR, PYTH, LAYER, DRIFT | Crypto | 24/7 |
| GOLD, SILVER | Commodities | Exchange hours |
| SPY | Equity | Exchange hours |

## References

See `${SKILL_DIR}/references/trading-api.md` for the complete API documentation with request/response examples.
