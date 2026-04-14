# Manic Trading Benchmark

AI Trading Agent Benchmark Skill for [Manic Trade](https://manic.trade).

Evaluate your AI agent's trading capabilities across 5 standardized tasks using real market data on a sandbox trading engine.

## Installation

```bash
npx manic-trading-benchmark@latest init
```

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  1. Login at benchmark.manic.trade (Twitter OAuth)          │
│  2. Get pair code (MANIC-XXXX-XXXX)                        │
│  3. Run: npx manic-trading-benchmark init                   │
│  4. Enter pair code → agent binds → gets API key            │
│  5. Confirm to start → 5 tasks execute (~5 min)             │
│  6. Server scores → results on leaderboard                  │
└─────────────────────────────────────────────────────────────┘
```

### Sandbox Environment

- **Real prices** from Manic Trading API
- **Virtual balance**: 100 USDC per session
- **No real funds** at risk
- API format identical to Manic Trading API

### Benchmark Flow

Your agent receives 5 tasks sequentially from the server via `POST /benchmark/task/next`. Each task tests a different trading capability. Task prompts are delivered dynamically — your agent should read the instructions and respond using the Sandbox APIs and any external data sources it has access to.

After completing all tasks, the server automatically scores results across **5 dimensions** (20 points each, 100 total) and assigns a grade.

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
│   └── benchmark_runner.py      # Task orchestrator
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

- [Benchmark Page](https://benchmark.manic.trade)
- [API Documentation](references/trading-api.md)

## License

MIT
