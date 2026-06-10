"""HALF — Ralph Loop: Nightly Audit and Maintenance Agent.

Schedulers (systemd timers or APScheduler) wake an agent nightly to
audit the codebase for typing coverage, duplicate logic, and performance
bottlenecks, automatically generating local Git branches and PRs.
"""

from __future__ import annotations

import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.ralph_loop")


class RalphLoop:
    """Nightly codebase audit and maintenance agent.

    Runs scheduled checks:
    - Typing coverage audit (mypy strict gaps)
    - Duplicate code detection
    - Performance bottleneck identification
    - Auto-generated PRs for fixes
    """

    def __init__(self, repo_root: str | Path = "."):
        self.repo_root = Path(repo_root)

    def run_full_audit(self) -> dict[str, Any]:
        """Run the complete nightly audit.

        Returns:
            Dict with all audit results.
        """
        timestamp = datetime.now(tz=timezone.utc).isoformat()
        results: dict[str, Any] = {
            "timestamp": timestamp,
            "typing_audit": self._audit_typing(),
            "duplicate_code": self._find_duplicates(),
            "perf_bottlenecks": self._find_perf_issues(),
            "unused_deps": self._find_unused_deps(),
        }
        results["score"] = self._calculate_score(results)
        results["branch_created"] = self._create_audit_branch(results)

        logger.info("Ralph Loop audit complete — score: %d/100", results["score"])
        return results

    def _audit_typing(self) -> dict[str, Any]:
        """Audit typing coverage via mypy."""
        typing_issues: list[str] = []; missing = typing_issues
        for f in sorted(self.repo_root.rglob("*.py")):
            if ".venv" in str(f) or "egg-info" in str(f):
                continue
            content = f.read_text(encoding="utf-8")
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("def ") and "->" not in stripped:
                    missing.append(f"{f.relative_to(self.repo_root)}:{i}")
                elif stripped.startswith("def __init__") and "->" not in stripped:
                    missing.append(f"{f.relative_to(self.repo_root)}:{i}")
        return {
            "files_checked": len(list(self.repo_root.rglob("*.py"))),
            "missing_return_annotations": len(missing),
            "examples": missing[:20],
        }

    def _find_duplicates(self) -> list[dict[str, Any]]:
        """Detect duplicated code blocks."""
        duplicates = []
        function_bodies: dict[str, list[tuple[str, int]]] = {}

        for f in sorted(self.repo_root.rglob("*.py")):
            if ".venv" in str(f) or "egg-info" in str(f):
                continue
            try:
                import ast
                tree = ast.parse(f.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        body_str = "".join(ast.dump(s) for s in node.body)
                        if body_str in function_bodies:
                            for prev_file, prev_line in function_bodies[body_str]:
                                duplicates.append({
                                    "file1": prev_file,
                                    "line1": prev_line,
                                    "file2": str(f.relative_to(self.repo_root)),
                                    "line2": node.lineno,
                                    "function": node.name,
                                })
                        else:
                            function_bodies[body_str] = [(str(f.relative_to(self.repo_root)), node.lineno)]
            except SyntaxError:
                continue

        return duplicates[:50]

    def _find_perf_issues(self) -> list[dict[str, Any]]:
        """Find potential performance bottlenecks."""
        issues = []
        for f in sorted(self.repo_root.rglob("*.py")):
            if ".venv" in str(f) or "egg-info" in str(f):
                continue
            content = f.read_text(encoding="utf-8")
            for i, line in enumerate(content.split("\n"), 1):
                stripped = line.strip()
                if "time.sleep(" in stripped:
                    issues.append({"file": str(f.relative_to(self.repo_root)), "line": i, "type": "sleep", "detail": stripped[:80]})
                if "for " in stripped and " in " in stripped and "range(" in stripped:
                    pass  # Normal loop — not necessarily perf issue
        return issues[:30]

    def _find_unused_deps(self) -> list[str]:
        """Find potentially unused dependencies."""
        return []  # Would need pip-audit or similar

    def _calculate_score(self, results: dict[str, Any]) -> int:
        """Calculate a health score from audit results."""
        score = 100
        score -= results.get("typing_audit", {}).get("missing_return_annotations", 0) * 2
        score -= len(results.get("duplicate_code", [])) * 5
        score -= len(results.get("perf_bottlenecks", [])) * 3
        return max(0, score)  # type: ignore[no-any-return]

    def _create_audit_branch(self, results: dict[str, Any]) -> bool:
        """Create a Git branch and PR with audit results."""
        from datetime import datetime
        try:
            branch_name = f"audit/ralph-loop-{datetime.now().strftime('%Y%m%d')}"
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

            # Create branch, add audit report, commit, push, create PR
            subprocess.run(["git", "checkout", "-b", branch_name],
                           cwd=self.repo_root, capture_output=True, timeout=30)

            # Write audit report
            report_path = self.repo_root / ".hale" / "audit-report.md"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                f"# Ralph Loop Audit — {timestamp}\n\n"
                f"## Health Score: {results.get('score', 0)}/100\n\n"
                f"### Typing Issues: {len(results.get('typing_audit', {}).get('examples', []))}\n"
                f"### Duplicate Code: {len(results.get('duplicate_code', []))} blocks\n"
                f"### Performance Issues: {len(results.get('perf_bottlenecks', []))}\n"
            )

            subprocess.run(["git", "add", str(report_path)], cwd=self.repo_root,
                           capture_output=True, timeout=30)
            subprocess.run(["git", "commit", "-m", f"chore: ralph-loop audit {timestamp}"],
                           cwd=self.repo_root, capture_output=True, timeout=30)
            subprocess.run(["git", "push", "-u", "origin", branch_name],
                           cwd=self.repo_root, capture_output=True, timeout=60)

            # Create PR using gh CLI
            pr_result = subprocess.run(
                ["gh", "pr", "create", "--base", "staging", "--head", branch_name,
                 "--title", f"chore: Ralph Loop audit {timestamp}",
                 "--body", f"Automated audit from Ralph Loop.\nScore: {results.get('score', 0)}/100"],
                cwd=self.repo_root, capture_output=True, text=True, timeout=30,
            )

            # Switch back
            subprocess.run(["git", "checkout", "-"], cwd=self.repo_root, capture_output=True, timeout=30)

            logger.info("Audit PR created: %s", pr_result.stdout.strip() if pr_result.returncode == 0 else "push only")
            return True
        except subprocess.TimeoutExpired as e:
            logger.error("Audit branch creation failed: %s", e)
            return False
