"""Step recording and summary output (spec 011, FR-009)."""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import DeployConfig, redact


@dataclass
class Step:
    name: str
    status: str = "ok"  # ok | failed | skipped
    evidence: str = ""

    @property
    def icon(self) -> str:
        return {"ok": "✓", "failed": "✗", "skipped": "−"}.get(self.status, "?")

    def line(self, dcfg: DeployConfig) -> str:
        return f"[{self.icon}] {self.name}: {redact(self.evidence, dcfg.secrets)}"


@dataclass
class RunReport:
    steps: list[Step] = field(default_factory=list)
    _dcfg: DeployConfig = field(default_factory=DeployConfig)

    def configure(self, dcfg: DeployConfig) -> None:
        self._dcfg = dcfg

    def add(self, name: str, status: str = "ok", evidence: str = "") -> Step:
        step = Step(name=name, status=status, evidence=evidence)
        self.steps.append(step)
        print(step.line(self._dcfg), flush=True)
        return step

    def echo(self, dcfg: DeployConfig, step: Step) -> None:
        print(step.line(dcfg), flush=True)

    @property
    def failures(self) -> list[Step]:
        return [s for s in self.steps if s.status == "failed"]

    def summary(self, dcfg: DeployConfig) -> str:
        lines = []
        if self.failures:
            lines.append(f"FAILURES ({len(self.failures)}):")
            lines.extend(f"  {s.line(dcfg)}" for s in self.failures)
        skipped = [s for s in self.steps if s.status == "skipped"]
        if skipped:
            lines.append(f"skipped ({len(skipped)}):")
            lines.extend(f"  {s.line(dcfg)}" for s in skipped)
        ok = [s for s in self.steps if s.status == "ok"]
        lines.append(f"ok: {len(ok)} steps")
        return "\n".join(lines)

    def exit_code(self) -> int:
        return len(self.failures)
