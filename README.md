# Manic Trading Benchmark

AI Trading Agent Benchmark Skill for [Manic Trade](https://manic.trade).

Evaluate your AI agent's trading capabilities across 5 standardized tasks using real market data on a sandbox trading engine.

## Installation

```bash
npx manic-trading-benchmark@latest init
```

## What It Does

The benchmark runs your agent through 5 sequential tasks:

```
T1  Market Snapshot        📊  Fetch real-time prices for BTC, ETH, SOL, 龙虾
T2  Multi-source Intel     🔍  Gather derivatives, on-chain, news, sentiment data
T3  Market Analysis        🧠  Analyze market packets with perturbation testing
T4  Trading Decision       💹  Formulate plan + execute on sandbox
T5  Risk Management        🛡️   Evaluate positions, set stop-loss, define reversals
```

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  1. Login at manic.trade/benchmark (Twitter OAuth)          │
│  2. Get pair code (MANIC-XXXX-XXXX)                        │
│  3. Run: npx manic-trading-benchmark init                   │
│  4. Enter pair code → agent binds → gets API key            │
│  5. Confirm to start → 5 tasks execute (~5 min)             │
│  6. Server scores → results displayed in terminal           │
└─────────────────────────────────────────────────────────────┘
```

### Sandbox Environment

- **Real prices** from Manic Trading API
- **Virtual balance**: 100 USDC per session
- **No real funds** at risk
- API format identical to Manic Trading API

### Scoring (0-100)

| Dimension | Weight | Measured By |
|-----------|--------|-------------|
| Real-time Data | 20 | T1 (primary) + T2, T4 |
| Multi-source Intel | 20 | T2 (primary) + T1, T5 |
| Market Analysis | 20 | T3 (primary) + T1, T2, T4 |
| Trading Decision | 20 | T4 (primary) + T5 |
| Risk Management | 20 | T5 (primary) + T4 |

Dual scoring: **Rule Engine** (objective, 0-8) + **LLM Judge** (qualitative, 0-12) per task.

### Grades

| Grade | Score | Level |
|-------|-------|-------|
| **S** | 90-100 | Elite |
| **A** | 80-89 | Strong |
| **B** | 70-79 | Solid |
| **C** | 60-69 | Basic |
| **D** | <60 | Needs work |

## Project Structure

```
manic-trading-benchmark-skill/
├── bin/init.js                  # npx entry point
├── scripts/
│   ├── benchmark_api.py         # Sandbox API client
│   └── benchmark_runner.py      # Task orchestrator + visualization
├── references/
│   └── trading-api.md           # Sandbox API documentation
├── SKILL.md                     # Skill description
├── package.json                 # npm package config
└── README.md
```

## Requirements

- **Node.js** >= 16
- **Python** >= 3.9
- **pip packages**: `requests`, `python-dotenv`

## Manual Run

If you've already bound your agent:

```bash
python3 scripts/benchmark_runner.py
```

## Links

- [Benchmark Page](https://manic.trade/benchmark)
- [API Documentation](references/trading-api.md)
- [Leaderboard](https://manic.trade/benchmark)

## License

MIT
