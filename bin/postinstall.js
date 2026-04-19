#!/usr/bin/env node

const c = {
  reset: "\x1b[0m",
  bold: "\x1b[1m",
  dim: "\x1b[2m",
  green: "\x1b[32m",
  cyan: "\x1b[36m",
  yellow: "\x1b[33m",
};

console.log(`
${c.green}${c.bold}✓ Manic Trading Benchmark skill installed.${c.reset}

${c.yellow}${c.bold}Next step:${c.reset} Run the setup command to pair your agent:

  ${c.cyan}npx manic-trading-benchmark${c.reset}

${c.dim}This will guide you through getting a pair code and binding your agent.${c.reset}
`);
