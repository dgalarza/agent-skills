#!/usr/bin/env node
// Quality-gate adapter for fallow (https://github.com/fallow-rs/fallow).
//
// Runs one fallow analysis and prints its findings as JSON Lines in the
// quality-gate contract: {"file", "line", "rule", "message"} per line.
//
//   node scripts/fallow-adapter.mjs complexity    # fallow health --complexity
//   node scripts/fallow-adapter.mjs duplication   # fallow dupes
//   node scripts/fallow-adapter.mjs dead-code     # fallow dead-code
//
// Extra arguments are passed through to fallow (for example `--production`
// or `--workspace web`). Thresholds, entry points, ignores, and rule
// severities come from the project's fallow config (.fallowrc.json).
//
// Fallow exits 1 when it has findings; that is expected. This adapter exits 0
// once fallow's JSON parses, and exits 2 when fallow fails (exit >= 2,
// missing binary, unparseable output), so a broken tool never reads as a pass.
//
// Messages are written so the engine's fingerprint stays stable: the first
// number in a message is the tracked metric (complexity value or duplicated
// lines) and line numbers are never part of the message.

import { spawnSync } from "node:child_process";

const COMMANDS = {
  complexity: ["health", "--complexity"],
  duplication: ["dupes"],
  "dead-code": ["dead-code"],
};

const NAME_KEYS = [
  "export_name",
  "member_name",
  "package_name",
  "binary_name",
  "specifier",
  "name",
];

function fail(message) {
  process.stderr.write(`fallow-adapter: ${message}\n`);
  process.exit(2);
}

function runFallow(args) {
  const npx = process.platform === "win32" ? "npx.cmd" : "npx";
  const proc = spawnSync(npx, ["--no-install", "fallow", ...args, "--format", "json", "--quiet"], {
    encoding: "utf8",
    maxBuffer: 256 * 1024 * 1024,
  });
  if (proc.error) fail(`could not run fallow: ${proc.error.message}`);
  if (proc.status !== 0 && proc.status !== 1) {
    fail(`fallow ${args[0]} exited ${proc.status}: ${(proc.stderr || proc.stdout).trim().split("\n").slice(-3).join(" / ")}`);
  }
  let data;
  try {
    data = JSON.parse(proc.stdout);
  } catch {
    fail(`fallow ${args[0]} did not print JSON: ${proc.stdout.slice(0, 200)}`);
  }
  if (data && data.error) fail(`fallow ${args[0]} reported an error: ${data.message}`);
  return data;
}

function emit(file, line, rule, message) {
  process.stdout.write(JSON.stringify({ file, line: line ?? null, rule, message }) + "\n");
}

function complexity(data) {
  const maxCyclomatic = data.summary?.max_cyclomatic_threshold ?? 20;
  const maxCognitive = data.summary?.max_cognitive_threshold ?? 15;
  for (const f of data.findings ?? []) {
    const name = f.name || "<anonymous>";
    if (typeof f.cyclomatic === "number" && f.cyclomatic > maxCyclomatic) {
      emit(f.path, f.line, "complexity-cyclomatic", `${f.cyclomatic} cyclomatic complexity in ${name}`);
    }
    if (typeof f.cognitive === "number" && f.cognitive > maxCognitive) {
      emit(f.path, f.line, "complexity-cognitive", `${f.cognitive} cognitive complexity in ${name}`);
    }
  }
}

function duplication(data) {
  for (const group of data.clone_groups ?? []) {
    const instances = group.instances ?? [];
    for (const inst of instances) {
      const others = [...new Set(instances.filter((o) => o !== inst).map((o) => o.file))].sort();
      const peers = others.length ? others.join(", ") : "itself";
      emit(inst.file, inst.start_line, "code-duplication", `${group.line_count} duplicated lines shared with ${peers}`);
    }
  }
}

// Every dead-code finding carries a finding_id ("dc1:<rule>:<hash>"). Only
// error-severity findings gate, so the project's `rules` config decides what
// blocks: a rule set to "warn" is reported by fallow but not by this adapter.
function isGatingFinding(item) {
  return Boolean(item?.finding_id) && (!item.effective_severity || item.effective_severity === "error");
}

function deadCodeFinding(item, fallbackRule) {
  const rule = item.finding_id.split(":")[1] || fallbackRule;
  const files = Array.isArray(item.files) ? item.files : [];
  const file = item.path || files[0] || "package.json";
  const name = NAME_KEYS.map((k) => item[k]).find((v) => typeof v === "string" && v);
  const subject = name || (files.length ? files.join(" -> ") : file);
  return { file, line: item.line, rule, message: `${rule.replace(/-/g, " ")}: ${subject}` };
}

function deadCode(data) {
  const lists = Object.entries(data).filter(([, items]) => Array.isArray(items));
  for (const [key, items] of lists) {
    for (const item of items.filter(isGatingFinding)) {
      const f = deadCodeFinding(item, key);
      emit(f.file, f.line, f.rule, f.message);
    }
  }
}

const check = process.argv[2];
if (!COMMANDS[check]) fail(`usage: fallow-adapter.mjs ${Object.keys(COMMANDS).join("|")} [fallow args...]`);
const data = runFallow([...COMMANDS[check], ...process.argv.slice(3)]);
({ complexity, duplication, "dead-code": deadCode })[check](data);
