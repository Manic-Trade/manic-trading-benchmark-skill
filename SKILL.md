# Manic Trading Benchmark Skill

> Evaluate AI trading agents across 5 standardized tasks on a sandbox trading engine with real market prices.

## Overview

This skill runs a complete trading agent benchmark on the **Manic Trade** platform. The benchmark evaluates 5 core dimensions through sequential tasks:

| Task | Dimension | Duration |
|------|-----------|----------|
| T1 — Market Snapshot | Real-time Data Acquisition | ~30s |
| T2 — Multi-source Intelligence | Multi-source Intel Gathering | ~60s |
| T3 — Market Analysis | Analytical Reasoning | ~90s |
| T4 — Trading Decision & Execution | Trading Decision Quality | ~30s |
| T5 — Risk Management | Risk Control Discipline | ~60s |

**Scoring**: Each task is scored by a dual-layer engine (Rule Engine + LLM Judge) across 5 dimensions, totaling **0-100 points** with grades S/A/B/C/D.

## Quick Start

### Step 1: Install & Bind

```bash
npx manic-trading-benchmark@latest init
```

This will:
1. Check your Python 3.9+ environment
2. Install benchmark skill files
3. Prompt you for a **pair code** (get it from [manic.trade/benchmark](https://manic.trade/benchmark))
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

### The 5 Tasks

**T1 — Market Snapshot**: Fetch real-time prices for BTC, ETH, SOL, and an obscure token (龙虾). Tests data accuracy, source citation, and completeness.

**T2 — Multi-source Intelligence**: Gather BTC market data from 4 dimensions — derivatives (Binance Futures), on-chain (CoinGecko), news (CryptoPanic), and sentiment (Fear & Greed Index). Synthesize into a directional recommendation.

**T3 — Market Analysis**: Analyze pre-built market packets with mixed signals. Two-stage evaluation: (1) initial thesis extraction, (2) response to perturbation/new information. Tests analytical rigor without external data access.

**T4 — Trading Decision & Execution**: Formulate a concrete trading plan based on T1-T2 intelligence, then execute it on the sandbox. Tests plan specificity, parameter consistency, and execution quality.

**T5 — Risk Management**: Evaluate pre-set positions (one winning, one losing), make close/hold decisions, and define stop-loss thresholds and reversal signals. Tests risk discipline and reasoning quality.

### Scoring

Each task produces a score through:
- **Part A (0-8)**: Rule engine — objective checks (price accuracy, API coverage, JSON validity, execution success, position management)
- **Part B (0-12)**: LLM Judge — qualitative evaluation (reasoning depth, analysis quality, decision coherence)

**5 Dimensions × 20 points each = 100 total**

| Grade | Score | Meaning |
|-------|-------|---------|
| S | 90-100 | Elite — Top-tier trading agent |
| A | 80-89 | Strong — Production-ready |
| B | 70-79 | Solid — Good with standout areas |
| C | 60-69 | Basic — Functional with weaknesses |
| D | <60 | Needs improvement |

## API Reference

See [references/trading-api.md](references/trading-api.md) for complete Sandbox API documentation.

## Requirements

- **Node.js** >= 16 (for npx init)
- **Python** >= 3.9 (for benchmark runner)
- **Network access** to benchmark-api.manic.trade and external APIs (Binance, CoinGecko, etc.)
