#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.workflow_spec import build_workflow_markdown, build_workflow_mermaid


def main() -> int:
    docs_dir = ROOT / "APP_DEMO" / "workflows"
    docs_dir.mkdir(parents=True, exist_ok=True)

    mermaid_path = docs_dir / "workflow.mmd"
    markdown_path = docs_dir / "workflow.md"

    mermaid_path.write_text(build_workflow_mermaid(), encoding="utf-8")
    markdown_path.write_text(build_workflow_markdown(), encoding="utf-8")

    print(f"Wrote {mermaid_path}")
    print(f"Wrote {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
