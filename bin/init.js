#!/usr/bin/env node

const { execSync, spawn } = require("child_process");
const readline = require("readline");
const path = require("path");
const fs = require("fs");
const https = require("https");
const http = require("http");

// ─── Constants ───────────────────────────────────────────────────────────────

const BENCHMARK_API_BASE = "https://benchmark-api.manic.trade";
const BIND_ENDPOINT = `${BENCHMARK_API_BASE}/benchmark/bind`;
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
  magenta: "\x1b[35m",
  cyan: "\x1b[36m",
  white: "\x1b[37m",
  bgBlue: "\x1b[44m",
  bgGreen: "\x1b[42m",
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

function httpPost(url, body) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const parsed = new URL(url);
    const mod = parsed.protocol === "https:" ? https : http;

    const req = mod.request(
      {
        hostname: parsed.hostname,
        port: parsed.port,
        path: parsed.pathname + parsed.search,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(data),
        },
      },
      (res) => {
        let body = "";
        res.on("data", (chunk) => (body += chunk));
        res.on("end", () => {
          try {
            resolve({ status: res.statusCode, data: JSON.parse(body) });
          } catch {
            resolve({ status: res.statusCode, data: body });
          }
        });
      }
    );
    req.on("error", reject);
    req.write(data);
    req.end();
  });
}

// ─── Step 1: Check Python ────────────────────────────────────────────────────

function checkPython() {
  console.log(`${c.blue}[1/4]${c.reset} Checking Python environment...`);

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
    `${c.blue}[2/4]${c.reset} Installing benchmark skill files...`
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

// ─── Step 3: Pair Code Binding ───────────────────────────────────────────────

async function bindAgent() {
  console.log(
    `\n${c.blue}[3/4]${c.reset} Agent binding`
  );
  console.log(
    `\n  ${c.dim}Get your pair code from: ${c.cyan}https://manic.trade/benchmark${c.reset}`
  );
  console.log(
    `  ${c.dim}Login with Twitter → Fill in Bot Name → Copy the pair code${c.reset}\n`
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

  const agentName =
    (await ask(
      `  ${c.yellow}?${c.reset} Agent name (optional, press Enter to skip): `
    )) || "Manic Benchmark Agent";

  const agentDescription =
    (await ask(
      `  ${c.yellow}?${c.reset} Agent description (optional, press Enter to skip): `
    )) || "";

  console.log(`\n  Binding agent...`);

  try {
    const res = await httpPost(BIND_ENDPOINT, {
      pair_code: pairCode,
      agent_name: agentName,
      description: agentDescription || undefined,
    });

    if (res.status !== 200 && res.status !== 201) {
      const msg =
        res.data?.message || res.data?.error || JSON.stringify(res.data);
      console.error(`\n  ${c.red}✗ Binding failed: ${msg}${c.reset}\n`);
      process.exit(1);
    }

    const apiKey = res.data?.data?.api_key || res.data?.api_key;
    const sandboxBaseUrl =
      res.data?.data?.sandbox_base_url ||
      res.data?.sandbox_base_url ||
      `${BENCHMARK_API_BASE}/agent`;

    if (!apiKey) {
      console.error(
        `\n  ${c.red}✗ No API key returned from server.${c.reset}\n`
      );
      console.error(`  Response: ${JSON.stringify(res.data, null, 2)}\n`);
      process.exit(1);
    }

    // Write .env
    const envPath = path.join(process.cwd(), ".env");
    const envContent = [
      `# Manic Trading Benchmark Configuration`,
      `# Generated at ${new Date().toISOString()}`,
      `BENCHMARK_API_KEY=${apiKey}`,
      `BENCHMARK_API_BASE=${sandboxBaseUrl}`,
      `BENCHMARK_SERVER_BASE=${BENCHMARK_API_BASE}`,
      "",
    ].join("\n");

    fs.writeFileSync(envPath, envContent);

    console.log(`  ${c.green}✓${c.reset} Agent bound successfully!`);
    console.log(`  ${c.green}✓${c.reset} API key saved to .env`);
    console.log(
      `  ${c.dim}  Key: ${apiKey.substring(0, 10)}...${c.reset}`
    );

    return { apiKey, sandboxBaseUrl };
  } catch (err) {
    console.error(
      `\n  ${c.red}✗ Network error: ${err.message}${c.reset}\n`
    );
    process.exit(1);
  }
}

// ─── Step 4: Run Benchmark ───────────────────────────────────────────────────

async function runBenchmark(pythonCmd) {
  console.log(
    `\n${c.blue}[4/4]${c.reset} Ready to start benchmark`
  );
  console.log(`
  ${c.bold}The benchmark will evaluate your agent across 5 tasks:${c.reset}
  ${c.dim}┌─────────────────────────────────────────────────┐
  │  T1  Market Snapshot        (~30s)  📊          │
  │  T2  Multi-source Intel     (~60s)  🔍          │
  │  T3  Market Analysis        (~90s)  🧠          │
  │  T4  Trading Decision       (~30s)  💹          │
  │  T5  Risk Management        (~60s)  🛡️           │
  └─────────────────────────────────────────────────┘${c.reset}
  ${c.dim}Total estimated time: ~5 minutes${c.reset}
`);

  const confirm = await ask(
    `  ${c.yellow}?${c.reset} Start the benchmark now? ${c.dim}[Y/n]${c.reset} `
  );

  if (confirm.toLowerCase() === "n") {
    console.log(
      `\n  ${c.dim}You can start the benchmark later by running:${c.reset}`
    );
    console.log(
      `  ${c.cyan}${pythonCmd} scripts/benchmark_runner.py${c.reset}\n`
    );
    process.exit(0);
  }

  console.log(`\n  ${c.green}Starting benchmark...${c.reset}\n`);

  const runnerPath = path.join(process.cwd(), "scripts", "benchmark_runner.py");

  return new Promise((resolve, reject) => {
    const child = spawn(pythonCmd, [runnerPath], {
      cwd: process.cwd(),
      stdio: "inherit",
      env: { ...process.env },
    });

    child.on("close", (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Benchmark runner exited with code ${code}`));
      }
    });

    child.on("error", (err) => {
      reject(err);
    });
  });
}

// ─── Main ────────────────────────────────────────────────────────────────────

async function main() {
  banner();

  const pythonCmd = checkPython();
  installSkillFiles();
  await bindAgent();

  try {
    await runBenchmark(pythonCmd);
  } catch (err) {
    console.error(`\n  ${c.red}✗ Benchmark failed: ${err.message}${c.reset}\n`);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
