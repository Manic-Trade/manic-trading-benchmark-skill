#!/usr/bin/env node

const { execSync } = require("child_process");
const readline = require("readline");
const path = require("path");
const fs = require("fs");

// ─── Constants ───────────────────────────────────────────────────────────────

const BENCHMARK_SERVER_BASE = "https://benchmark-api-alpha.manic.trade";
const MIN_PYTHON_VERSION = [3, 9];

// ─── Colors ──────────────────────────────────────────────────────────────────

const c = {
  reset: "\x1b[0m",
  bold: "\x1b[1m",
  dim: "\x1b[2m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  cyan: "\x1b[36m",
};

function banner() {
  console.log(`
${c.cyan}${c.bold}  ╔══════════════════════════════════════════════════╗
  ║                                                  ║
  ║     🚀  Manic Trading Agent Benchmark  🚀       ║
  ║                                                  ║
  ║     Evaluate your AI agent's trading skills      ║
  ║     across 5 standardized trading tasks          ║
  ║                                                  ║
  ╚══════════════════════════════════════════════════╝${c.reset}
`);
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function ask(question) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

// ─── Step 1: Check Python ────────────────────────────────────────────────────

function checkPython() {
  console.log(`${c.blue}[1/3]${c.reset} Checking Python environment...`);

  const candidates = ["python3", "python"];
  for (const cmd of candidates) {
    try {
      const version = execSync(`${cmd} --version 2>&1`, {
        encoding: "utf-8",
      }).trim();
      const match = version.match(/Python (\d+)\.(\d+)\.(\d+)/);
      if (match) {
        const major = parseInt(match[1]);
        const minor = parseInt(match[2]);
        if (
          major > MIN_PYTHON_VERSION[0] ||
          (major === MIN_PYTHON_VERSION[0] && minor >= MIN_PYTHON_VERSION[1])
        ) {
          console.log(`  ${c.green}✓${c.reset} Found ${version} (${cmd})`);
          return cmd;
        }
      }
    } catch {}
  }

  console.error(
    `\n  ${c.red}✗ Python ${MIN_PYTHON_VERSION.join(".")}+ is required but not found.${c.reset}`
  );
  console.error(
    `  Install from: ${c.cyan}https://www.python.org/downloads/${c.reset}\n`
  );
  process.exit(1);
}

// ─── Step 2: Install Skill Files ─────────────────────────────────────────────

function installSkillFiles() {
  console.log(
    `${c.blue}[2/3]${c.reset} Installing benchmark skill files...`
  );

  const pkgRoot = path.resolve(__dirname, "..");
  const targetDir = process.cwd();

  const filesToCopy = [
    { src: "SKILL.md", dest: "SKILL.md" },
    { src: "scripts/benchmark_api.py", dest: "scripts/benchmark_api.py" },
    {
      src: "scripts/benchmark_runner.py",
      dest: "scripts/benchmark_runner.py",
    },
    {
      src: "references/trading-api.md",
      dest: "references/trading-api.md",
    },
  ];

  for (const file of filesToCopy) {
    const srcPath = path.join(pkgRoot, file.src);
    const destPath = path.join(targetDir, file.dest);

    fs.mkdirSync(path.dirname(destPath), { recursive: true });

    if (fs.existsSync(srcPath)) {
      fs.copyFileSync(srcPath, destPath);
      console.log(`  ${c.green}✓${c.reset} ${file.dest}`);
    } else {
      console.log(`  ${c.yellow}⚠${c.reset} ${file.src} not found in package, skipping`);
    }
  }

  // Install Python dependencies
  console.log(`\n  Installing Python dependencies...`);
  const pyDeps = ["requests", "python-dotenv"];
  for (const dep of pyDeps) {
    try {
      execSync(`pip3 install ${dep} 2>&1`, { encoding: "utf-8", stdio: "pipe" });
      console.log(`  ${c.green}✓${c.reset} ${dep}`);
    } catch {
      console.log(`  ${c.yellow}⚠${c.reset} Could not install ${dep} — run: pip3 install ${dep}`);
    }
  }
}

// ─── Step 3: Save Pair Code ──────────────────────────────────────────────────

async function savePairCode() {
  console.log(
    `\n${c.blue}[3/3]${c.reset} Pair code setup`
  );

  const envPath = path.join(process.cwd(), ".env");

  // Check if .env already has a pair code
  if (fs.existsSync(envPath)) {
    const existing = fs.readFileSync(envPath, "utf-8");
    const match = existing.match(/^BENCHMARK_PAIR_CODE=(MANIC-[A-Z0-9]{4}-[A-Z0-9]{4})$/m);
    if (match) {
      console.log(`  ${c.green}✓${c.reset} Pair code already configured: ${c.dim}${match[1]}${c.reset}`);
      console.log(`\n  ${c.green}Setup complete!${c.reset} Your AI agent will handle binding automatically when you start a benchmark run.\n`);
      return;
    }
  }

  console.log(
    `\n  ${c.dim}Get your pair code from: ${c.cyan}https://benchmark.manic.trade${c.reset}`
  );
  console.log(
    `  ${c.dim}Login with Twitter → Fill in Agent Name → Copy the pair code${c.reset}\n`
  );

  const pairCode = await ask(
    `  ${c.yellow}?${c.reset} Enter your pair code (e.g. MANIC-XXXX-XXXX): `
  );

  if (!pairCode || !pairCode.match(/^MANIC-[A-Z0-9]{4}-[A-Z0-9]{4}$/)) {
    console.error(
      `\n  ${c.red}✗ Invalid pair code format. Expected: MANIC-XXXX-XXXX${c.reset}\n`
    );
    process.exit(1);
  }

  const envContent = [
    `# Manic Trading Benchmark Configuration`,
    `# Generated at ${new Date().toISOString()}`,
    `BENCHMARK_PAIR_CODE=${pairCode}`,
    `BENCHMARK_SERVER_BASE=${BENCHMARK_SERVER_BASE}`,
    "",
  ].join("\n");

  fs.writeFileSync(envPath, envContent);

  console.log(`  ${c.green}✓${c.reset} Pair code saved to .env`);
  console.log(`\n  ${c.green}Setup complete!${c.reset} Your AI agent will handle binding automatically when you start a benchmark run.\n`);
}

// ─── Main ────────────────────────────────────────────────────────────────────

async function main() {
  banner();

  checkPython();
  installSkillFiles();
  await savePairCode();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
