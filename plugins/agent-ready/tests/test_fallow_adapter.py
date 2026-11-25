"""Tests for the fallow adapter (assets/fallow-adapter.mjs) shipped in agent-ready.

A fake `npx` on PATH replays canned fallow JSON, so the tests need Node.js but
not fallow or the network. They prove the adapter emits the quality-gate jsonl
contract, keeps fingerprints stable across line moves, tracks the metric, and
never turns a fallow failure into a pass.

Run:  python3 -m unittest discover -s plugins/agent-ready/tests -v
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ADAPTER = os.path.join(HERE, "..", "..", "..", "skills", "agent-ready", "assets", "fallow-adapter.mjs")

FAKE_NPX = """#!/bin/sh
# argv: --no-install fallow <subcommand> ... ; replay $FAKE_DIR/<subcommand>.json
cat "$FAKE_DIR/$3.json"
exit "${FAKE_EXIT:-1}"
"""

HEALTH = {
    "kind": "health",
    "summary": {"max_cyclomatic_threshold": 20, "max_cognitive_threshold": 15},
    "findings": [
        {"path": "src/util.ts", "name": "complex", "line": 3, "cyclomatic": 22, "cognitive": 21},
        {"path": "src/util.ts", "name": "nested", "line": 9, "cyclomatic": 8, "cognitive": 18},
        {"path": "src/ok.ts", "name": "crapOnly", "line": 1, "cyclomatic": 6, "cognitive": 4, "crap": 42.0},
    ],
}

DUPES = {
    "kind": "dupes",
    "clone_groups": [
        {"line_count": 8, "instances": [
            {"file": "src/a.ts", "start_line": 1, "end_line": 8},
            {"file": "src/b.ts", "start_line": 4, "end_line": 11},
        ]},
    ],
}

DEAD = {
    "kind": "dead-code",
    "total_issues": 4,
    "unused_files": [{"path": "src/orphan.ts", "finding_id": "dc1:unused-file:1", "effective_severity": "error"}],
    "unused_exports": [{"path": "src/util.ts", "export_name": "unusedExport", "line": 2,
                        "finding_id": "dc1:unused-export:2", "effective_severity": "error"}],
    "unused_dependencies": [{"package_name": "left-pad", "path": "package.json", "line": 1,
                             "finding_id": "dc1:unused-dependency:3", "effective_severity": "error"}],
    "unused_dev_dependencies": [{"package_name": "eslint", "path": "package.json", "line": 1,
                                 "finding_id": "dc1:unused-dev-dependency:4", "effective_severity": "warn"}],
    "next_steps": [{"id": "trace", "command": "fallow dead-code --trace x"}],
}


@unittest.skipUnless(shutil.which("node"), "Node.js is required to run the fallow adapter")
class FallowAdapterTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="fallow-adapter-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        npx = os.path.join(self.dir, "npx")
        with open(npx, "w") as fh:
            fh.write(FAKE_NPX)
        os.chmod(npx, 0o755)
        self.replay(health=HEALTH, dupes=DUPES, **{"dead-code": DEAD})

    def replay(self, **payloads):
        for name, data in payloads.items():
            with open(os.path.join(self.dir, f"{name}.json"), "w") as fh:
                fh.write(data if isinstance(data, str) else json.dumps(data))

    def run_adapter(self, check, exit_code=1):
        env = {**os.environ, "PATH": self.dir + os.pathsep + os.environ["PATH"],
               "FAKE_DIR": self.dir, "FAKE_EXIT": str(exit_code)}
        return subprocess.run(["node", ADAPTER, check], env=env, text=True, capture_output=True)

    def findings(self, check, exit_code=1):
        r = self.run_adapter(check, exit_code)
        self.assertEqual(r.returncode, 0, r.stderr)
        return [json.loads(line) for line in r.stdout.splitlines() if line.strip()]

    def test_complexity_emits_one_finding_per_exceeded_dimension(self):
        out = self.findings("complexity")
        self.assertEqual([(f["rule"], f["message"]) for f in out], [
            ("complexity-cyclomatic", "22 cyclomatic complexity in complex"),
            ("complexity-cognitive", "21 cognitive complexity in complex"),
            ("complexity-cognitive", "18 cognitive complexity in nested"),
        ])
        self.assertEqual(out[0]["file"], "src/util.ts")
        self.assertEqual(out[0]["line"], 3)

    def test_metric_leads_the_message_and_line_numbers_stay_out(self):
        for check in ("complexity", "duplication", "dead-code"):
            for f in self.findings(check):
                self.assertNotIn(str(f["line"]) + ":", f["message"])
        dup = self.findings("duplication")
        self.assertEqual(dup[0]["message"], "8 duplicated lines shared with src/b.ts")
        self.assertEqual(dup[1]["message"], "8 duplicated lines shared with src/a.ts")
        self.assertEqual(dup[1]["line"], 4)

    def test_dead_code_keeps_only_error_severity_findings_keyed_by_name(self):
        out = self.findings("dead-code")
        self.assertEqual([(f["file"], f["rule"], f["message"]) for f in out], [
            ("src/orphan.ts", "unused-file", "unused file: src/orphan.ts"),
            ("src/util.ts", "unused-export", "unused export: unusedExport"),
            ("package.json", "unused-dependency", "unused dependency: left-pad"),
        ])

    def test_clean_run_with_exit_zero_emits_nothing(self):
        self.replay(health={"kind": "health", "summary": {}, "findings": []})
        self.assertEqual(self.findings("complexity", exit_code=0), [])

    def test_fallow_runtime_error_is_a_failure(self):
        self.replay(health={"error": True, "message": "invalid config", "exit_code": 2})
        r = self.run_adapter("complexity", exit_code=2)
        self.assertEqual(r.returncode, 2)
        self.assertIn("exited 2", r.stderr)
        self.assertEqual(r.stdout, "")

    def test_unparseable_output_is_a_failure(self):
        self.replay(dupes="not json")
        r = self.run_adapter("duplication")
        self.assertEqual(r.returncode, 2)
        self.assertIn("did not print JSON", r.stderr)

    def test_unknown_check_is_refused(self):
        r = self.run_adapter("style")
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage", r.stderr)


if __name__ == "__main__":
    unittest.main()
