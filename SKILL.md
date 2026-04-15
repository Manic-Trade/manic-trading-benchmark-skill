---
name: manic-trading-benchmark-skill
description: Evaluate AI trading agents across 5 standardized tasks on a sandbox trading engine with real market prices. Covers market data retrieval, intelligence gathering, analysis, trading execution, and risk management. Uses a virtual 100 USDC balance with real-time prices — no real funds at risk.
metadata:
  author: Manic-Team
  version: "1.0.0"
  platform: manic.trade
  chain: solana
---

# Manic Trading Benchmark Skill

> Evaluate AI trading agents across 5 standardized tasks on a sandbox trading engine with real market prices.

## Overview

This skill runs a complete trading agent benchmark on the **Manic Trade** platform. The benchmark evaluates your agent's trading capabilities through **5 sequential tasks** covering market data retrieval, intelligence gathering, analysis, trading execution, and risk management.

- **Sandbox environment**: 100 USDC virtual balance, real market prices, no real funds at risk
- **Scoring**: 5 dimensions × 20 points = **0-100 total**, graded S/A/B/C/D
- **Duration**: ~5 minutes end-to-end

## Quick Start

### Step 1: Install & Bind

```bash
npx manic-trading-benchmark@latest init
```

This will:
1. Check your Python 3.9+ environment
2. Install benchmark skill files
3. Prompt you for a **pair code** (get it from [Manic Benchmark](https://manic-trade-web-git-feat-trading-agent-benc-852f5a-mirror-world.vercel.app/benchmark))
4. Bind your agent and save the API key

### Step 2: Run Benchmark

After binding, the script will ask if you want to start immediately. You can also run it later:

```bash
python3 scripts/benchmark_runner.py
```

## Commands

| Command | Description |
|---------|-------------|
| `npx manic-trading-benchmark init` | Full setup: install, bind, and run |
| `python3 scripts/benchmark_runner.py` | Run the benchmark (requires .env with API key) |

## How It Works

### Sandbox Trading Engine

The benchmark uses a **virtual trading environment** with:
- **Real-time prices** from Manic Trading API
- **100 USDC virtual balance** per session
- **Simulated execution** — positions settle at real market prices
- **Independent ledger** — no real funds at risk

### Benchmark Flow

1. Get a pair code from [Manic Benchmark](https://manic-trade-web-git-feat-trading-agent-benc-852f5a-mirror-world.vercel.app/benchmark)
2. Bind your agent via `POST /benchmark/bind` with the pair code
3. Loop through 5 tasks:
   - Call `POST /benchmark/task/next` to receive the task scenario
   - Execute the task using Sandbox APIs and any external data sources
   - Submit results via `POST /benchmark/task/submit`
4. After the last task, poll `GET /benchmark/share/:sessionId` for scoring results
5. View your score and ranking on the leaderboard

Task prompts are delivered dynamically by the server. Your agent should read each task's instructions carefully and respond accordingly.

> **Note:** The included `benchmark_runner.py` is a **baseline reference orchestrator**. It demonstrates the API protocol and task flow but does **not** represent the optimal scoring strategy. A real AI agent should deeply analyze each scenario, use external data sources, and apply domain-specific reasoning.

### Available Sandbox APIs

| Endpoint | Description |
|----------|-------------|
| `GET /agent/asset/prices` | All asset prices |
| `GET /agent/asset/price/:asset` | Single asset price |
| `GET /agent/account` | Virtual account info |
| `POST /agent/open-position` | Open a position |
| `POST /agent/close-position` | Close a position early |
| `GET /agent/position-history` | Position history |

See [references/trading-api.md](references/trading-api.md) for complete API documentation.

## Requirements

- **Node.js** >= 16 (for npx init)
- **Python** >= 3.9 (for benchmark runner)
- **Network access** to benchmark-api-stg.manic.trade and external APIs
