from __future__ import annotations

import unittest
from unittest.mock import patch

from app.agents.executor import executor_node
from app.agents.planner import planner_node
from app.agents.researcher import researcher_node
from app.agents.synthesizer import synthesizer_node


class AgentFallbackTests(unittest.TestCase):
    @patch("app.agents.planner.create_chat_model", side_effect=RuntimeError("missing key"))
    def test_planner_falls_back_when_model_creation_fails(self, _mock_create_chat_model) -> None:
        result = planner_node({"task": "普通任务", "messages": []})

        self.assertEqual(result["mode"], "research_then_execute")
        self.assertTrue(result["plan"])

    @patch("app.agents.researcher.create_chat_model", side_effect=RuntimeError("missing key"))
    def test_researcher_falls_back_when_model_creation_fails(self, _mock_create_chat_model) -> None:
        result = researcher_node({"task": "普通任务", "plan": "test", "research_plan": {}, "messages": []})

        self.assertIn("Goal:", result["research_notes"])

    @patch("app.agents.executor.create_chat_model", side_effect=RuntimeError("missing key"))
    def test_executor_falls_back_when_model_creation_fails(self, _mock_create_chat_model) -> None:
        result = executor_node(
            {
                "task": "普通任务",
                "plan": "test",
                "research_notes": "notes",
                "file_plan": {},
                "command_plan": {},
                "messages": [],
            }
        )

        self.assertIn("Current Assessment:", result["execution_notes"])

    @patch("app.agents.synthesizer.create_chat_model", side_effect=RuntimeError("missing key"))
    def test_synthesizer_falls_back_when_model_creation_fails(self, _mock_create_chat_model) -> None:
        result = synthesizer_node(
            {
                "task": "普通任务",
                "plan": "test",
                "research_notes": "notes",
                "execution_notes": "notes",
                "file_plan": {},
                "command_plan": {},
                "messages": [],
            }
        )

        self.assertIn("当前判断", result["final_response"])


if __name__ == "__main__":
    unittest.main()
