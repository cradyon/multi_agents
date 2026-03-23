from __future__ import annotations

import json
import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PYDANTIC_AVAILABLE = importlib.util.find_spec("pydantic") is not None

if PYDANTIC_AVAILABLE:
    from app.demo_reader import list_threads, read_thread


@unittest.skipUnless(PYDANTIC_AVAILABLE, "pydantic is not installed in this environment")
class DemoReaderTests(unittest.TestCase):
    def test_list_threads_skips_invalid_json_and_non_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            threads_dir = root / "threads"
            valid_dir = threads_dir / "valid-thread"
            invalid_dir = threads_dir / "invalid-thread"
            valid_dir.mkdir(parents=True)
            invalid_dir.mkdir(parents=True)
            (threads_dir / "README.md").write_text("not a directory", encoding="utf-8")
            (valid_dir / "thread.json").write_text(
                json.dumps({"thread_id": "valid-thread", "task": "demo", "status": "completed"}),
                encoding="utf-8",
            )
            (invalid_dir / "thread.json").write_text("{not-json", encoding="utf-8")

            with patch("app.demo_reader.get_settings", return_value=SimpleNamespace(coordination_dir=root)):
                threads = list_threads()

        self.assertEqual(len(threads), 1)
        self.assertEqual(threads[0]["thread_id"], "valid-thread")
        self.assertEqual(threads[0]["path"], str(valid_dir))

    def test_read_thread_populates_agent_details(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            thread_dir = root / "threads" / "thread-123"
            agent_dir = thread_dir / "agents" / "agent-a-planner"
            agent_dir.mkdir(parents=True)

            (thread_dir / "thread.json").write_text(
                json.dumps({"thread_id": "thread-123", "task": "demo", "status": "completed"}),
                encoding="utf-8",
            )
            (thread_dir / "final.md").write_text("final answer", encoding="utf-8")
            (agent_dir / "status.md").write_text("done", encoding="utf-8")
            (agent_dir / "context.json").write_text(
                json.dumps({"status": "completed", "context": {"task": "demo"}}),
                encoding="utf-8",
            )
            (agent_dir / "log.md").write_text("planner log", encoding="utf-8")
            (agent_dir / "output.md").write_text("planner output", encoding="utf-8")

            with patch("app.demo_reader.get_settings", return_value=SimpleNamespace(coordination_dir=root)):
                payload = read_thread("thread-123")

        self.assertEqual(payload["thread_id"], "thread-123")
        self.assertEqual(payload["final"], "final answer")
        self.assertEqual(len(payload["agents"]), 1)
        self.assertEqual(payload["agents"][0]["agent_id"], "agent-a-planner")
        self.assertEqual(payload["agents"][0]["context"]["status"], "completed")


if __name__ == "__main__":
    unittest.main()
