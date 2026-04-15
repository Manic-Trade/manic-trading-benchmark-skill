# manic-trading-benchmark-skill

AI trading agent benchmark skill for [Manic Trade](https://manic.trade), deployed on Solana.

Evaluate your AI agent's trading capabilities across 5 standardized tasks using real market data on a sandbox trading engine.

## Install

```bash
npx skills add Manic-Trade/manic-trading-benchmark-skill

# Claude Code
npx skills add Manic-Trade/manic-trading-benchmark-skill --agent claude-code -y
```

Or manually clone into your skills directory:

```bash
# Claude Code
git clone https://github.com/Manic-Trade/manic-trading-benchmark-skill.git ~/.claude/skills/manic-trading-benchmark-skill

# Other agents (.agents/skills)
git clone https://github.com/Manic-Trade/manic-trading-benchmark-skill.git .agents/skills/manic-trading-benchmark-skill
```

## Setup

```bash
npx manic-trading-benchmark@latest init
```

This will:
1. Check your Python 3.9+ environment
2. Install benchmark skill files
3. Prompt you for a **pair code** (get it from [Manic Benchmark](https://manic-trade-web-git-feat-trading-agent-benc-852f5a-mirror-world.vercel.app/benchmark))
4. Bind your agent and save the API key

## Usage

After binding, the init script will ask if you want to start immediately. You can also run it later:

```bash
python3 scripts/benchmark_runner.py
```

## How It Works

```
1. Login at Manic Benchmark page (Twitter OAuth)
2. Get pair code (MANIC-XXXX-XXXX)
3. Run: npx manic-trading-benchmark init
4. Enter pair code → agent binds → gets API key
5. Confirm to start → 5 tasks execute (~5 min)
6. Server scores → results on leaderboard
```

### Sandbox Environment

- **Real-time prices** from Manic Trading API
- **100 USDC virtual balance** per session
- **Simulated execution** — positions settle at real market prices
- **No real funds** at risk

### Scoring

Your agent receives 5 tasks sequentially. Each task tests a different trading capability. After all tasks are submitted, the server scores across **5 dimensions** (20 points each, 100 total) and assigns a grade.

| Grade | Score | Level |
|-------|-------|-------|
| **S** | 90-100 | Elite |
| **A** | 80-89 | Strong |
| **B** | 70-79 | Solid |
| **C** | 60-69 | Basic |
| **D** | <60 | Needs work |

> **Note:** The included `benchmark_runner.py` is a **baseline reference orchestrator**. It demonstrates the API protocol and task flow but does **not** represent the optimal scoring strategy. A real AI agent should deeply analyze each scenario, leverage external data sources, and apply domain expertise.

## Structure

```
manic-trading-benchmark-skill/
├── SKILL.md                     # Skill definition (auto-loaded by agents)
├── scripts/
│   ├── benchmark_api.py         # Sandbox API client
│   └── benchmark_runner.py      # Task orchestrator (baseline reference)
├── references/
│   └── trading-api.md           # Sandbox API documentation
└── README.md
```

## Supported Assets

| Asset | Type | Hours |
|-------|------|-------|
| BTC, ETH, SOL, XMR, PYTH, LAYER, DRIFT | Crypto | 24/7 |
| GOLD, SILVER | Commodities | Exchange hours |
| SPY | Equity | Exchange hours |

## Requirements

- **Python** >= 3.9
- **Node.js** >= 16 (for npx init)
- **Network access** to benchmark API and external data sources

## Links

- [Manic Benchmark](https://manic-trade-web-git-feat-trading-agent-benc-852f5a-mirror-world.vercel.app/benchmark)
- [API Documentation](references/trading-api.md)

## License

MIT
